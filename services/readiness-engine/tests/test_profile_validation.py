import uuid
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select

from app.algorithms import match_skills
from app.db.session import dispose_engine, get_sessionmaker
from app.models.analysis import Analysis, AnalysisPrioritySkill, AnalysisSkillResult
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)
from app.schemas.analysis import AnalysisCreateRequest, C04AnalysisResponse
from app.schemas.profile_validation import (
    ProfileValidationError,
    validate_industry_profile,
    validate_industry_profile_data,
    validate_industry_requirement_data,
    validate_user_skill_data,
    validate_user_skill_profile,
    validate_user_skill_profile_data,
)
from app.services.analysis_service import AnalysisService
from app.services.profile_loader import _read_user_fixture

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"


# Ensure clean engine state across async database tests
@pytest.fixture
async def cleanup_database_engine():
    yield
    await dispose_engine()


# Helper to build a valid industry profile dict
def _valid_industry_profile_dict() -> dict[str, Any]:
    return {
        "role_id": "RL-000003",
        "primary_observed_title": "Software Engineer",
        "mapping_status": "verified",
        "career_level": "ENTRY_LEVEL",
        "profile_version": "2026-10-18T00:00:00Z",
        "requirements": [
            {
                "skill_id": "SK-000100",
                "standard_name": "Python Programming",
                "mapping_status": "verified",
                "required_proficiency_score": 0.75,
                "demand_weight": 0.9,
            },
            {
                "skill_id": "SK-000200",
                "standard_name": "Database Design",
                "mapping_status": "verified",
                "required_proficiency_score": 0.6,
                "demand_weight": 0.8,
            },
        ],
    }


# Helper to build a valid user skill profile dict
def _valid_user_skill_profile_dict() -> dict[str, Any]:
    return {
        "user_id": str(uuid.uuid4()),
        "profile_version": "2026-10-18T00:00:00Z",
        "skills": [
            {
                "skill_id": "SK-000100",
                "standard_name": "Python Programming",
                "mapping_status": "verified",
                "proficiency_score": 0.8,
                "evidence_confidence": 0.95,
            },
            {
                "skill_id": "SK-000200",
                "standard_name": "Database Design",
                "mapping_status": "verified",
                "proficiency_score": 0.5,
                "evidence_confidence": 0.85,
            },
        ],
    }


def test_01_all_seed_files_valid_and_dynamically_loaded():
    # Dynamically discover and validate all industry and user seed profiles
    industry_files = list((SEED_DIR / "industry-role-profiles").glob("*.json"))
    assert len(industry_files) >= 3, (
        "Expected at least 3 industry profiles in seed directory"
    )

    for file_path in industry_files:
        with open(file_path, encoding="utf-8") as f:
            import json

            data = json.load(f)
        profile_data = data.get("data", {}).get(
            "industry_role_profile", data.get("data", {}).get("industryRoleProfile", {})
        )
        validated = validate_industry_profile_data(profile_data)
        assert validated.role_id is not None or validated.candidate_role_id is not None
        assert len(validated.requirements) > 0

    user_files = list((SEED_DIR / "user-skill-profiles").glob("*.json"))
    assert len(user_files) >= 1, (
        "Expected at least 1 user skill profile in seed directory"
    )

    for file_path in user_files:
        data = _read_user_fixture(file_path)
        user_data = data.get("data", {}).get(
            "user_skill_profile", data.get("data", {}).get("userSkillProfile", {})
        )
        validated_user = validate_user_skill_profile_data(user_data)
        assert validated_user.user_id is not None
        assert len(validated_user.skills) > 0


def test_02_industry_profile_missing_required_fields():
    # Empty requirements list must raise ProfileValidationError
    data = _valid_industry_profile_dict()
    data["requirements"] = []
    with pytest.raises(
        ProfileValidationError, match="requirements must be a non-empty list"
    ):
        validate_industry_profile_data(data)

    # Missing role_id on verified role must raise ProfileValidationError
    data2 = _valid_industry_profile_dict()
    data2["role_id"] = None
    with pytest.raises(ProfileValidationError, match="canonical role_id is missing"):
        validate_industry_profile_data(data2)


def test_03_industry_requirement_missing_fields_and_incorrect_types():
    # Non-numeric demand_weight
    req = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": 0.5,
        "demand_weight": "heavy",
    }
    with pytest.raises(ProfileValidationError, match="demand_weight' must be numeric"):
        validate_industry_requirement_data(req)

    # Missing required_proficiency_score
    req2 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "demand_weight": 0.8,
    }
    with pytest.raises(
        ProfileValidationError, match="required_proficiency_score' is required"
    ):
        validate_industry_requirement_data(req2)


