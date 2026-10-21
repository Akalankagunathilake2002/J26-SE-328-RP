import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import dispose_engine, get_sessionmaker
from app.models.analysis import (
    Analysis,
    AnalysisReport,
    AnalysisSkillResult,
    AnalysisStatus,
)
from app.models.cache import KnowledgeSnapshot
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)
from app.services.explanation_service import (
    build_readiness_summary,
    build_skill_explanation,
    interpret_readiness_score,
)


# Dispose engine after each test to ensure clean database connections
@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    yield
    await dispose_engine()


# Helper to generate unique canonical role IDs
def _generate_role_id() -> str:
    return f"RL-{random.randint(100000, 999999)}"


# Helper to persist a custom industry profile
async def _create_industry_profile(
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
        raw_payload={"source": "test_reports"},
    )
    for r in requirements:
        req = IndustryProfileRequirement(
            id=uuid.uuid4(),
            industry_profile_id=profile.id,
            skill_id=r.get("skill_id", "SK-000001"),
            standard_name=r["standard_name"],
            primary_observed_term=r["standard_name"],
            observed_terms=[],
            mapping_status=r.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            required_proficiency_level=r.get(
                "required_proficiency_level", "INTERMEDIATE"
            ),
            required_proficiency_score=r.get("required_proficiency_score", 0.7),
            demand_weight=r.get("demand_weight", 1.0),
        )
        profile.requirements.append(req)

    session.add(profile)
    await session.commit()
    return profile


# Helper to persist a custom student skill profile
async def _create_user_profile(
    session,
    user_id: uuid.UUID,
    skills: list[dict[str, Any]],
) -> UserSkillProfile:
    profile = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        profile_version=f"v-{uuid.uuid4().hex[:8]}",
        raw_payload={"source": "test_reports"},
    )
    for s in skills:
        skill_entry = UserSkillProfileSkill(
            id=uuid.uuid4(),
            user_skill_profile_id=profile.id,
            skill_id=s.get("skill_id", "SK-000001"),
            standard_name=s["standard_name"],
            primary_observed_term=s["standard_name"],
            observed_terms=[],
            mapping_status=s.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            proficiency_level=s.get("proficiency_level", "INTERMEDIATE"),
            proficiency_score=s.get("proficiency_score", 0.7),
            evidence_confidence=s.get("evidence_confidence", 1.0),
        )
        profile.skills.append(skill_entry)

    session.add(profile)
    await session.commit()
    return profile


# Test 1: Unit verification of deterministic readiness score interpretation thresholds
@pytest.mark.anyio
async def test_01_readiness_score_interpretation_tiers():
    tier, expl = interpret_readiness_score(92.0)
    assert tier == "High Readiness"
    assert "92.0%" in expl

    tier, expl = interpret_readiness_score(78.5)
    assert tier == "Moderate Readiness"
    assert "78.5%" in expl

    tier, expl = interpret_readiness_score(62.0)
    assert tier == "Developing Readiness"
    assert "62.0%" in expl

    tier, expl = interpret_readiness_score(35.0)
    assert tier == "Low Readiness"
    assert "35.0%" in expl

    tier, expl = interpret_readiness_score(None)
    assert tier == "Not Computed"


