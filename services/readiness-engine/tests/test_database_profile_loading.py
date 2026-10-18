import random
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.algorithms import match_skills
from app.db.session import dispose_engine, get_sessionmaker
from app.models.analysis import Analysis, AnalysisPrioritySkill, AnalysisSkillResult
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)
from app.schemas.analysis import AnalysisCreateRequest
from app.schemas.profile_validation import ProfileValidationError
from app.services.analysis_service import AnalysisService
from app.services.profile_loader import (
    ProfileNotFoundError,
    SnapshotNotFoundError,
    resolve_industry_profile,
    resolve_snapshot,
    resolve_user_profile,
)


# Dispose database engine after each test to prevent event loop connection reuse
@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    yield
    await dispose_engine()


# Helper to generate a valid 6-digit canonical role ID
def _gen_role_id() -> str:
    return f"RL-{random.randint(100000, 999999)}"


# Helper to persist a minimal valid industry profile directly into PostgreSQL
async def _create_test_industry_profile(
    session,
    role_id: str,
    role_title: str,
    requirements: list[dict[str, Any]],
) -> IndustryProfile:
    profile = IndustryProfile(
        id=uuid.uuid4(),
        role_id=role_id,
        primary_observed_title=role_title,
        mapping_status="verified",
        career_level="ENTRY_LEVEL",
        profile_version=f"v-{uuid.uuid4().hex[:8]}",
        raw_payload={"source": "test_db_profile_loader"},
    )
    for r in requirements:
        req = IndustryProfileRequirement(
            id=uuid.uuid4(),
            industry_profile_id=profile.id,
            skill_id=r.get("skill_id"),
            candidate_skill_id=r.get("candidate_skill_id"),
            standard_name=r["standard_name"],
            primary_observed_term=r["standard_name"],
            observed_terms=[],
            mapping_status=r.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            required_proficiency_level="INTERMEDIATE",
            required_proficiency_score=r["required_proficiency_score"],
            demand_weight=r["demand_weight"],
        )
        profile.requirements.append(req)

    session.add(profile)
    await session.commit()
    return profile


# Helper to persist a minimal valid student skill profile directly into PostgreSQL
async def _create_test_user_profile(
    session,
    user_id: uuid.UUID,
    skills: list[dict[str, Any]],
) -> UserSkillProfile:
    profile = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        profile_version=f"v-{uuid.uuid4().hex[:8]}",
        raw_payload={"source": "test_db_profile_loader"},
    )
    for s in skills:
        skill_entry = UserSkillProfileSkill(
            id=uuid.uuid4(),
            user_skill_profile_id=profile.id,
            skill_id=s.get("skill_id"),
            candidate_skill_id=s.get("candidate_skill_id"),
            standard_name=s["standard_name"],
            primary_observed_term=s["standard_name"],
            observed_terms=[],
            mapping_status=s.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            proficiency_level="INTERMEDIATE",
            proficiency_score=s["proficiency_score"],
            evidence_confidence=s.get("evidence_confidence", 1.0),
            verification_status="VERIFIED",
        )
        profile.skills.append(skill_entry)

    session.add(profile)
    await session.commit()
    return profile