def test_04_industry_canonical_skill_id_and_mapping_status():
    # Invalid mapping status
    req = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "UNKNOWN_STATUS",
        "required_proficiency_score": 0.5,
        "demand_weight": 0.8,
    }
    with pytest.raises(ProfileValidationError, match="invalid mapping_status"):
        validate_industry_requirement_data(req)

    # Every canonical status with valid skill_id must pass validation
    for canonical_status in (
        "verified",
        "resolved",
        "canonical",
        "CANONICAL",
        "VERIFIED",
    ):
        valid_req = {
            "skill_id": "SK-000100",
            "standard_name": "Python",
            "mapping_status": canonical_status,
            "required_proficiency_score": 0.5,
            "demand_weight": 0.8,
        }
        validated = validate_industry_requirement_data(valid_req)
        assert validated.mapping_status == canonical_status.lower()
        assert validated.skill_id == "SK-000100"

    # Canonical mapping statuses without canonical skill_id must be rejected
    for canonical_status in ("verified", "resolved", "canonical", "CANONICAL"):
        req_missing = {
            "skill_id": None,
            "standard_name": "Python",
            "mapping_status": canonical_status,
            "required_proficiency_score": 0.5,
            "demand_weight": 0.8,
        }
        with pytest.raises(
            ProfileValidationError, match="canonical skill_id is missing"
        ):
            validate_industry_requirement_data(req_missing)

    # Malformed canonical skill_id
    req3 = {
        "skill_id": "INVALID-ID",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": 0.5,
        "demand_weight": 0.8,
    }
    with pytest.raises(ProfileValidationError, match="must match SK-XXXXXX"):
        validate_industry_requirement_data(req3)


def test_05_industry_numeric_boundaries_and_non_finite():
    # Negative demand weight
    req = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": 0.5,
        "demand_weight": -0.1,
    }
    with pytest.raises(
        ProfileValidationError, match="demand_weight -0.1 cannot be negative"
    ):
        validate_industry_requirement_data(req)

    # Zero required_proficiency_score must be rejected (scoring divides by it)
    req2 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": 0.0,
        "demand_weight": 0.8,
    }
    with pytest.raises(
        ProfileValidationError,
        match="required_proficiency_score 0.0 must be strictly > 0.0",
    ):
        validate_industry_requirement_data(req2)

    # Score > 1.0 must be rejected
    req3 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": 1.5,
        "demand_weight": 0.8,
    }
    with pytest.raises(
        ProfileValidationError,
        match="required_proficiency_score 1.5 must be strictly > 0.0 and <= 1.0",
    ):
        validate_industry_requirement_data(req3)

    # NaN demand_weight
    req4 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": 0.5,
        "demand_weight": float("nan"),
    }
    with pytest.raises(ProfileValidationError, match="demand_weight' must be finite"):
        validate_industry_requirement_data(req4)

    # Infinite score
    req5 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "required_proficiency_score": float("inf"),
        "demand_weight": 0.8,
    }
    with pytest.raises(
        ProfileValidationError, match="required_proficiency_score' must be finite"
    ):
        validate_industry_requirement_data(req5)


def test_06_industry_duplicate_skill_entries():
    # Duplicate canonical skills in requirement list
    data = _valid_industry_profile_dict()
    data["requirements"].append(
        {
            "skill_id": "SK-000100",
            "standard_name": "Python Duplicate",
            "mapping_status": "verified",
            "required_proficiency_score": 0.8,
            "demand_weight": 0.5,
        }
    )
    with pytest.raises(
        ProfileValidationError,
        match="duplicate requirement for canonical skill_id 'SK-000100'",
    ):
        validate_industry_profile_data(data)


def test_07_user_profile_missing_required_fields_and_types():
    # Non-numeric evidence_confidence
    sk = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "proficiency_score": 0.5,
        "evidence_confidence": "high",
    }
    with pytest.raises(
        ProfileValidationError, match="evidence_confidence' must be numeric"
    ):
        validate_user_skill_data(sk)

    # Missing proficiency_score
    sk2 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "evidence_confidence": 0.8,
    }
    with pytest.raises(ProfileValidationError, match="proficiency_score' is required"):
        validate_user_skill_data(sk2)


