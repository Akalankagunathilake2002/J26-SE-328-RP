import random
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import dispose_engine, get_sessionmaker
from app.models.analysis import (
    Analysis,
    AnalysisPrioritySkill,
    AnalysisReport,
    AnalysisSkillResult,
)
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)
from app.schemas.analysis import AnalysisCreateRequest
from app.services.analysis_service import AnalysisService


# Dispose engine after each test to ensure clean connections
@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    yield
    await dispose_engine()


# Helper to generate unique canonical role IDs for isolated testing
def _generate_role_id() -> str:
    return f"RL-{random.randint(100000, 999999)}"


# Helper to persist a custom industry profile with mixed requirement statuses
async def _create_custom_industry_profile(
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
        raw_payload={"source": "test_persistence"},
    )
    for r in requirements:
        req = IndustryProfileRequirement(
            id=uuid.uuid4(),
            industry_profile_id=profile.id,
            skill_id=r.get("skill_id"),
            standard_name=r["standard_name"],
            primary_observed_term=r["standard_name"],
            observed_terms=[],
            mapping_status=r.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            required_proficiency_level="INTERMEDIATE",
            required_proficiency_score=r.get("required_proficiency_score", 0.7),
            demand_weight=r.get("demand_weight", 1.0),
        )
        profile.requirements.append(req)

    session.add(profile)
    await session.commit()
    return profile


# Helper to persist a custom student skill profile
async def _create_custom_user_profile(
    session,
    user_id: uuid.UUID,
    skills: list[dict[str, Any]],
) -> UserSkillProfile:
    profile = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        profile_version=f"v-{uuid.uuid4().hex[:8]}",
        raw_payload={"source": "test_persistence"},
    )
    for s in skills:
        skill_entry = UserSkillProfileSkill(
            id=uuid.uuid4(),
            user_skill_profile_id=profile.id,
            skill_id=s.get("skill_id"),
            standard_name=s["standard_name"],
            primary_observed_term=s["standard_name"],
            observed_terms=[],
            mapping_status=s.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            proficiency_level="INTERMEDIATE",
            proficiency_score=s.get("proficiency_score", 0.7),
            evidence_confidence=s.get("evidence_confidence", 1.0),
        )
        profile.skills.append(skill_entry)

    session.add(profile)
    await session.commit()
    return profile


# Test 1: Verify complete persistence of analysis header record in fresh database session
@pytest.mark.anyio
async def test_01_persistence_of_analysis_header_record(client: AsyncClient):
    payload = {
        "role_id": "RL-000003",
        "matching_method": "RELATIONSHIP_AWARE",
        "scoring_config_version": "1.0",
    }
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 201
    analysis_id = uuid.UUID(response.json()["analysisId"])

    # Query directly in a new, independent session
    session_maker = get_sessionmaker()
    async with session_maker() as session:
        stmt = select(Analysis).where(Analysis.analysis_id == analysis_id)
        res = await session.execute(stmt)
        record = res.scalars().first()

        assert record is not None
        assert record.analysis_id == analysis_id
        assert record.user_id is not None
        assert record.user_skill_profile_id is not None
        assert record.industry_profile_id is not None
        assert record.snapshot_id is not None
        assert record.matching_method == "RELATIONSHIP_AWARE"
        assert record.scoring_config_version == "1.0"
        assert record.readiness_score is not None
        assert 0.0 <= record.readiness_score <= 100.0
        assert record.status == "COMPLETED"
        assert record.started_at is not None
        assert record.completed_at is not None
        assert record.completed_at >= record.started_at
        assert record.error_message is None


