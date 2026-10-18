import uuid

import pytest

from app.algorithms.matching import (
    MatchingPolicy,
    RequirementInput,
    StudentSkillInput,
    match_skills,
)
from app.algorithms.priorities import (
    PrioritySkillResult,
    calculate_learning_priorities,
    format_c04_payload,
    prioritize_from_readiness,
)
from app.algorithms.readiness import (
    RequirementAssessmentStatus,
    score_readiness,
)
from app.algorithms.skill_gaps import (
    GapClassification,
    SkillGapResult,
)


def test_01_correct_priority_calculation():
    # learning_priority = demand_weight * capability_gap
    # demand_weight = 0.90, capability_gap = 0.50 -> learning_priority = 0.45
    gap_item = SkillGapResult(
        industry_requirement_id=uuid.uuid4(),
        required_canonical_skill_id="SK-000001",
        required_skill_name="Python",
        required_proficiency=0.80,
        student_proficiency=0.40,
        coverage_credit=1.00,
        capability_coverage=0.50,
        capability_gap=0.40,
        assessment_status=RequirementAssessmentStatus.ASSESSED.value,
        gap_classification=GapClassification.PARTIALLY_COVERED.value,
        demand_weight=0.90,
        evidence_confidence=0.80,
        is_actionable=True,
        explanation="",
    )

    priorities = calculate_learning_priorities([gap_item])
    assert len(priorities) == 1
    # 0.90 * 0.40 = 0.36
    assert pytest.approx(priorities[0].learning_priority, rel=1e-5) == 0.36
    assert priorities[0].priority_rank == 1
    assert priorities[0].capability_gap == 0.40
    assert priorities[0].demand_weight == 0.90