def test_08_user_canonical_skill_id_and_mapping_status():
    # Invalid mapping status
    sk = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "NOT_A_STATUS",
        "proficiency_score": 0.5,
        "evidence_confidence": 0.8,
    }
    with pytest.raises(ProfileValidationError, match="invalid mapping_status"):
        validate_user_skill_data(sk)

    # Every canonical status with valid skill_id must pass validation
    for canonical_status in (
        "verified",
        "resolved",
        "canonical",
        "CANONICAL",
        "VERIFIED",
    ):
        valid_sk = {
            "skill_id": "SK-000100",
            "standard_name": "Python",
            "mapping_status": canonical_status,
            "proficiency_score": 0.5,
            "evidence_confidence": 0.8,
        }
        validated = validate_user_skill_data(valid_sk)
        assert validated.mapping_status == canonical_status.lower()
        assert validated.skill_id == "SK-000100"

    # Canonical mapping statuses without canonical skill_id must be rejected
    for canonical_status in ("verified", "resolved", "canonical", "CANONICAL"):
        sk_missing = {
            "skill_id": None,
            "standard_name": "Python",
            "mapping_status": canonical_status,
            "proficiency_score": 0.5,
            "evidence_confidence": 0.8,
        }
        with pytest.raises(
            ProfileValidationError, match="canonical skill_id is missing"
        ):
            validate_user_skill_data(sk_missing)


def test_09_user_numeric_boundaries_and_non_finite():
    # Out of range proficiency_score (< 0.0)
    sk = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "proficiency_score": -0.2,
        "evidence_confidence": 0.8,
    }
    with pytest.raises(
        ProfileValidationError,
        match="proficiency_score -0.2 must be between 0.0 and 1.0",
    ):
        validate_user_skill_data(sk)

    # Out of range evidence_confidence (> 1.0)
    sk2 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "proficiency_score": 0.5,
        "evidence_confidence": 1.2,
    }
    with pytest.raises(
        ProfileValidationError,
        match="evidence_confidence 1.2 must be between 0.0 and 1.0",
    ):
        validate_user_skill_data(sk2)

    # NaN in student proficiency
    sk3 = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "mapping_status": "verified",
        "proficiency_score": float("nan"),
        "evidence_confidence": 0.8,
    }
    with pytest.raises(
        ProfileValidationError, match="proficiency_score' must be finite"
    ):
        validate_user_skill_data(sk3)


def test_10_user_duplicate_skill_entries():
    # Duplicate canonical skills in student skill profile
    data = _valid_user_skill_profile_dict()
    data["skills"].append(
        {
            "skill_id": "SK-000100",
            "standard_name": "Python Duplicate",
            "mapping_status": "verified",
            "proficiency_score": 0.9,
            "evidence_confidence": 0.8,
        }
    )
    with pytest.raises(
        ProfileValidationError,
        match="duplicate skill entry for canonical skill_id 'SK-000100'",
    ):
        validate_user_skill_profile_data(data)


def test_11_unresolved_mappings_and_unassessed_requirements_remain_valid():
    # Test all unassessed statuses: unresolved, unmapped, candidate, provisional
    for unassessed_status in ("unresolved", "unmapped", "candidate", "provisional"):
        unresolved_req = {
            "skill_id": None,
            "candidate_skill_id": f"CAND-{unassessed_status}",
            "standard_name": f"Emerging Skill {unassessed_status}",
            "mapping_status": unassessed_status,
            "required_proficiency_score": 0.5,
            "demand_weight": 0.7,
        }
        validated_req = validate_industry_requirement_data(unresolved_req)
        assert validated_req.mapping_status == unassessed_status
        assert validated_req.skill_id is None

        unresolved_skill = {
            "skill_id": None,
            "candidate_skill_id": f"CAND-USER-{unassessed_status}",
            "standard_name": f"Emerging Skill {unassessed_status}",
            "mapping_status": unassessed_status,
            "proficiency_score": 0.4,
            "evidence_confidence": 0.6,
        }
        validated_skill = validate_user_skill_data(unresolved_skill)
        assert validated_skill.mapping_status == unassessed_status
        assert validated_skill.skill_id is None


