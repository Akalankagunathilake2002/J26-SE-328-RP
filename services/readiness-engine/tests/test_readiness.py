import math
import uuid

import pytest

from app.algorithms.matching import RequirementInput, StudentSkillInput, match_skills
from app.algorithms.readiness import (
    RequirementReadinessInput,
    ScoringStatus,
    calculate_readiness,
    calculate_single_requirement_readiness,
    score_readiness,
)


def test_01_worked_example():
    # Worked example from research specification:
    # demand_weight = 0.90, required_proficiency = 0.80, student_proficiency = 0.60
    # coverage_credit = 1.00, evidence_confidence = 0.80
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.90,
        required_proficiency=0.80,
        student_proficiency=0.60,
        coverage_credit=1.00,
        evidence_confidence=0.80,
        standard_name="Python",
    )

    single_res = calculate_single_requirement_readiness(req_input)

    # 1. proficiency_alignment = min(1.0, 0.60 / 0.80) = 0.75
    assert math.isclose(single_res.proficiency_alignment, 0.75, rel_tol=1e-5)
    # 2. capability_coverage = 1.00 * 0.75 = 0.75
    assert math.isclose(single_res.capability_coverage, 0.75, rel_tol=1e-5)
    # 3. readiness_satisfaction = 0.75 * 0.80 = 0.60
    assert math.isclose(single_res.readiness_satisfaction, 0.60, rel_tol=1e-5)
    # 4. weighted_contribution = 0.90 * 0.60 = 0.54
    assert math.isclose(single_res.weighted_contribution, 0.54, rel_tol=1e-5)

    overall_res = calculate_readiness([req_input])

    # 5. overall_readiness = 100 * 0.54 / 0.90 = 60.0
    assert overall_res.is_calculated is True
    assert overall_res.overall_readiness is not None
    assert math.isclose(overall_res.overall_readiness, 60.0, rel_tol=1e-5)
    assert overall_res.status == ScoringStatus.CALCULATED.value


def test_02_student_proficiency_meets_requirement():
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.75,
        student_proficiency=0.75,
        coverage_credit=1.0,
        evidence_confidence=1.0,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert math.isclose(res.proficiency_alignment, 1.0, rel_tol=1e-5)
    assert math.isclose(res.readiness_satisfaction, 1.0, rel_tol=1e-5)


def test_03_student_proficiency_exceeds_requirement_capped_at_one():
    # Alignment must cap at 1.0 even when student proficiency exceeds target
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.70,
        student_proficiency=0.95,
        coverage_credit=1.0,
        evidence_confidence=1.0,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert res.proficiency_alignment == 1.0
    assert res.capability_coverage == 1.0
    assert res.readiness_satisfaction == 1.0


def test_04_partial_matching_credit():
    # Partial coverage credit scales down capability coverage
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=0.50,
        evidence_confidence=0.90,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert math.isclose(res.proficiency_alignment, 1.0, rel_tol=1e-5)
    assert math.isclose(res.capability_coverage, 0.50, rel_tol=1e-5)
    assert math.isclose(res.readiness_satisfaction, 0.45, rel_tol=1e-5)


def test_05_zero_matching_credit():
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=0.00,
        evidence_confidence=0.90,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert res.capability_coverage == 0.0
    assert res.readiness_satisfaction == 0.0
    assert res.weighted_contribution == 0.0


def test_06_zero_student_proficiency():
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.80,
        student_proficiency=0.00,
        coverage_credit=1.00,
        evidence_confidence=1.00,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert res.proficiency_alignment == 0.0
    assert res.readiness_satisfaction == 0.0
    assert res.weighted_contribution == 0.0


def test_07_evidence_confidence_zero():
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=1.00,
        evidence_confidence=0.00,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert res.proficiency_alignment == 1.0
    assert res.capability_coverage == 1.0
    # Zero confidence discounts readiness satisfaction entirely
    assert res.readiness_satisfaction == 0.0
    assert res.weighted_contribution == 0.0