@pytest.mark.anyio
async def test_01_analysis_uses_selected_database_industry_profile():
    # Verify analysis uses the exact industry profile selected from PostgreSQL
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        # Create two distinct industry profiles in the database
        role_1 = await _create_test_industry_profile(
            session,
            role_id=_gen_role_id(),
            role_title="Backend Microservices Specialist",
            requirements=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 0.9,
                }
            ],
        )
        role_2 = await _create_test_industry_profile(
            session,
            role_id=_gen_role_id(),
            role_title="Data Platform Engineer",
            requirements=[
                {
                    "skill_id": "SK-000200",
                    "standard_name": "SQL",
                    "required_proficiency_score": 0.7,
                    "demand_weight": 0.85,
                }
            ],
        )

        # Run analysis for role_1
        req1 = AnalysisCreateRequest(
            industry_profile_id=role_1.id,
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis1, c04_1 = await service.run_analysis(session, req1)
        assert analysis1.industry_profile_id == role_1.id
        assert c04_1["roleName"] == "Backend Microservices Specialist"

        # Run analysis for role_2
        req2 = AnalysisCreateRequest(
            industry_profile_id=role_2.id,
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis2, c04_2 = await service.run_analysis(session, req2)
        assert analysis2.industry_profile_id == role_2.id
        assert c04_2["roleName"] == "Data Platform Engineer"


@pytest.mark.anyio
async def test_02_analysis_uses_selected_database_user_profile():
    # Verify analysis loads and evaluates the exact student profile selected from PostgreSQL
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()

        stu_a = await _create_test_user_profile(
            session,
            user_id=user_a,
            skills=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "proficiency_score": 0.9,
                    "evidence_confidence": 0.95,
                }
            ],
        )
        stu_b = await _create_test_user_profile(
            session,
            user_id=user_b,
            skills=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "proficiency_score": 0.3,
                    "evidence_confidence": 0.5,
                }
            ],
        )

        # Run analysis selecting user_a
        req_a = AnalysisCreateRequest(
            role_id="RL-000003",
            user_id=user_a,
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis_a, c04_a = await service.run_analysis(session, req_a)
        assert analysis_a.user_skill_profile_id == stu_a.id
        assert c04_a["user_id"] == str(user_a)

        # Run analysis selecting user_b
        req_b = AnalysisCreateRequest(
            role_id="RL-000003",
            user_id=user_b,
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis_b, c04_b = await service.run_analysis(session, req_b)
        assert analysis_b.user_skill_profile_id == stu_b.id
        assert c04_b["user_id"] == str(user_b)


@pytest.mark.anyio
async def test_03_missing_industry_profile_fails_clearly_without_fallback():
    # Missing industry profile must raise ProfileNotFoundError and never silently load fixtures
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        initial_count = await session.scalar(select(func.count(IndustryProfile.id)))
        missing_role_id = _gen_role_id()

        req = AnalysisCreateRequest(
            role_id=missing_role_id,
            matching_method="RELATIONSHIP_AWARE",
        )

        with pytest.raises(
            ProfileNotFoundError, match="could not be resolved from database"
        ):
            await service.run_analysis(session, req)

        # Verify no silent fixture loading or row creation occurred
        current_count = await session.scalar(select(func.count(IndustryProfile.id)))
        assert current_count == initial_count


@pytest.mark.anyio
async def test_04_missing_user_profile_fails_clearly_without_fallback():
    # Missing user profile must raise ProfileNotFoundError and never silently load fixtures
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        initial_count = await session.scalar(select(func.count(UserSkillProfile.id)))
        missing_user = uuid.uuid4()

        req = AnalysisCreateRequest(
            role_id="RL-000003",
            user_id=missing_user,
            matching_method="RELATIONSHIP_AWARE",
        )

        with pytest.raises(
            ProfileNotFoundError, match="could not be resolved from database"
        ):
            await service.run_analysis(session, req)

        current_count = await session.scalar(select(func.count(UserSkillProfile.id)))
        assert current_count == initial_count


@pytest.mark.anyio
async def test_05_missing_snapshot_fails_clearly_without_fallback():
    # Missing snapshot must raise SnapshotNotFoundError and never silently create dummy records
    session_maker = get_sessionmaker()

    async with session_maker() as session:
        missing_id = uuid.uuid4()
        with pytest.raises(
            SnapshotNotFoundError, match="could not be found in database"
        ):
            await resolve_snapshot(
                session, snapshot_id=missing_id, allow_fixture_fallback=False
            )


@pytest.mark.anyio
async def test_06_silent_fixture_fallback_is_prevented_in_loader():
    # Verify resolve_user_profile and resolve_industry_profile strictly reject missing records
    session_maker = get_sessionmaker()

    async with session_maker() as session:
        with pytest.raises(
            ProfileNotFoundError, match="could not be resolved from database"
        ):
            await resolve_industry_profile(
                session, role_id="RL-999999", allow_fixture_fallback=False
            )

        with pytest.raises(
            ProfileNotFoundError, match="could not be resolved from database"
        ):
            await resolve_user_profile(
                session, user_id=uuid.uuid4(), allow_fixture_fallback=False
            )


@pytest.mark.anyio
async def test_07_validation_occurs_on_database_records_before_matching(monkeypatch):
    # Persist an invalid profile directly in PostgreSQL and verify validation stops before Algorithm 1
    session_maker = get_sessionmaker()
    service = AnalysisService()

    match_called = False

    def tracked_match(*args, **kwargs):
        nonlocal match_called
        match_called = True
        return match_skills(*args, **kwargs)

    monkeypatch.setattr("app.services.analysis_service.match_skills", tracked_match)

    async with session_maker() as session:
        # Insert an invalid industry requirement with negative demand weight directly into PostgreSQL
        invalid_role = await _create_test_industry_profile(
            session,
            role_id=_gen_role_id(),
            role_title="Invalid Demand Weight Role",
            requirements=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "required_proficiency_score": 0.5,
                    "demand_weight": -0.8,  # Invalid negative weight
                }
            ],
        )
        invalid_role_id = invalid_role.id

        req = AnalysisCreateRequest(
            industry_profile_id=invalid_role_id,
            matching_method="RELATIONSHIP_AWARE",
        )

        with pytest.raises(
            ProfileValidationError, match="demand_weight -0.8 cannot be negative"
        ):
            await service.run_analysis(session, req)

        # Assert Algorithm 1 was NEVER executed
        assert match_called is False, (
            "Algorithm 1 (match_skills) must NOT execute when validation fails"
        )

        # Verify analysis record in database is marked FAILED without child results
        res = await session.execute(
            select(Analysis).where(Analysis.industry_profile_id == invalid_role_id)
        )
        failed_analysis = res.scalars().first()
        assert failed_analysis is not None
        assert failed_analysis.status == "FAILED"

        child_skills = await session.execute(
            select(AnalysisSkillResult).where(
                AnalysisSkillResult.analysis_id == failed_analysis.analysis_id
            )
        )
        assert len(child_skills.scalars().all()) == 0

        child_priorities = await session.execute(
            select(AnalysisPrioritySkill).where(
                AnalysisPrioritySkill.analysis_id == failed_analysis.analysis_id
            )
        )
        assert len(child_priorities.scalars().all()) == 0