@pytest.mark.anyio
async def test_12_validation_failure_before_algorithm_1_invoked(
    monkeypatch, cleanup_database_engine
):
    # Verify validation fails BEFORE Algorithm 1 runs, leaving no partial skill results
    session_maker = get_sessionmaker()
    service = AnalysisService()

    # Track whether match_skills is ever called
    match_invoked = False

    def tracked_match(*args, **kwargs):
        nonlocal match_invoked
        match_invoked = True
        return match_skills(*args, **kwargs)

    monkeypatch.setattr("app.services.analysis_service.match_skills", tracked_match)

    async with session_maker() as session:
        # Create an invalid industry profile in the database with score = 0.0
        bad_role = IndustryProfile(
            id=uuid.uuid4(),
            role_id="RL-000999",
            primary_observed_title="Bad Role",
            mapping_status="verified",
            career_level="ENTRY_LEVEL",
            profile_version=f"v1-{uuid.uuid4().hex[:8]}",
            raw_payload={},
        )
        bad_req = IndustryProfileRequirement(
            id=uuid.uuid4(),
            industry_profile_id=bad_role.id,
            skill_id="SK-000999",
            standard_name="Bad Skill",
            primary_observed_term="Bad Skill",
            observed_terms=[],
            mapping_status="verified",
            skill_type="TECHNICAL",
            required_proficiency_level="BEGINNER",
            required_proficiency_score=0.0,  # Invalid! Must be > 0.0
            demand_weight=1.0,
        )
        bad_role_id = bad_role.id
        bad_role.requirements.append(bad_req)
        session.add(bad_role)
        await session.commit()

        req = AnalysisCreateRequest(
            industry_profile_id=bad_role_id,
            matching_method="RELATIONSHIP_AWARE",
        )

        with pytest.raises(
            ProfileValidationError,
            match="required_proficiency_score 0.0 must be strictly > 0.0",
        ):
            await service.run_analysis(session, req)

        # Assert Algorithm 1 was NEVER executed
        assert match_invoked is False, (
            "Algorithm 1 (match_skills) must NOT be invoked when validation fails"
        )

        # Check DB: Analysis recorded as FAILED, no child rows created
        stmt = select(Analysis).where(Analysis.industry_profile_id == bad_role_id)
        res = await session.execute(stmt)
        failed_analysis = res.scalars().first()

        assert failed_analysis is not None
        assert failed_analysis.status == "FAILED"
        assert "strictly > 0.0" in (failed_analysis.error_message or "")

        # Verify no skill results or priority rows were persisted
        sr_stmt = select(AnalysisSkillResult).where(
            AnalysisSkillResult.analysis_id == failed_analysis.analysis_id
        )
        sr_res = await session.execute(sr_stmt)
        assert len(sr_res.scalars().all()) == 0

        p_stmt = select(AnalysisPrioritySkill).where(
            AnalysisPrioritySkill.analysis_id == failed_analysis.analysis_id
        )
        p_res = await session.execute(p_stmt)
        assert len(p_res.scalars().all()) == 0


@pytest.mark.anyio
async def test_13_c04_contract_compatibility(cleanup_database_engine):
    # Verify C04 response retains exact contract keys and structure
    session_maker = get_sessionmaker()
    service = AnalysisService()

    async with session_maker() as session:
        req = AnalysisCreateRequest(
            role_id="RL-000003",
            matching_method="RELATIONSHIP_AWARE",
        )
        analysis, c04_payload = await service.run_analysis(session, req)

        assert analysis.status == "COMPLETED"
        assert "analysisId" in c04_payload
        assert "user_id" in c04_payload
        assert "roleId" in c04_payload
        assert "roleName" in c04_payload
        assert "readinessScore" in c04_payload
        assert "prioritySkills" in c04_payload

        # Validate with C04 response model
        validated_c04 = C04AnalysisResponse.model_validate(c04_payload)
        assert validated_c04.roleId == "RL-000003"
        assert len(validated_c04.prioritySkills) > 0

        # Verify priority skill item keys
        first_p = c04_payload["prioritySkills"][0]
        assert "skillId" in first_p
        assert "skillName" in first_p
        assert "priorityRank" in first_p
        assert "learningPriority" in first_p
        assert "gap" in first_p