def test_02_descending_ranking_order():
    # Sort eligible skill gaps by learning_priority descending
    # Skill A: weight=0.9, gap=0.5 -> priority = 0.45
    # Skill B: weight=0.8, gap=0.3 -> priority = 0.24
    # Skill C: weight=0.5, gap=0.8 -> priority = 0.40
    gaps = [
        SkillGapResult(
            industry_requirement_id="REQ-B",
            required_canonical_skill_id="SK-000002",
            required_skill_name="SQL",
            required_proficiency=0.8,
            student_proficiency=0.5,
            coverage_credit=1.0,
            capability_coverage=0.625,
            capability_gap=0.3,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
            demand_weight=0.8,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
        SkillGapResult(
            industry_requirement_id="REQ-A",
            required_canonical_skill_id="SK-000001",
            required_skill_name="Python",
            required_proficiency=1.0,
            student_proficiency=0.5,
            coverage_credit=1.0,
            capability_coverage=0.5,
            capability_gap=0.5,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
            demand_weight=0.9,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
        SkillGapResult(
            industry_requirement_id="REQ-C",
            required_canonical_skill_id="SK-000003",
            required_skill_name="Docker",
            required_proficiency=0.8,
            student_proficiency=0.0,
            coverage_credit=0.0,
            capability_coverage=0.0,
            capability_gap=0.8,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.MISSING.value,
            demand_weight=0.5,
            evidence_confidence=None,
            is_actionable=True,
            explanation="",
        ),
    ]

    ranked = calculate_learning_priorities(gaps)
    assert len(ranked) == 3

    # Rank 1: Skill A (0.45)
    assert ranked[0].required_canonical_skill_id == "SK-000001"
    assert ranked[0].priority_rank == 1
    assert pytest.approx(ranked[0].learning_priority, rel=1e-5) == 0.45

    # Rank 2: Skill C (0.40)
    assert ranked[1].required_canonical_skill_id == "SK-000003"
    assert ranked[1].priority_rank == 2
    assert pytest.approx(ranked[1].learning_priority, rel=1e-5) == 0.40

    # Rank 3: Skill B (0.24)
    assert ranked[2].required_canonical_skill_id == "SK-000002"
    assert ranked[2].priority_rank == 3
    assert pytest.approx(ranked[2].learning_priority, rel=1e-5) == 0.24


def test_03_deterministic_tie_breaking():
    # Tie-breaking rules:
    # 1. Higher demand_weight breaks ties on identical priority
    # 2. Canonical skill ID breaks ties when both priority and demand_weight are identical
    gaps = [
        # Skill 1: priority = 0.8 * 0.5 = 0.40, demand_weight = 0.8, skill_id = SK-000003
        SkillGapResult(
            industry_requirement_id="REQ-1",
            required_canonical_skill_id="SK-000003",
            required_skill_name="Docker",
            required_proficiency=1.0,
            student_proficiency=0.5,
            coverage_credit=1.0,
            capability_coverage=0.5,
            capability_gap=0.5,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
            demand_weight=0.8,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
        # Skill 2: priority = 0.4 * 1.0 = 0.40, demand_weight = 0.4, skill_id = SK-000001
        SkillGapResult(
            industry_requirement_id="REQ-2",
            required_canonical_skill_id="SK-000001",
            required_skill_name="Python",
            required_proficiency=1.0,
            student_proficiency=0.0,
            coverage_credit=0.0,
            capability_coverage=0.0,
            capability_gap=1.0,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.MISSING.value,
            demand_weight=0.4,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
        # Skill 3: priority = 0.8 * 0.5 = 0.40, demand_weight = 0.8, skill_id = SK-000002
        SkillGapResult(
            industry_requirement_id="REQ-3",
            required_canonical_skill_id="SK-000002",
            required_skill_name="Kubernetes",
            required_proficiency=1.0,
            student_proficiency=0.5,
            coverage_credit=1.0,
            capability_coverage=0.5,
            capability_gap=0.5,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
            demand_weight=0.8,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
    ]

    ranked = calculate_learning_priorities(gaps)
    # Between Skill 1 and Skill 3: both priority=0.40, weight=0.8.
    # Tie-break on canonical skill ID: SK-000002 precedes SK-000003.
    # Skill 2: priority=0.40, but lower weight=0.4 -> ranks 3rd.
    assert ranked[0].required_canonical_skill_id == "SK-000002"
    assert ranked[0].priority_rank == 1

    assert ranked[1].required_canonical_skill_id == "SK-000003"
    assert ranked[1].priority_rank == 2

    assert ranked[2].required_canonical_skill_id == "SK-000001"
    assert ranked[2].priority_rank == 3


def test_04_zero_priority_and_fully_covered_skills():
    # Fully covered skills (gap = 0.0) are excluded from the actionable list by default
    gaps = [
        SkillGapResult(
            industry_requirement_id="REQ-COVERED",
            required_canonical_skill_id="SK-000001",
            required_skill_name="Python",
            required_proficiency=0.8,
            student_proficiency=0.8,
            coverage_credit=1.0,
            capability_coverage=1.0,
            capability_gap=0.0,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.COVERED.value,
            demand_weight=1.0,
            evidence_confidence=1.0,
            is_actionable=False,
            explanation="",
        ),
        SkillGapResult(
            industry_requirement_id="REQ-ZERO-WEIGHT",
            required_canonical_skill_id="SK-000002",
            required_skill_name="Haskell",
            required_proficiency=0.8,
            student_proficiency=0.0,
            coverage_credit=0.0,
            capability_coverage=0.0,
            capability_gap=0.8,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.MISSING.value,
            demand_weight=0.0,  # Zero demand weight
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
        SkillGapResult(
            industry_requirement_id="REQ-NORMAL",
            required_canonical_skill_id="SK-000003",
            required_skill_name="SQL",
            required_proficiency=0.8,
            student_proficiency=0.4,
            coverage_credit=1.0,
            capability_coverage=0.5,
            capability_gap=0.4,
            assessment_status="ASSESSED",
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
            demand_weight=0.5,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
    ]

    actionable_ranked = calculate_learning_priorities(gaps, include_covered=False)
    # Covered skill is excluded
    assert len(actionable_ranked) == 2
    assert actionable_ranked[0].required_canonical_skill_id == "SK-000003"
    assert pytest.approx(actionable_ranked[0].learning_priority, rel=1e-5) == 0.20

    # Zero-weight skill has priority 0.0, ranked at the bottom of actionable gaps
    assert actionable_ranked[1].required_canonical_skill_id == "SK-000002"
    assert pytest.approx(actionable_ranked[1].learning_priority, rel=1e-5) == 0.0

    # When include_covered=True, covered skill is included at the end
    all_ranked = calculate_learning_priorities(gaps, include_covered=True)
    assert len(all_ranked) == 3


def test_05_exclusion_of_unassessed_requirements():
    # Unassessed requirements must be strictly excluded from priority ranking
    gaps = [
        SkillGapResult(
            industry_requirement_id="REQ-UNASSESSED",
            required_canonical_skill_id="SK-000099",
            required_skill_name="Unresolved Skill",
            required_proficiency=0.8,
            student_proficiency=None,
            coverage_credit=0.0,
            capability_coverage=0.0,
            capability_gap=0.0,
            assessment_status=RequirementAssessmentStatus.UNASSESSED.value,
            gap_classification=GapClassification.UNASSESSED.value,
            demand_weight=1.0,
            evidence_confidence=None,
            is_actionable=False,
            explanation="",
        ),
        SkillGapResult(
            industry_requirement_id="REQ-ACTIVE",
            required_canonical_skill_id="SK-000001",
            required_skill_name="Python",
            required_proficiency=0.8,
            student_proficiency=0.4,
            coverage_credit=1.0,
            capability_coverage=0.5,
            capability_gap=0.4,
            assessment_status=RequirementAssessmentStatus.ASSESSED.value,
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
            demand_weight=0.8,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        ),
    ]

    ranked = calculate_learning_priorities(gaps)
    assert len(ranked) == 1
    assert ranked[0].required_canonical_skill_id == "SK-000001"


def test_06_evidence_confidence_does_not_affect_priority():
    # Evidence confidence is an indicator of verification quality, not gap or priority
    gap_high_conf = SkillGapResult(
        industry_requirement_id="REQ-1",
        required_canonical_skill_id="SK-000001",
        required_skill_name="Python",
        required_proficiency=0.8,
        student_proficiency=0.4,
        coverage_credit=1.0,
        capability_coverage=0.5,
        capability_gap=0.4,
        assessment_status="ASSESSED",
        gap_classification=GapClassification.PARTIALLY_COVERED.value,
        demand_weight=0.9,
        evidence_confidence=1.0,
        is_actionable=True,
        explanation="",
    )
    gap_low_conf = SkillGapResult(
        industry_requirement_id="REQ-2",
        required_canonical_skill_id="SK-000002",
        required_skill_name="SQL",
        required_proficiency=0.8,
        student_proficiency=0.4,
        coverage_credit=1.0,
        capability_coverage=0.5,
        capability_gap=0.4,
        assessment_status="ASSESSED",
        gap_classification=GapClassification.PARTIALLY_COVERED.value,
        demand_weight=0.9,
        evidence_confidence=0.1,  # Low confidence
        is_actionable=True,
        explanation="",
    )

    ranked = calculate_learning_priorities([gap_high_conf, gap_low_conf])
    assert len(ranked) == 2
    # Both have demand_weight 0.9 and gap 0.4 -> priority 0.36
    assert pytest.approx(ranked[0].learning_priority, rel=1e-5) == 0.36
    assert pytest.approx(ranked[1].learning_priority, rel=1e-5) == 0.36


def test_07_correct_priority_rank_numbering():
    # Priority ranks must be 1-indexed and strictly sequential (1, 2, 3...)
    gaps = [
        SkillGapResult(
            industry_requirement_id=f"REQ-{i}",
            required_canonical_skill_id=f"SK-00000{i}",
            required_skill_name=f"Skill {i}",
            required_proficiency=1.0,
            student_proficiency=0.0,
            coverage_credit=0.0,
            capability_coverage=0.0,
            capability_gap=1.0 - (i * 0.1),
            assessment_status="ASSESSED",
            gap_classification=GapClassification.MISSING.value,
            demand_weight=1.0,
            evidence_confidence=1.0,
            is_actionable=True,
            explanation="",
        )
        for i in range(1, 6)
    ]

    ranked = calculate_learning_priorities(gaps)
    assert len(ranked) == 5
    for idx, item in enumerate(ranked, start=1):
        assert item.priority_rank == idx


def test_08_extra_student_skills_do_not_create_priority_skills():
    # Extras in student skill profile must not produce phantom industry requirements
    reqs = [
        RequirementInput(
            requirement_id="REQ-1",
            skill_id="SK-000001",
            standard_name="Python",
            mapping_status="RESOLVED",
            demand_weight=1.0,
            required_proficiency="ADVANCED",
        )
    ]
    student_skills = [
        StudentSkillInput(
            skill_record_id="STU-1",
            skill_id="SK-000001",
            standard_name="Python",
            mapping_status="RESOLVED",
            proficiency_level="INTERMEDIATE",
        ),
        StudentSkillInput(
            skill_record_id="STU-EXTRA-1",
            skill_id="SK-EXTRA-1",
            standard_name="Ruby",
            mapping_status="RESOLVED",
            proficiency_level="ADVANCED",
        ),
        StudentSkillInput(
            skill_record_id="STU-EXTRA-2",
            skill_id="SK-EXTRA-2",
            standard_name="Haskell",
            mapping_status="RESOLVED",
            proficiency_level="ADVANCED",
        ),
    ]

    # Algorithm 1: Match
    matching_results = match_skills(reqs, student_skills)
    assert len(matching_results) == 1

    # Algorithm 2: Readiness
    overall_readiness = score_readiness(
        requirements=[
            {"id": "REQ-1", "demand_weight": 1.0, "required_proficiency": 0.8}
        ],
        matching_results=matching_results,
        student_skills=[
            {"id": "STU-1", "student_proficiency": 0.4, "evidence_confidence": 1.0}
        ],
    )

    # Algorithm 3B: Learning priorities
    priorities = prioritize_from_readiness(overall_readiness)
    assert len(priorities) == 1
    assert priorities[0].required_canonical_skill_id == "SK-000001"


def test_09_c04_output_contract_exact_keys_and_casing():
    # Verify C04 output schema format: analysisId, user_id, roleId, roleName, readinessScore, prioritySkills
    priority_items = [
        PrioritySkillResult(
            priority_rank=1,
            industry_requirement_id=uuid.uuid4(),
            required_canonical_skill_id="SK-000458",
            required_skill_name="Python",
            learning_priority=0.4500,
            capability_gap=0.5000,
            demand_weight=0.90,
            required_proficiency=0.80,
            student_proficiency=0.40,
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
        ),
        PrioritySkillResult(
            priority_rank=2,
            industry_requirement_id=uuid.uuid4(),
            required_canonical_skill_id="SK-000165",
            required_skill_name="JavaScript",
            learning_priority=0.3200,
            capability_gap=0.4000,
            demand_weight=0.80,
            required_proficiency=0.70,
            student_proficiency=0.30,
            gap_classification=GapClassification.PARTIALLY_COVERED.value,
        ),
    ]

    analysis_uuid = uuid.uuid4()
    user_uuid = uuid.uuid4()
    role_uuid = uuid.uuid4()

    c04_payload = format_c04_payload(
        priority_skills=priority_items,
        role_name="Software Testing Intern",
        readiness_score=60.0,
        analysis_id=analysis_uuid,
        user_id=user_uuid,
        role_id=role_uuid,
    )

    # Validate exact top-level keys
    expected_top_keys = {
        "analysisId",
        "user_id",
        "roleId",
        "roleName",
        "readinessScore",
        "prioritySkills",
    }
    assert set(c04_payload.keys()) == expected_top_keys
    assert c04_payload["analysisId"] == str(analysis_uuid)
    assert c04_payload["user_id"] == str(user_uuid)
    assert c04_payload["roleId"] == str(role_uuid)
    assert c04_payload["roleName"] == "Software Testing Intern"
    assert c04_payload["readinessScore"] == 60.0

    # Validate exact prioritySkills items
    assert len(c04_payload["prioritySkills"]) == 2
    first_skill = c04_payload["prioritySkills"][0]
    expected_item_keys = {
        "skillId",
        "skillName",
        "priorityRank",
        "learningPriority",
        "gap",
    }
    assert set(first_skill.keys()) == expected_item_keys
    assert first_skill["skillId"] == "SK-000458"
    assert first_skill["skillName"] == "Python"
    assert first_skill["priorityRank"] == 1
    assert first_skill["learningPriority"] == 0.4500
    assert first_skill["gap"] == 0.5000


def test_10_end_to_end_pipeline_integration():
    # Complete end-to-end flow:
    # 1. Matching (Algorithm 1)
    # 2. Readiness Scoring (Algorithm 2)
    # 3. Skill Gaps (Algorithm 3A)
    # 4. Learning Priorities & C04 Payload (Algorithm 3B)
    req1 = RequirementInput(
        requirement_id="REQ-TEST-1",
        skill_id="SK-000263",
        standard_name="plan software testing",
        mapping_status="RESOLVED",
        demand_weight=0.82,
        required_proficiency="INTERMEDIATE",
    )
    req2 = RequirementInput(
        requirement_id="REQ-TEST-2",
        skill_id="SK-000165",
        standard_name="JavaScript",
        mapping_status="RESOLVED",
        demand_weight=0.90,
        required_proficiency="ADVANCED",
    )
    req3 = RequirementInput(
        requirement_id="REQ-TEST-3",
        skill_id="SK-UNRESOLVED",
        standard_name="Unresolved Skill",
        mapping_status="UNRESOLVED",
        demand_weight=0.50,
    )

    # Student has:
    # 1. Full match on JavaScript (student_prof=0.82, required_prof=0.82) -> covered
    # 2. No match on plan software testing -> missing
    student_skills = [
        StudentSkillInput(
            skill_record_id="STU-SK-1",
            skill_id="SK-000165",
            standard_name="JavaScript",
            mapping_status="RESOLVED",
        )
    ]

    # Algorithm 1: Match
    policy = MatchingPolicy()
    matching_results = match_skills([req1, req2, req3], student_skills, policy=policy)
    assert len(matching_results) == 3

    # Algorithm 2: Readiness scoring
    req_scoring_data = [
        {
            "id": "REQ-TEST-1",
            "demand_weight": 0.82,
            "required_proficiency": 0.50,
            "skill_id": "SK-000263",
            "standard_name": "plan software testing",
        },
        {
            "id": "REQ-TEST-2",
            "demand_weight": 0.90,
            "required_proficiency": 0.82,
            "skill_id": "SK-000165",
            "standard_name": "JavaScript",
        },
        {
            "id": "REQ-TEST-3",
            "demand_weight": 0.50,
            "required_proficiency": 0.60,
            "skill_id": "SK-UNRESOLVED",
            "mapping_status": "UNRESOLVED",
        },
    ]
    student_scoring_data = [
        {"id": "STU-SK-1", "student_proficiency": 0.82, "evidence_confidence": 0.90}
    ]

    overall_readiness = score_readiness(
        requirements=req_scoring_data,
        matching_results=matching_results,
        student_skills=student_scoring_data,
    )

    assert overall_readiness.is_calculated is True
    assert overall_readiness.assessable_requirements_count == 2
    assert overall_readiness.unassessed_requirements_count == 1

    # Algorithm 3B: Learning priorities
    priorities = prioritize_from_readiness(overall_readiness)

    # Plan software testing is missing (gap = 0.50), while JavaScript is fully covered (gap = 0.0)
    # Actionable priority list contains ONLY the missing skill
    assert len(priorities) == 1
    missing_item = priorities[0]
    assert missing_item.required_canonical_skill_id == "SK-000263"
    assert missing_item.priority_rank == 1
    assert pytest.approx(missing_item.capability_gap, rel=1e-5) == 0.50
    # priority = 0.82 * 0.50 = 0.41
    assert pytest.approx(missing_item.learning_priority, rel=1e-5) == 0.4100

    # C04 Payload Generation
    c04_export = format_c04_payload(
        priority_skills=priorities,
        role_name="Software Testing Intern",
        readiness_score=overall_readiness.overall_readiness,
        analysis_id="ANALYSIS-001",
        user_id="USER-001",
        role_id="RL-000003",
    )

    assert c04_export["roleName"] == "Software Testing Intern"
    assert len(c04_export["prioritySkills"]) == 1
    assert c04_export["prioritySkills"][0]["skillId"] == "SK-000263"
    assert c04_export["prioritySkills"][0]["gap"] == 0.50