# Test 2: Verify per-requirement skill results are completely persisted without dropping records
@pytest.mark.anyio
async def test_02_persistence_of_per_requirement_skill_results(client: AsyncClient):
    payload = {"role_id": "RL-000003"}
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 201
    analysis_id = uuid.UUID(response.json()["analysisId"])

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        stmt = (
            select(AnalysisSkillResult)
            .where(AnalysisSkillResult.analysis_id == analysis_id)
            .order_by(AnalysisSkillResult.required_skill_name)
        )
        res = await session.execute(stmt)
        skill_results = res.scalars().all()

        # RL-000003 in seed industry profiles has 5 requirements
        assert len(skill_results) == 5

        valid_match_types = {
            "EXACT",
            "ALIAS",
            "EQUIVALENT",
            "PARTIAL_RELATIONSHIP",
            "MISSING",
            "UNASSESSED",
        }
        valid_result_statuses = {
            "COVERED",
            "PARTIALLY_COVERED",
            "MISSING",
            "UNASSESSED",
        }

        for sr in skill_results:
            assert sr.analysis_id == analysis_id
            assert sr.industry_requirement_id is not None
            assert len(sr.required_skill_name) > 0
            assert sr.match_type in valid_match_types
            assert sr.result_status in valid_result_statuses
            assert 0.0 <= sr.coverage_credit <= 1.0
            assert sr.required_proficiency in ("BEGINNER", "INTERMEDIATE", "ADVANCED")
            assert sr.industry_weight is not None and sr.industry_weight > 0

            # When matched to a student skill, verify matched attributes
            if sr.user_skill_profile_skill_id is not None:
                assert sr.matched_skill_name is not None
                assert sr.user_proficiency is not None
                assert sr.evidence_confidence is not None


# Test 3: Verify priority skills are stored with strictly descending scores and 1-indexed ranks
@pytest.mark.anyio
async def test_03_persistence_of_priority_skills_ordering_and_scores(
    client: AsyncClient,
):
    payload = {"role_id": "RL-000003"}
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 201
    analysis_id = uuid.UUID(response.json()["analysisId"])

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        stmt = (
            select(AnalysisPrioritySkill)
            .where(AnalysisPrioritySkill.analysis_id == analysis_id)
            .order_by(AnalysisPrioritySkill.priority_rank)
        )
        res = await session.execute(stmt)
        priorities = res.scalars().all()

        assert len(priorities) > 0

        scores = [p.learning_priority_score for p in priorities]
        ranks = [p.priority_rank for p in priorities]

        # Ranks must be sequential 1, 2, 3...
        assert ranks == list(range(1, len(priorities) + 1))
        # Learning priority scores must be descending
        assert scores == sorted(scores, reverse=True)

        for p in priorities:
            assert p.analysis_id == analysis_id
            assert p.skill_id.startswith("SK-")
            assert len(p.skill_name) > 0
            assert p.gap > 0.0
            assert p.required_proficiency is not None


# Test 4: Verify persisted C04 report payload adheres to exact field naming and casing
@pytest.mark.anyio
async def test_04_persistence_of_c04_report_payload_and_casing(client: AsyncClient):
    payload = {"role_id": "RL-000003"}
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 201
    analysis_id = uuid.UUID(response.json()["analysisId"])

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        stmt = select(AnalysisReport).where(AnalysisReport.analysis_id == analysis_id)
        res = await session.execute(stmt)
        report = res.scalars().first()

        assert report is not None
        assert report.report_version == "1.0"
        assert report.status == "READY"
        assert report.generation_method == "RELATIONSHIP_AWARE"

        data = report.report_payload
        expected_top_keys = {
            "analysisId",
            "user_id",
            "roleId",
            "roleName",
            "readinessScore",
            "prioritySkills",
        }
        assert set(data.keys()) == expected_top_keys
        assert data["analysisId"] == str(analysis_id)
        assert data["roleId"] == "RL-000003"
        assert data["roleName"] == "Software Testing Intern"
        assert isinstance(data["readinessScore"], (int, float))

        expected_item_keys = {
            "skillId",
            "skillName",
            "priorityRank",
            "learningPriority",
            "gap",
        }
        for item in data["prioritySkills"]:
            assert set(item.keys()) == expected_item_keys
            assert item["skillId"].startswith("SK-")
            assert isinstance(item["priorityRank"], int)
            assert isinstance(item["learningPriority"], (int, float))
            assert isinstance(item["gap"], (int, float))