def test_14_sqlalchemy_model_validation_functions():
    # Test validate_industry_profile and validate_user_skill_profile with valid model instances
    role = IndustryProfile(
        id=uuid.uuid4(),
        role_id="RL-000001",
        primary_observed_title="Valid Role",
        mapping_status="verified",
        career_level="MID_LEVEL",
        profile_version="v1",
        raw_payload={},
    )
    req = IndustryProfileRequirement(
        id=uuid.uuid4(),
        industry_profile_id=role.id,
        skill_id="SK-000123",
        standard_name="Valid Skill",
        primary_observed_term="Valid Skill",
        observed_terms=[],
        mapping_status="verified",
        skill_type="TECHNICAL",
        required_proficiency_level="INTERMEDIATE",
        required_proficiency_score=0.7,
        demand_weight=0.8,
    )
    role.requirements.append(req)

    # Valid profile should pass without exception
    validate_industry_profile(role)

    # Missing requirements should raise
    role.requirements.clear()
    with pytest.raises(ProfileValidationError, match="requirements cannot be empty"):
        validate_industry_profile(role)

    # Valid user skill profile should pass
    user_prof = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        profile_version="v1",
        raw_payload={},
    )
    skill = UserSkillProfileSkill(
        id=uuid.uuid4(),
        user_skill_profile_id=user_prof.id,
        skill_id="SK-000123",
        standard_name="Valid Skill",
        primary_observed_term="Valid Skill",
        observed_terms=[],
        mapping_status="verified",
        skill_type="TECHNICAL",
        proficiency_level="INTERMEDIATE",
        proficiency_score=0.75,
        evidence_confidence=0.9,
    )
    user_prof.skills.append(skill)
    validate_user_skill_profile(user_prof)

    # Invalid proficiency should raise
    skill.proficiency_score = 1.5
    with pytest.raises(
        ProfileValidationError,
        match="proficiency_score 1.5 must be between 0.0 and 1.0",
    ):
        validate_user_skill_profile(user_prof)


def test_15_proficiency_level_validation():
    # 1. Industry profile requirement missing required_proficiency_level
    role = IndustryProfile(
        id=uuid.uuid4(),
        role_id="RL-000100",
        primary_observed_title="Data Scientist",
        mapping_status="verified",
        career_level="ENTRY_LEVEL",
        profile_version="v1",
        raw_payload={},
    )
    req = IndustryProfileRequirement(
        id=uuid.uuid4(),
        industry_profile_id=role.id,
        skill_id="SK-000100",
        standard_name="Python",
        primary_observed_term="Python",
        observed_terms=[],
        mapping_status="verified",
        skill_type="TECHNICAL",
        required_proficiency_level=None,  # Missing!
        required_proficiency_score=0.8,
        demand_weight=0.9,
    )
    role.requirements.append(req)

    with pytest.raises(
        ProfileValidationError,
        match="required_proficiency_level is required and cannot be empty",
    ):
        validate_industry_profile(role)

    # Invalid required_proficiency_level
    req.required_proficiency_level = "SUPER_HERO"
    with pytest.raises(
        ProfileValidationError,
        match="invalid required_proficiency_level 'SUPER_HERO'",
    ):
        validate_industry_profile(role)

    # 2. User skill profile missing proficiency_level
    user_prof = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        profile_version="v1",
        raw_payload={},
    )
    skill = UserSkillProfileSkill(
        id=uuid.uuid4(),
        user_skill_profile_id=user_prof.id,
        skill_id="SK-000100",
        standard_name="Python",
        primary_observed_term="Python",
        observed_terms=[],
        mapping_status="verified",
        skill_type="TECHNICAL",
        proficiency_level="",  # Empty!
        proficiency_score=0.8,
        evidence_confidence=0.9,
    )
    user_prof.skills.append(skill)

    with pytest.raises(
        ProfileValidationError,
        match="proficiency_level is required and cannot be empty",
    ):
        validate_user_skill_profile(user_prof)

    # Invalid user proficiency_level
    skill.proficiency_level = "UNKNOWN_TIER"
    with pytest.raises(
        ProfileValidationError,
        match="invalid proficiency_level 'UNKNOWN_TIER'",
    ):
        validate_user_skill_profile(user_prof)

    # 3. Dictionary payload validation
    req_dict_invalid = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "required_proficiency_level": "INVALID_TIER",
        "required_proficiency_score": 0.8,
        "demand_weight": 0.9,
    }
    with pytest.raises(
        ProfileValidationError,
        match="invalid required_proficiency_level 'INVALID_TIER'",
    ):
        validate_industry_requirement_data(req_dict_invalid)

    user_dict_invalid = {
        "skill_id": "SK-000100",
        "standard_name": "Python",
        "proficiency_level": "INVALID_TIER",
        "proficiency_score": 0.8,
        "evidence_confidence": 0.9,
    }
    with pytest.raises(
        ProfileValidationError,
        match="invalid proficiency_level 'INVALID_TIER'",
    ):
        validate_user_skill_data(user_dict_invalid)