def test_08_evidence_confidence_one():
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.50,
        required_proficiency=0.80,
        student_proficiency=0.40,
        coverage_credit=1.00,
        evidence_confidence=1.00,
    )
    res = calculate_single_requirement_readiness(req_input)
    assert res.readiness_satisfaction == res.capability_coverage
    assert math.isclose(res.readiness_satisfaction, 0.50, rel_tol=1e-5)


def test_09_different_demand_weights_weighted_averaging():
    # Requirement 1: high importance (weight 3.0), complete satisfaction (1.0)
    req1 = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=3.0,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=1.00,
        evidence_confidence=1.00,
    )
    # Requirement 2: low importance (weight 1.0), zero satisfaction (0.0)
    req2 = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.80,
        student_proficiency=0.00,
        coverage_credit=1.00,
        evidence_confidence=1.00,
    )

    res = calculate_readiness([req1, req2])
    # Expected weighted score: 100 * (3.0 * 1.0 + 1.0 * 0.0) / (3.0 + 1.0) = 75.0%
    assert res.overall_readiness is not None
    assert math.isclose(res.overall_readiness, 75.0, rel_tol=1e-5)


def test_10_multiple_industry_requirements_diverse_outcomes():
    # 3-requirement profile: exact match, partial match, and missing skill
    reqs = [
        RequirementReadinessInput(
            requirement_id=uuid.uuid4(),
            demand_weight=0.40,
            required_proficiency=0.80,
            student_proficiency=0.80,
            coverage_credit=1.00,
            evidence_confidence=0.90,
            standard_name="JavaScript",
        ),
        RequirementReadinessInput(
            requirement_id=uuid.uuid4(),
            demand_weight=0.35,
            required_proficiency=0.70,
            student_proficiency=0.35,
            coverage_credit=0.75,
            evidence_confidence=0.80,
            standard_name="React",
        ),
        RequirementReadinessInput(
            requirement_id=uuid.uuid4(),
            demand_weight=0.25,
            required_proficiency=0.80,
            student_proficiency=None,
            coverage_credit=0.00,
            evidence_confidence=None,
            standard_name="SQL",
            match_type="MISSING",
        ),
    ]

    res = calculate_readiness(reqs)
    assert res.is_calculated is True
    assert res.assessable_requirements_count == 3
    assert res.unassessed_requirements_count == 0
    assert math.isclose(res.total_included_demand_weight, 1.0, rel_tol=1e-5)

    # Req 1: 0.40 * (1.0 * 0.90) = 0.36
    # Req 2: 0.35 * ( (0.35/0.70 * 0.75) * 0.80 ) = 0.35 * (0.375 * 0.80) = 0.35 * 0.30 = 0.105
    # Req 3: 0.25 * 0.0 = 0.0
    # Sum: 0.465 -> Overall: 46.5%
    expected_score = 100.0 * (0.36 + 0.105) / 1.0
    assert res.overall_readiness is not None
    assert math.isclose(res.overall_readiness, expected_score, rel_tol=1e-5)


def test_11_assessable_requirement_with_no_matching_student_skill():
    # When a requirement is assessable but student lacks the skill, weight is in denominator with 0 contribution
    req_missing = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.50,
        required_proficiency=0.80,
        student_proficiency=None,
        coverage_credit=0.00,
        evidence_confidence=None,
        match_type="MISSING",
    )
    req_met = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.50,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=1.00,
        evidence_confidence=1.00,
        match_type="EXACT",
    )

    res = calculate_readiness([req_missing, req_met])
    # Total weight: 1.0, numerator: 0.50 * 1.0 = 0.50 -> 50.0%
    assert res.overall_readiness is not None
    assert math.isclose(res.overall_readiness, 50.0, rel_tol=1e-5)
    assert res.assessable_requirements_count == 2