@pytest.mark.anyio
async def test_08_api_returns_400_for_missing_database_profiles(client: AsyncClient):
    # Test that HTTP POST /analyses returns 400 Bad Request when database record does not exist
    missing_role = _gen_role_id()
    resp_role = await client.post("/analyses", json={"role_id": missing_role})
    assert resp_role.status_code == 400
    assert "could not be resolved from database" in resp_role.json()["detail"]

    missing_user = str(uuid.uuid4())
    resp_user = await client.post(
        "/analyses", json={"role_id": "RL-000003", "user_id": missing_user}
    )
    assert resp_user.status_code == 400
    assert "could not be resolved from database" in resp_user.json()["detail"]


@pytest.mark.anyio
async def test_09_assessable_vs_unassessed_requirements_in_database_profile():
    # Database profile containing both assessable and unassessed requirements evaluates properly
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        mixed_role = await _create_test_industry_profile(
            session,
            role_id=_gen_role_id(),
            role_title="Mixed Assessment Role",
            requirements=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "mapping_status": "verified",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 1.0,
                },
                {
                    "skill_id": None,
                    "candidate_skill_id": "CAND-EMERGING-001",
                    "standard_name": "Emerging Quantum Framework",
                    "mapping_status": "unresolved",
                    "required_proficiency_score": 0.5,
                    "demand_weight": 0.6,
                },
            ],
        )

        req = AnalysisCreateRequest(
            industry_profile_id=mixed_role.id,
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis, c04_payload = await service.run_analysis(session, req)

        assert analysis.status == "COMPLETED"
        assert c04_payload["roleName"] == "Mixed Assessment Role"


@pytest.mark.anyio
async def test_10_database_canonical_and_unmapped_statuses():
    # Industry profile in PostgreSQL with CANONICAL, UNMAPPED, and CANDIDATE statuses
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        role = await _create_test_industry_profile(
            session,
            role_id=_gen_role_id(),
            role_title="Taxonomy Mapped Role",
            requirements=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "mapping_status": "CANONICAL",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 1.0,
                },
                {
                    "skill_id": None,
                    "candidate_skill_id": "CAND-001",
                    "standard_name": "Unmapped Emerging Framework",
                    "mapping_status": "UNMAPPED",
                    "required_proficiency_score": 0.5,
                    "demand_weight": 0.6,
                },
                {
                    "skill_id": None,
                    "candidate_skill_id": "CAND-002",
                    "standard_name": "Candidate AI Library",
                    "mapping_status": "CANDIDATE",
                    "required_proficiency_score": 0.5,
                    "demand_weight": 0.4,
                },
            ],
        )

        role_id = role.id

        req = AnalysisCreateRequest(
            industry_profile_id=role_id,
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis, c04_payload = await service.run_analysis(session, req)

        assert analysis.status == "COMPLETED"

        # Check skill results in DB: canonical is assessed, unmapped and candidate are UNASSESSED
        res = await session.execute(
            select(AnalysisSkillResult).where(
                AnalysisSkillResult.analysis_id == analysis.analysis_id
            )
        )
        skill_results = res.scalars().all()
        assert len(skill_results) == 3

        unassessed_items = [sr for sr in skill_results if sr.match_type == "UNASSESSED"]
        assert len(unassessed_items) == 2
        for item in unassessed_items:
            assert item.result_status == "UNASSESSED"
            assert item.gap == 0.0

        assessed_items = [sr for sr in skill_results if sr.match_type != "UNASSESSED"]
        assert len(assessed_items) == 1
        assert assessed_items[0].required_skill_name == "Python"

        # Priority skills must only contain the assessed canonical skill, not unmapped/candidate
        priority_names = [p["skillName"] for p in c04_payload["prioritySkills"]]
        assert "Unmapped Emerging Framework" not in priority_names
        assert "Candidate AI Library" not in priority_names


@pytest.mark.anyio
@pytest.mark.parametrize(
    "patch_target,exception_cls",
    [
        ("app.services.analysis_service.match_skills", RuntimeError),
        ("app.services.analysis_service.score_readiness", RuntimeError),
        ("app.services.analysis_service.calculate_skill_gaps", RuntimeError),
        ("app.services.analysis_service.calculate_learning_priorities", RuntimeError),
    ],
)
async def test_11_failures_across_multiple_stages_leave_zero_partial_rows_and_failed_status(
    monkeypatch, patch_target, exception_cls
):
    # Simulated failure at each pipeline stage rolls back cleanly, records FAILED, and leaves 0 child rows
    def mock_fail(*args, **kwargs):
        raise exception_cls(f"Forced failure in {patch_target}")

    monkeypatch.setattr(patch_target, mock_fail)

    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        role = await _create_test_industry_profile(
            session,
            role_id=_gen_role_id(),
            role_title=f"Stage Fail Role - {patch_target.split('.')[-1]}",
            requirements=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python",
                    "required_proficiency_score": 0.5,
                    "demand_weight": 0.8,
                }
            ],
        )
        role_id = role.id

        req = AnalysisCreateRequest(
            industry_profile_id=role_id,
            matching_method="RELATIONSHIP_AWARE",
        )

        with pytest.raises(exception_cls, match=f"Forced failure in {patch_target}"):
            await service.run_analysis(session, req)

        # Confirm analysis is recorded as FAILED in database
        res = await session.execute(
            select(Analysis).where(Analysis.industry_profile_id == role_id)
        )
        failed_analysis = res.scalars().first()
        assert failed_analysis is not None
        assert failed_analysis.status == "FAILED"
        assert f"Forced failure in {patch_target}" in (
            failed_analysis.error_message or ""
        )

        # Confirm ZERO child rows were persisted
        child_skills = await session.execute(
            select(AnalysisSkillResult).where(
                AnalysisSkillResult.analysis_id == failed_analysis.analysis_id
            )
        )
        assert len(child_skills.scalars().all()) == 0

        child_priorities = await session.execute(
            select(AnalysisPrioritySkill).where(
                AnalysisPrioritySkill.analysis_id == failed_analysis.analysis_id
            )
        )
        assert len(child_priorities.scalars().all()) == 0