# Test 2: Unit verification of skill explanation generation across match and gap types
@pytest.mark.anyio
async def test_02_skill_explanation_deterministic_templates():
    # Exact match satisfied
    sr_exact = AnalysisSkillResult(
        id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
        required_skill_name="Python",
        matched_skill_name="Python",
        match_type="EXACT",
        coverage_credit=1.0,
        required_proficiency="INTERMEDIATE",
        user_proficiency="ADVANCED",
        industry_weight=1.0,
        satisfaction=1.0,
        gap=0.0,
        result_status="SATISFIED",
    )
    out_exact = build_skill_explanation(sr_exact, total_assessable_weight=2.0)
    assert "Direct exact match" in out_exact.explanation
    assert out_exact.readinessContribution == 50.0
    assert out_exact.maxPotentialContribution == 50.0
    assert "Contributed 50.0 points" in out_exact.contributionExplanation

    # Relationship match with partial satisfaction
    sr_rel = AnalysisSkillResult(
        id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
        required_skill_name="FastAPI",
        matched_skill_name="Flask",
        match_type="RELATIONSHIP",
        relationship_id="REL-000412",
        coverage_credit=0.7,
        required_proficiency="ADVANCED",
        user_proficiency="INTERMEDIATE",
        industry_weight=1.0,
        satisfaction=0.5,
        gap=0.35,
        result_status="PARTIAL",
    )
    out_rel = build_skill_explanation(sr_rel, total_assessable_weight=2.0)
    assert "REL-000412" in out_rel.explanation
    assert "70% coverage credit" in out_rel.explanation
    assert out_rel.readinessContribution == 25.0

    # Missing skill
    sr_missing = AnalysisSkillResult(
        id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
        required_skill_name="Kubernetes",
        matched_skill_name=None,
        match_type="MISSING",
        coverage_credit=0.0,
        required_proficiency="INTERMEDIATE",
        user_proficiency=None,
        industry_weight=1.0,
        satisfaction=0.0,
        gap=0.7,
        result_status="MISSING",
    )
    out_missing = build_skill_explanation(sr_missing, total_assessable_weight=2.0)
    assert "No demonstrated skill found" in out_missing.explanation
    assert out_missing.readinessContribution == 0.0

    # Unassessed skill
    sr_unassessed = AnalysisSkillResult(
        id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
        required_skill_name="Legacy Tool",
        matched_skill_name=None,
        match_type="UNASSESSED",
        coverage_credit=0.0,
        required_proficiency="INTERMEDIATE",
        user_proficiency=None,
        industry_weight=1.0,
        satisfaction=None,
        gap=None,
        result_status="UNASSESSED",
    )
    out_unassessed = build_skill_explanation(sr_unassessed, total_assessable_weight=2.0)
    assert "mapping status is unresolved" in out_unassessed.explanation
    assert out_unassessed.readinessContribution == 0.0
    assert (
        "excluded from the scoring denominator"
        in out_unassessed.contributionExplanation
    )