def test_12_exclusion_of_unassessed_requirements():
    # Unassessed requirements must not penalize the student: excluded from numerator and denominator
    req_unassessed = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.50,
        required_proficiency=0.80,
        coverage_credit=0.00,
        is_assessable=False,
        match_type="UNASSESSED",
    )
    req_assessed = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.50,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=1.00,
        evidence_confidence=1.00,
        is_assessable=True,
        match_type="EXACT",
    )

    res = calculate_readiness([req_unassessed, req_assessed])
    # Denominator only includes assessed requirement (0.50), score is 100 * 0.50 / 0.50 = 100.0%
    assert res.overall_readiness is not None
    assert math.isclose(res.overall_readiness, 100.0, rel_tol=1e-5)
    assert res.assessable_requirements_count == 1
    assert res.unassessed_requirements_count == 1
    assert math.isclose(res.total_included_demand_weight, 0.50, rel_tol=1e-5)


def test_13_empty_set_of_assessable_requirements():
    res_empty = calculate_readiness([])
    assert res_empty.overall_readiness is None
    assert res_empty.is_calculated is False
    assert res_empty.status == ScoringStatus.NO_ASSESSABLE_REQUIREMENTS.value

    # All unassessed also results in empty assessable set
    req_unassessed = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.80,
        coverage_credit=0.0,
        is_assessable=False,
    )
    res_all_unassessed = calculate_readiness([req_unassessed])
    assert res_all_unassessed.overall_readiness is None
    assert res_all_unassessed.is_calculated is False
    assert res_all_unassessed.status == ScoringStatus.NO_ASSESSABLE_REQUIREMENTS.value


def test_14_zero_total_included_demand_weight():
    req_zero_weight = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.0,
        required_proficiency=0.80,
        student_proficiency=0.80,
        coverage_credit=1.0,
        evidence_confidence=1.0,
        is_assessable=True,
    )
    res = calculate_readiness([req_zero_weight])
    assert res.overall_readiness is None
    assert res.is_calculated is False
    assert res.status == ScoringStatus.ZERO_DEMAND_WEIGHT.value


def test_15_missing_required_inputs():
    with pytest.raises(ValueError, match="cannot be None"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="REQ-1",
                demand_weight=None,  # type: ignore[arg-type]
                required_proficiency=0.8,
                coverage_credit=1.0,
            )
        )

    with pytest.raises(ValueError, match="cannot be None"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="REQ-2",
                demand_weight=1.0,
                required_proficiency=None,  # type: ignore[arg-type]
                coverage_credit=1.0,
            )
        )

    with pytest.raises(ValueError, match="cannot be None"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="REQ-3",
                demand_weight=1.0,
                required_proficiency=0.8,
                coverage_credit=None,  # type: ignore[arg-type]
            )
        )


def test_16_invalid_negative_and_out_of_range_values():
    # Negative demand weight
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-1",
                demand_weight=-0.5,
                required_proficiency=0.8,
                coverage_credit=1.0,
            )
        )

    # Required proficiency > 1.0
    with pytest.raises(ValueError, match="cannot exceed 1.0"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-2",
                demand_weight=1.0,
                required_proficiency=1.5,
                coverage_credit=1.0,
            )
        )

    # Student proficiency > 1.0
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-3",
                demand_weight=1.0,
                required_proficiency=0.8,
                student_proficiency=1.2,
                coverage_credit=1.0,
            )
        )

    # Coverage credit > 1.0
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-4",
                demand_weight=1.0,
                required_proficiency=0.8,
                coverage_credit=1.2,
            )
        )

    # Evidence confidence < 0.0
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-5",
                demand_weight=1.0,
                required_proficiency=0.8,
                coverage_credit=1.0,
                evidence_confidence=-0.1,
            )
        )


def test_17_nan_and_infinity_rejected():
    with pytest.raises(ValueError, match="must be finite"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-NAN",
                demand_weight=float("nan"),
                required_proficiency=0.8,
                coverage_credit=1.0,
            )
        )

    with pytest.raises(ValueError, match="must be finite"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-INF",
                demand_weight=1.0,
                required_proficiency=float("inf"),
                coverage_credit=1.0,
            )
        )


def test_18_zero_required_proficiency_rejected():
    with pytest.raises(ValueError, match="strictly greater than 0"):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-ZERO",
                demand_weight=1.0,
                required_proficiency=0.0,
                coverage_credit=1.0,
            )
        )