# Test 5: Verify retrieval through both GET endpoints after completion
@pytest.mark.anyio
async def test_05_retrieval_through_both_get_endpoints_after_completion(
    client: AsyncClient,
):
    post_res = await client.post("/analyses", json={"role_id": "RL-000003"})
    assert post_res.status_code == 201
    analysis_id = post_res.json()["analysisId"]

    # 1. Detail endpoint /analyses/{id}
    detail_res = await client.get(f"/analyses/{analysis_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["analysis_id"] == analysis_id
    assert detail["status"] == "COMPLETED"
    assert len(detail["skill_results"]) == 5
    assert len(detail["priority_skills"]) == 5
    assert detail["c04_payload"] is not None

    # 2. C04 endpoint /analyses/{id}/c04
    c04_res = await client.get(f"/analyses/{analysis_id}/c04")
    assert c04_res.status_code == 200
    c04_data = c04_res.json()
    assert c04_data["analysisId"] == analysis_id
    assert c04_data["roleId"] == "RL-000003"

    # 3. Prefixed endpoints /readiness/analyses/{id} and /readiness/analyses/{id}/c04
    pref_detail = await client.get(f"/readiness/analyses/{analysis_id}")
    assert pref_detail.status_code == 200
    pref_c04 = await client.get(f"/readiness/analyses/{analysis_id}/c04")
    assert pref_c04.status_code == 200
    assert pref_c04.json() == c04_data


# Test 6: Verify consistency between persisted records and algorithm outputs
@pytest.mark.anyio
async def test_06_consistency_between_persisted_values_and_algorithm_outputs():
    service = AnalysisService()
    session_maker = get_sessionmaker()

    async with session_maker() as session:
        req = AnalysisCreateRequest(
            role_id="RL-000003",
            matching_method="RELATIONSHIP_AWARE",
            scoring_config_version="1.0",
        )
        analysis, c04_payload = await service.run_analysis(session, req)
        analysis_id = analysis.analysis_id
        score_from_service = analysis.readiness_score

    # Open fresh session to compare persisted records against the returned payload
    async with session_maker() as fresh_session:
        saved = await service.get_analysis_by_id(fresh_session, analysis_id)
        assert saved is not None
        assert saved.readiness_score == score_from_service
        assert saved.reports[0].report_payload == c04_payload
        assert len(saved.priority_skills) == len(c04_payload["prioritySkills"])

        for db_p, payload_p in zip(
            saved.priority_skills, c04_payload["prioritySkills"], strict=True
        ):
            assert db_p.skill_id == payload_p["skillId"]
            assert db_p.priority_rank == payload_p["priorityRank"]
            assert (
                abs(db_p.learning_priority_score - payload_p["learningPriority"]) < 1e-4
            )
            assert abs(db_p.gap - payload_p["gap"]) < 1e-4


# Test 7: Verify failed persistence leaves zero partial child result, priority, or report rows
@pytest.mark.anyio
async def test_07_failed_persistence_leaves_zero_partial_child_rows(monkeypatch):
    service = AnalysisService()

    # Trigger failure specifically during the persistence step
    def broken_format_c04(*args, **kwargs):
        raise RuntimeError("Simulated failure during result assembly")

    monkeypatch.setattr(
        "app.services.analysis_service.format_c04_payload", broken_format_c04
    )

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        req = AnalysisCreateRequest(role_id="RL-000003")
        with pytest.raises(
            RuntimeError, match="Simulated failure during result assembly"
        ):
            await service.run_analysis(session, req)

    # In a fresh session, verify that the failed analysis has exactly 0 child rows
    async with session_maker() as fresh_session:
        stmt = (
            select(Analysis)
            .where(Analysis.status == "FAILED")
            .order_by(Analysis.started_at.desc())
        )
        res = await fresh_session.execute(stmt)
        failed_analysis = res.scalars().first()

        assert failed_analysis is not None
        assert failed_analysis.status == "FAILED"
        assert "Simulated failure during result assembly" in (
            failed_analysis.error_message or ""
        )

        # Check child tables directly for partial row pollution
        stmt_sr = select(AnalysisSkillResult).where(
            AnalysisSkillResult.analysis_id == failed_analysis.analysis_id
        )
        res_sr = await fresh_session.execute(stmt_sr)
        assert len(res_sr.scalars().all()) == 0

        stmt_ps = select(AnalysisPrioritySkill).where(
            AnalysisPrioritySkill.analysis_id == failed_analysis.analysis_id
        )
        res_ps = await fresh_session.execute(stmt_ps)
        assert len(res_ps.scalars().all()) == 0

        stmt_rep = select(AnalysisReport).where(
            AnalysisReport.analysis_id == failed_analysis.analysis_id
        )
        res_rep = await fresh_session.execute(stmt_rep)
        assert len(res_rep.scalars().all()) == 0


# Test 8: Verify repeated analysis requests create separate analysis records without overwriting
@pytest.mark.anyio
async def test_08_repeated_analysis_requests_create_distinct_records(
    client: AsyncClient,
):
    payload = {"role_id": "RL-000003"}
    res1 = await client.post("/analyses", json=payload)
    res2 = await client.post("/analyses", json=payload)

    assert res1.status_code == 201
    assert res2.status_code == 201

    id1 = uuid.UUID(res1.json()["analysisId"])
    id2 = uuid.UUID(res2.json()["analysisId"])
    assert id1 != id2

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        a1 = (
            (await session.execute(select(Analysis).where(Analysis.analysis_id == id1)))
            .scalars()
            .first()
        )
        a2 = (
            (await session.execute(select(Analysis).where(Analysis.analysis_id == id2)))
            .scalars()
            .first()
        )

        assert a1 is not None and a2 is not None
        assert a1.analysis_id != a2.analysis_id
        assert a1.status == "COMPLETED"
        assert a2.status == "COMPLETED"


# Test 9: Verify nonexistent analysis retrieval returns clear 404 responses
@pytest.mark.anyio
async def test_09_nonexistent_analysis_retrieval(client: AsyncClient):
    random_id = uuid.uuid4()

    detail_res = await client.get(f"/analyses/{random_id}")
    assert detail_res.status_code == 404
    assert f"Analysis with ID '{random_id}' not found" in detail_res.json()["detail"]

    c04_res = await client.get(f"/analyses/{random_id}/c04")
    assert c04_res.status_code == 404
    assert f"Analysis with ID '{random_id}' not found" in c04_res.json()["detail"]

    prefixed_res = await client.get(f"/readiness/analyses/{random_id}")
    assert prefixed_res.status_code == 404


# Test 10: Verify unassessed requirements are persisted but excluded from readiness and priorities
@pytest.mark.anyio
async def test_10_unassessed_requirements_handling_and_exclusion(client: AsyncClient):
    session_maker = get_sessionmaker()
    role_id = _generate_role_id()
    user_id = uuid.uuid4()

    # Create industry profile with 1 assessable and 1 unassessed requirement
    async with session_maker() as session:
        industry_profile = await _create_custom_industry_profile(
            session=session,
            role_id=role_id,
            role_title="Data Engineer",
            requirements=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python Programming",
                    "mapping_status": "verified",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 0.6,
                },
                {
                    "skill_id": None,
                    "standard_name": "Legacy Tool X",
                    "mapping_status": "unresolved",
                    "required_proficiency_score": 0.5,
                    "demand_weight": 0.4,
                },
            ],
        )
        user_profile = await _create_custom_user_profile(
            session=session,
            user_id=user_id,
            skills=[
                {
                    "skill_id": "SK-000100",
                    "standard_name": "Python Programming",
                    "mapping_status": "verified",
                    "proficiency_score": 0.8,
                    "evidence_confidence": 1.0,
                }
            ],
        )
        ind_id = industry_profile.id
        usr_prof_id = user_profile.id

    payload = {
        "industry_profile_id": str(ind_id),
        "user_skill_profile_id": str(usr_prof_id),
        "role_id": role_id,
    }
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 201
    c04_data = response.json()
    analysis_id = uuid.UUID(c04_data["analysisId"])

    # 1. Unassessed requirement demand_weight (0.4) must be excluded from scoring denominator
    # Assessable requirement has 100% satisfaction (0.8 / 0.8 = 1.0, weight=0.6)
    # Overall score must be 100.0, NOT discounted by unassessed 0.4
    assert c04_data["readinessScore"] == 100.0

    # 2. Check persistence in a fresh database session
    async with session_maker() as session:
        stmt_sr = (
            select(AnalysisSkillResult)
            .where(AnalysisSkillResult.analysis_id == analysis_id)
            .order_by(AnalysisSkillResult.required_skill_name)
        )
        res_sr = await session.execute(stmt_sr)
        skill_results = res_sr.scalars().all()

        # Both requirements must be persisted
        assert len(skill_results) == 2

        unassessed_sr = next(
            s for s in skill_results if s.required_skill_name == "Legacy Tool X"
        )
        assert unassessed_sr.match_type == "UNASSESSED"
        assert unassessed_sr.result_status == "UNASSESSED"
        assert unassessed_sr.coverage_credit == 0.0

        # 3. Unassessed requirement must NOT appear in priority skills
        stmt_ps = select(AnalysisPrioritySkill).where(
            AnalysisPrioritySkill.analysis_id == analysis_id
        )
        res_ps = await session.execute(stmt_ps)
        priority_skills = res_ps.scalars().all()
        assert not any(p.skill_name == "Legacy Tool X" for p in priority_skills)