# Test 3: Integration verification of GET /analyses/{analysis_id}/report for completed analysis
@pytest.mark.anyio
async def test_03_completed_analysis_explanation_report(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session=session,
            role_id=role_id,
            role_title="Backend Microservices Engineer",
            requirements=[
                {
                    "skill_id": "SK-000001",
                    "standard_name": "Python",
                    "required_proficiency_level": "ADVANCED",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 1.0,
                },
                {
                    "skill_id": "SK-000002",
                    "standard_name": "Docker",
                    "required_proficiency_level": "INTERMEDIATE",
                    "required_proficiency_score": 0.7,
                    "demand_weight": 0.8,
                },
            ],
        )
        usr = await _create_user_profile(
            session=session,
            user_id=user_id,
            skills=[
                {
                    "skill_id": "SK-000001",
                    "standard_name": "Python",
                    "proficiency_level": "ADVANCED",
                    "proficiency_score": 0.8,
                    "evidence_confidence": 1.0,
                }
            ],
        )
        ind_id, usr_id = ind.id, usr.id

    # Create analysis
    create_resp = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_id,
        },
    )
    assert create_resp.status_code == 201
    analysis_id = create_resp.json()["analysisId"]

    # Retrieve explanation report
    report_resp = await client.get(f"/analyses/{analysis_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()

    # Verify top-level contract and identification fields
    assert report_data["analysisId"] == analysis_id
    assert report_data["user_id"] == str(user_id)
    assert report_data["roleId"] == role_id
    assert report_data["roleName"] == "Backend Microservices Engineer"
    assert report_data["status"] == "COMPLETED"
    assert report_data["reportVersion"] == "1.0"
    assert report_data["generatedAt"] is not None

    # Verify readiness summary
    summary = report_data["readinessSummary"]
    assert summary["readinessScore"] > 0.0
    assert summary["tier"] in [
        "High Readiness",
        "Moderate Readiness",
        "Developing Readiness",
        "Low Readiness",
    ]
    assert summary["totalRequirements"] == 2
    assert summary["assessableRequirements"] == 2
    assert summary["satisfiedCount"] == 1
    assert summary["missingCount"] == 1

    # Verify skill explanations
    skill_expls = {s["skillName"]: s for s in report_data["skillExplanations"]}
    assert "Python" in skill_expls
    assert "Docker" in skill_expls
    assert skill_expls["Python"]["resultStatus"] in ("COVERED", "SATISFIED")
    assert "Direct exact match" in skill_expls["Python"]["explanation"]
    assert skill_expls["Docker"]["resultStatus"] == "MISSING"
    assert "No demonstrated skill found" in skill_expls["Docker"]["explanation"]

    # Verify learning priority explanation
    priority_expls = report_data["priorityExplanations"]
    assert len(priority_expls) == 1
    docker_priority = priority_expls[0]
    assert docker_priority["skillName"] == "Docker"
    assert docker_priority["priorityRank"] == 1
    assert "Ranked #1 learning priority" in docker_priority["explanation"]
    assert "industry demand weight of 0.80" in docker_priority["explanation"]


# Test 4: Verify verified relationship explanation appears only when relationship is matched
@pytest.mark.anyio
async def test_04_verified_relationship_explanations(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session=session,
            role_id=role_id,
            role_title="Relational DB Specialist",
            requirements=[
                {
                    "skill_id": "SK-000010",
                    "standard_name": "Relational Databases",
                    "required_proficiency_level": "INTERMEDIATE",
                    "required_proficiency_score": 0.7,
                    "demand_weight": 1.0,
                }
            ],
        )
        usr = await _create_user_profile(
            session=session,
            user_id=user_id,
            skills=[
                {
                    "skill_id": "SK-000011",
                    "standard_name": "PostgreSQL",
                    "proficiency_level": "INTERMEDIATE",
                    "proficiency_score": 0.7,
                    "evidence_confidence": 1.0,
                }
            ],
        )
        snapshot = (await session.execute(select(KnowledgeSnapshot))).scalars().first()

        # Create analysis directly with a relationship skill result
        an = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr.id,
            industry_profile_id=ind.id,
            snapshot_id=snapshot.snapshot_id,
            matching_method="RELATIONSHIP_AWARE",
            scoring_config_version="1.0",
            readiness_score=85.0,
            status="COMPLETED",
            started_at=datetime.now(UTC) - timedelta(minutes=5),
            completed_at=datetime.now(UTC) - timedelta(minutes=4),
        )
        session.add(an)

        sr = AnalysisSkillResult(
            id=uuid.uuid4(),
            analysis_id=an.analysis_id,
            industry_requirement_id=ind.requirements[0].id,
            user_skill_profile_skill_id=usr.skills[0].id,
            required_skill_name="Relational Databases",
            matched_skill_name="PostgreSQL",
            match_type="RELATIONSHIP",
            relationship_id="REL-000055",
            coverage_credit=0.85,
            required_proficiency="INTERMEDIATE",
            user_proficiency="INTERMEDIATE",
            evidence_confidence=1.0,
            industry_weight=1.0,
            satisfaction=0.85,
            gap=0.10,
            result_status="PARTIAL",
        )
        session.add(sr)
        await session.commit()
        target_analysis_id = str(an.analysis_id)

    # Retrieve explanation report
    resp = await client.get(f"/analyses/{target_analysis_id}/report")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["relationshipExplanations"]) == 1
    rel = data["relationshipExplanations"][0]
    assert rel["relationshipId"] == "REL-000055"
    assert rel["requiredSkillName"] == "Relational Databases"
    assert rel["matchedSkillName"] == "PostgreSQL"
    assert rel["coverageCredit"] == 0.85
    assert "REL-000055" in rel["explanation"]
    assert "85% coverage credit" in rel["explanation"]