def test_19_exact_match_and_relationship_aware_methods_use_same_formula():
    req_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.90,
        required_proficiency=0.80,
        student_proficiency=0.60,
        coverage_credit=1.00,
        evidence_confidence=0.80,
    )

    res_exact = calculate_readiness([req_input], matching_method="EXACT_BASELINE")
    res_rel = calculate_readiness([req_input], matching_method="RELATIONSHIP_AWARE")

    # Readiness formula and numerical results must be identical regardless of matching method flag
    assert res_exact.overall_readiness == res_rel.overall_readiness
    assert res_exact.matching_method == "EXACT_BASELINE"
    assert res_rel.matching_method == "RELATIONSHIP_AWARE"


def test_20_unsupported_or_zero_credit_matches_gain_no_readiness():
    # Even with high student proficiency (1.0) and high evidence confidence (1.0), zero matching credit produces zero readiness
    req_zero_credit = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=1.0,
        required_proficiency=0.8,
        student_proficiency=1.0,
        coverage_credit=0.0,
        evidence_confidence=1.0,
        match_type="RELATED_TO_UNSUPPORTED",
    )
    res = calculate_single_requirement_readiness(req_zero_credit)
    assert res.capability_coverage == 0.0
    assert res.readiness_satisfaction == 0.0
    assert res.weighted_contribution == 0.0


def test_21_extra_student_skills_do_not_inflate_readiness():
    req = RequirementInput(
        requirement_id=uuid.uuid4(),
        skill_id="SK-000001",
        standard_name="Python",
        mapping_status="RESOLVED",
        demand_weight=1.0,
    )
    stu_matching = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id="SK-000001",
        standard_name="Python",
    )
    # Extra unrequested skills possessed by the student
    stu_extra1 = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id="SK-000002",
        standard_name="Haskell",
    )
    stu_extra2 = StudentSkillInput(
        skill_record_id=uuid.uuid4(),
        skill_id="SK-000003",
        standard_name="Cobol",
    )

    # 1. Matching and scoring with only requested skill
    match_res_single = match_skills([req], [stu_matching])
    readiness_single = score_readiness(
        requirements=[
            {
                "id": req.requirement_id,
                "demand_weight": 1.0,
                "required_proficiency": 0.8,
            }
        ],
        matching_results=match_res_single,
        student_skills=[
            {
                "id": stu_matching.skill_record_id,
                "student_proficiency": 0.8,
                "evidence_confidence": 1.0,
            }
        ],
    )

    # 2. Matching and scoring with extra skills present
    match_res_multi = match_skills([req], [stu_matching, stu_extra1, stu_extra2])
    readiness_multi = score_readiness(
        requirements=[
            {
                "id": req.requirement_id,
                "demand_weight": 1.0,
                "required_proficiency": 0.8,
            }
        ],
        matching_results=match_res_multi,
        student_skills=[
            {
                "id": stu_matching.skill_record_id,
                "student_proficiency": 0.8,
                "evidence_confidence": 1.0,
            },
            {
                "id": stu_extra1.skill_record_id,
                "student_proficiency": 1.0,
                "evidence_confidence": 1.0,
            },
            {
                "id": stu_extra2.skill_record_id,
                "student_proficiency": 1.0,
                "evidence_confidence": 1.0,
            },
        ],
    )

    # Overall readiness score must remain completely identical
    assert readiness_single.overall_readiness == readiness_multi.overall_readiness
    assert readiness_single.overall_readiness == 100.0


def test_22_invalid_input_cannot_silently_produce_plausible_score():
    with pytest.raises(TypeError):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-TYPE",
                demand_weight="heavy",  # type: ignore[arg-type]
                required_proficiency=0.8,
                coverage_credit=1.0,
            )
        )

    with pytest.raises(TypeError):
        calculate_single_requirement_readiness(
            RequirementReadinessInput(
                requirement_id="R-BOOL",
                demand_weight=True,  # type: ignore[arg-type]
                required_proficiency=0.8,
                coverage_credit=1.0,
            )
        )