# Test 5: Verify unassessed skills are explained and do not contribute to readiness
@pytest.mark.anyio
async def test_05_unassessed_skills_explanation_and_zero_contribution(
    client: AsyncClient,
):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session=session,
            role_id=role_id,
            role_title="AI Research Engineer",
            requirements=[
                {
                    "skill_id": "SK-000001",
                    "standard_name": "Python",
                    "required_proficiency_level": "ADVANCED",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 1.0,
                    "mapping_status": "verified",
                },
                {
                    "skill_id": None,
                    "standard_name": "Proprietary Quantum Tool",
                    "required_proficiency_level": "INTERMEDIATE",
                    "required_proficiency_score": 0.7,
                    "demand_weight": 0.5,
                    "mapping_status": "unresolved",
                },
            ],
        )
        usr = await _create_user_profile(
            session=session,
            user_id=user_id,
            skills=[
                {
                    "skill_id": "SK-000001",
                    "standard_name": "Python",
                    "proficiency_level": "ADVANCED",
                    "proficiency_score": 0.8,
                    "evidence_confidence": 1.0,
                }
            ],
        )
        ind_id, usr_id = ind.id, usr.id

    create_resp = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_id,
        },
    )
    assert create_resp.status_code == 201
    analysis_id = create_resp.json()["analysisId"]

    report_resp = await client.get(f"/analyses/{analysis_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()

    # Unassessed count in summary
    assert report_data["readinessSummary"]["unassessedCount"] == 1
    assert report_data["readinessSummary"]["assessableRequirements"] == 1

    # Check unassessed skill explanation
    unassessed_expl = next(
        s
        for s in report_data["skillExplanations"]
        if s["skillName"] == "Proprietary Quantum Tool"
    )
    assert unassessed_expl["matchType"] == "UNASSESSED"
    assert unassessed_expl["readinessContribution"] == 0.0
    assert (
        "excluded from scoring and learning priorities"
        in unassessed_expl["explanation"]
    )

    # Verify unassessed skill never appears in priority recommendations
    assert not any(
        p["skillName"] == "Proprietary Quantum Tool"
        for p in report_data["priorityExplanations"]
    )


# Test 6: Verify unknown analysis ID returns 404 Not Found
@pytest.mark.anyio
async def test_06_unknown_analysis_returns_404(client: AsyncClient):
    random_id = uuid.uuid4()
    resp = await client.get(f"/analyses/{random_id}/report")
    assert resp.status_code == 404
    assert f"Analysis with ID '{random_id}' not found" in resp.json()["detail"]


# Test 7: Verify pending and failed analyses return 400 Bad Request with informative details
@pytest.mark.anyio
async def test_07_pending_and_failed_analyses_return_400(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session, role_id, "Role Pending", [{"standard_name": "SQL"}]
        )
        usr = await _create_user_profile(session, user_id, [{"standard_name": "SQL"}])
        snapshot = (await session.execute(select(KnowledgeSnapshot))).scalars().first()

        pending_an = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr.id,
            industry_profile_id=ind.id,
            snapshot_id=snapshot.snapshot_id,
            status=AnalysisStatus.PENDING.value,
            started_at=datetime.now(UTC),
        )
        failed_an = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr.id,
            industry_profile_id=ind.id,
            snapshot_id=snapshot.snapshot_id,
            status=AnalysisStatus.FAILED.value,
            error_message="Profile validation failed: missing proficiency level",
            started_at=datetime.now(UTC) - timedelta(minutes=5),
            completed_at=datetime.now(UTC) - timedelta(minutes=4),
        )
        session.add_all([pending_an, failed_an])
        await session.commit()

        pending_id = str(pending_an.analysis_id)
        failed_id = str(failed_an.analysis_id)

    # Pending analysis check
    res_pending = await client.get(f"/analyses/{pending_id}/report")
    assert res_pending.status_code == 400
    assert "current status: PENDING" in res_pending.json()["detail"]

    # Failed analysis check includes error message
    res_failed = await client.get(f"/analyses/{failed_id}/report")
    assert res_failed.status_code == 400
    assert "current status: FAILED" in res_failed.json()["detail"]
    assert "Profile validation failed" in res_failed.json()["detail"]


# Test 8: Verify repeated report retrieval requests do not create duplicate persisted reports
@pytest.mark.anyio
async def test_08_repeated_requests_prevent_duplicate_persisted_reports(
    client: AsyncClient,
):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session, role_id, "Idempotency Test Role", [{"standard_name": "Java"}]
        )
        usr = await _create_user_profile(session, user_id, [{"standard_name": "Java"}])
        ind_id, usr_id = ind.id, usr.id

    create_resp = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_id,
        },
    )
    assert create_resp.status_code == 201
    analysis_id = uuid.UUID(create_resp.json()["analysisId"])

    # First retrieval generates and persists the report
    resp1 = await client.get(f"/analyses/{analysis_id}/report")
    assert resp1.status_code == 200

    # Second retrieval retrieves the existing persisted report
    resp2 = await client.get(f"/analyses/{analysis_id}/report")
    assert resp2.status_code == 200
    assert resp1.json()["analysisId"] == resp2.json()["analysisId"]

    # Third retrieval via prefixed route
    resp3 = await client.get(f"/readiness/analyses/{analysis_id}/report")
    assert resp3.status_code == 200

    # Query DB directly to verify exactly 1 explanation report exists
    async with session_maker() as fresh_session:
        stmt = select(AnalysisReport).where(
            AnalysisReport.analysis_id == analysis_id,
            AnalysisReport.report_version == "explanation_v1.1",
        )
        res = await fresh_session.execute(stmt)
        explanation_reports = res.scalars().all()
        assert len(explanation_reports) == 1
        assert explanation_reports[0].generation_method == "DETERMINISTIC_TEMPLATES"


# Test 9: Verify existing C04 report retrieval remains unchanged after explanation report generation
@pytest.mark.anyio
async def test_09_c04_retrieval_remains_unaffected(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session, role_id, "C04 Invariant Role", [{"standard_name": "C++"}]
        )
        usr = await _create_user_profile(session, user_id, [{"standard_name": "C++"}])
        ind_id, usr_id = ind.id, usr.id

    create_resp = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_id,
        },
    )
    assert create_resp.status_code == 201
    analysis_id = create_resp.json()["analysisId"]

    # Generate explanation report
    rep_resp = await client.get(f"/analyses/{analysis_id}/report")
    assert rep_resp.status_code == 200

    # Retrieve downstream C04 payload and verify exact contract keys
    c04_resp = await client.get(f"/analyses/{analysis_id}/c04")
    assert c04_resp.status_code == 200
    c04_data = c04_resp.json()

    expected_keys = {
        "analysisId",
        "user_id",
        "roleId",
        "roleName",
        "readinessScore",
        "prioritySkills",
        "baselineReadinessScore",
    }
    assert set(c04_data.keys()) == expected_keys
    assert c04_data["analysisId"] == analysis_id
    assert c04_data["roleId"] == role_id


# Test 10: Verify missing supporting values do not produce fabricated explanations
@pytest.mark.anyio
async def test_10_missing_supporting_values_do_not_fabricate():
    sr = AnalysisSkillResult(
        id=uuid.uuid4(),
        analysis_id=uuid.uuid4(),
        required_skill_name="General Problem Solving",
        matched_skill_name=None,
        match_type="UNKNOWN_TYPE",
        coverage_credit=0.0,
        required_proficiency="INTERMEDIATE",
        user_proficiency=None,
        industry_weight=None,
        satisfaction=None,
        gap=None,
        result_status="UNKNOWN_STATUS",
    )
    out = build_skill_explanation(sr, total_assessable_weight=0.0)
    assert (
        "Evaluated skill requirement 'General Problem Solving' with status 'UNKNOWN_STATUS'"
        in out.explanation
    )
    assert out.readinessContribution == 0.0
    assert out.maxPotentialContribution == 0.0


# Test 11: Verification of exact matches with evidence confidence < 1.0 (satisfaction below 1)
@pytest.mark.anyio
async def test_11_exact_matches_with_discounted_evidence_confidence_classification():
    skills_data = [
        ("Python", 1.0, 0.75, 0.75, 0.0, "COVERED"),
        ("SQL", 1.0, 0.86, 0.86, 0.0, "COVERED"),
        ("Docker", 1.0, 0.62, 0.62, 0.0, "COVERED"),
        ("Git", 1.0, 0.80, 0.80, 0.0, "COVERED"),
        ("REST APIs", 1.0, 0.82, 0.82, 0.0, "COVERED"),
        ("FastAPI", 1.0, 0.69, 0.69, 0.0, "COVERED"),
    ]
    skill_results = []
    for name, weight, conf, sat, gap, status in skills_data:
        skill_results.append(
            AnalysisSkillResult(
                id=uuid.uuid4(),
                analysis_id=uuid.uuid4(),
                required_skill_name=name,
                matched_skill_name=name,
                match_type="EXACT",
                coverage_credit=1.0,
                required_proficiency="INTERMEDIATE",
                user_proficiency="INTERMEDIATE",
                evidence_confidence=conf,
                industry_weight=weight,
                satisfaction=sat,
                gap=gap,
                result_status=status,
            )
        )

    summary = build_readiness_summary(
        readiness_score=75.705,
        skill_results=skill_results,
        role_name="Software Engineer",
    )

    # Must NOT treat COVERED skills as fully satisfied if satisfaction < 1.0
    assert summary.satisfiedCount == 0
    assert summary.partialCount == 6
    assert summary.missingCount == 0
    assert summary.totalRequirements == 6
    assert "All 6 skill requirement(s) are matched with zero capability gaps" in summary.summaryText
    assert "developing evidence confidence" in summary.summaryText
    assert "developing evidence confidence rather than skill deficiencies" in summary.interpretation

    # Verify per-skill explanation distinguishes exact match from satisfaction
    total_weight = sum(s.industry_weight or 1.0 for s in skill_results)
    for sr in skill_results:
        out = build_skill_explanation(sr, total_assessable_weight=total_weight)
        assert "Direct exact match" in out.explanation
        assert "100% proficiency satisfaction" not in out.contributionExplanation
        assert "adjusted by" in out.contributionExplanation

