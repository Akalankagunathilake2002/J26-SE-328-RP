import uuid

import pytest

from app.algorithms.readiness import (
    RequirementAssessmentStatus,
    RequirementReadinessInput,
    calculate_single_requirement_readiness,
)
from app.algorithms.skill_gaps import (
    GapClassification,
    SkillGapInput,
    calculate_single_skill_gap,
    calculate_skill_gaps,
)


def test_01_fully_covered_skill_produces_zero_gap():
    # When student capability coverage is complete (1.0), capability gap must be 0.0 and classified as COVERED
    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=1.00,
        coverage_credit=1.00,
        student_proficiency=0.80,
        skill_id="SK-000001",
        standard_name="Python",
    )
    result = calculate_single_skill_gap(req_input)

    assert result.capability_gap == 0.0
    assert result.gap_classification == GapClassification.COVERED.value
    assert result.is_actionable is False


def test_02_student_proficiency_exceeds_requirement():
    # When student proficiency exceeds the required level, capability gap remains 0.0 and classified as COVERED
    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.60,
        capability_coverage=1.00,
        coverage_credit=1.00,
        student_proficiency=0.90,
        skill_id="SK-000002",
        standard_name="SQL",
    )
    result = calculate_single_skill_gap(req_input)

    assert result.capability_gap == 0.0
    assert result.gap_classification == GapClassification.COVERED.value
    assert result.is_actionable is False


def test_03_partially_covered_skill():
    # Partial coverage of 0.50 on required proficiency 0.80 leaves a remaining gap of 0.40
    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=0.50,
        coverage_credit=1.00,
        student_proficiency=0.40,
        skill_id="SK-000003",
        standard_name="Docker",
    )
    result = calculate_single_skill_gap(req_input)

    # capability_gap = 0.80 * (1.0 - 0.50) = 0.40
    assert pytest.approx(result.capability_gap, rel=1e-5) == 0.40
    assert result.gap_classification == GapClassification.PARTIALLY_COVERED.value
    assert result.is_actionable is True


def test_04_missing_skill_produces_full_gap():
    # Zero capability coverage produces a full gap equal to required proficiency
    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.75,
        capability_coverage=0.00,
        coverage_credit=0.00,
        student_proficiency=None,
        skill_id="SK-000004",
        standard_name="Kubernetes",
    )
    result = calculate_single_skill_gap(req_input)

    # capability_gap = 0.75 * (1.0 - 0.0) = 0.75
    assert pytest.approx(result.capability_gap, rel=1e-5) == 0.75
    assert result.gap_classification == GapClassification.MISSING.value
    assert result.is_actionable is True


def test_05_exact_match_gap_consistency():
    # For exact matching with full credit, capability_gap must strictly equal max(0.0, required - student)
    req_prof = 0.80
    stu_prof = 0.60
    coverage_credit = 1.00

    # Intermediate alignment = 0.60 / 0.80 = 0.75; capability coverage = 1.0 * 0.75 = 0.75
    cap_cov = coverage_credit * min(1.0, stu_prof / req_prof)

    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=req_prof,
        capability_coverage=cap_cov,
        coverage_credit=coverage_credit,
        student_proficiency=stu_prof,
        skill_id="SK-000005",
        standard_name="Git",
    )
    result = calculate_single_skill_gap(req_input)

    expected_gap = max(0.0, req_prof - stu_prof)
    assert pytest.approx(result.capability_gap, rel=1e-5) == expected_gap
    assert pytest.approx(result.capability_gap, rel=1e-5) == 0.20
    assert result.gap_classification == GapClassification.PARTIALLY_COVERED.value


def test_06_partial_relationship_coverage():
    # Relationship partial credit of 0.70 with student proficiency 0.80 and required proficiency 0.80
    # Alignment = 1.0; capability coverage = 0.70 * 1.0 = 0.70; gap = 0.80 * (1.0 - 0.70) = 0.24
    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=0.70,
        coverage_credit=0.70,
        student_proficiency=0.80,
        skill_id="SK-000006",
        standard_name="TypeScript",
    )
    result = calculate_single_skill_gap(req_input)

    assert pytest.approx(result.capability_gap, rel=1e-5) == 0.24
    assert result.gap_classification == GapClassification.PARTIALLY_COVERED.value
    assert result.is_actionable is True


def test_07_exclusion_of_unassessed_requirements():
    # Unassessed requirements must have zero gap and be marked as non-actionable
    req_input = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=0.00,
        coverage_credit=0.00,
        student_proficiency=None,
        assessment_status=RequirementAssessmentStatus.UNASSESSED.value,
        match_type="UNASSESSED",
        skill_id="SK-000007",
        standard_name="Legacy System",
    )
    result = calculate_single_skill_gap(req_input)

    assert result.capability_gap == 0.0
    assert result.gap_classification == GapClassification.UNASSESSED.value
    assert result.is_actionable is False
    assert result.assessment_status == RequirementAssessmentStatus.UNASSESSED.value


def test_08_evidence_confidence_does_not_affect_gap():
    # Evidence confidence represents verification quality and must not alter the capability gap
    req_high_conf = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=0.50,
        evidence_confidence=1.00,
        skill_id="SK-000008",
        standard_name="Django",
    )
    req_low_conf = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=0.50,
        evidence_confidence=0.10,
        skill_id="SK-000008",
        standard_name="Django",
    )
    req_no_conf = SkillGapInput(
        requirement_id=uuid.uuid4(),
        required_proficiency=0.80,
        capability_coverage=0.50,
        evidence_confidence=None,
        skill_id="SK-000008",
        standard_name="Django",
    )

    res_high = calculate_single_skill_gap(req_high_conf)
    res_low = calculate_single_skill_gap(req_low_conf)
    res_none = calculate_single_skill_gap(req_no_conf)

    assert (
        res_high.capability_gap
        == res_low.capability_gap
        == res_none.capability_gap
        == 0.40
    )


def test_09_direct_consumption_of_readiness_result():
    # Algorithm 3A can consume RequirementReadinessResult directly from Algorithm 2
    readiness_input = RequirementReadinessInput(
        requirement_id=uuid.uuid4(),
        demand_weight=0.90,
        required_proficiency=0.80,
        coverage_credit=1.00,
        student_proficiency=0.60,
        evidence_confidence=0.80,
        skill_id="SK-000009",
        standard_name="FastAPI",
    )
    readiness_res = calculate_single_requirement_readiness(readiness_input)

    # Readiness result has capability_coverage = 1.0 * (0.6 / 0.8) = 0.75
    gap_res = calculate_single_skill_gap(readiness_res)

    # Expected gap: 0.80 * (1.0 - 0.75) = 0.20
    assert pytest.approx(gap_res.capability_gap, rel=1e-5) == 0.20
    assert gap_res.gap_classification == GapClassification.PARTIALLY_COVERED.value
    assert gap_res.required_canonical_skill_id == "SK-000009"
    assert gap_res.required_skill_name == "FastAPI"
    assert gap_res.demand_weight == 0.90


def test_10_batch_calculation_of_diverse_skills():
    # Batch calculate gaps across covered, partial, missing, and unassessed items
    items = [
        SkillGapInput(
            requirement_id="REQ-1",
            required_proficiency=0.8,
            capability_coverage=1.0,
            skill_id="SK-1",
            standard_name="Python",
        ),
        SkillGapInput(
            requirement_id="REQ-2",
            required_proficiency=0.8,
            capability_coverage=0.5,
            skill_id="SK-2",
            standard_name="Docker",
        ),
        SkillGapInput(
            requirement_id="REQ-3",
            required_proficiency=0.6,
            capability_coverage=0.0,
            skill_id="SK-3",
            standard_name="Kubernetes",
        ),
        SkillGapInput(
            requirement_id="REQ-4",
            required_proficiency=0.5,
            capability_coverage=0.0,
            skill_id="SK-4",
            assessment_status=RequirementAssessmentStatus.UNASSESSED.value,
        ),
    ]
    results = calculate_skill_gaps(items)

    assert len(results) == 4
    assert results[0].gap_classification == GapClassification.COVERED.value
    assert results[0].capability_gap == 0.0

    assert results[1].gap_classification == GapClassification.PARTIALLY_COVERED.value
    assert pytest.approx(results[1].capability_gap, rel=1e-5) == 0.40

    assert results[2].gap_classification == GapClassification.MISSING.value
    assert pytest.approx(results[2].capability_gap, rel=1e-5) == 0.60

    assert results[3].gap_classification == GapClassification.UNASSESSED.value
    assert results[3].is_actionable is False


def test_11_input_validation_errors():
    # Test strict validation for missing, out-of-range, and invalid types
    with pytest.raises(ValueError, match="strictly greater than 0"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=0.0,
                capability_coverage=0.5,
            )
        )

    with pytest.raises(ValueError, match="cannot exceed 1.0"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=1.5,
                capability_coverage=0.5,
            )
        )

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=0.8,
                capability_coverage=-0.1,
            )
        )

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=0.8,
                capability_coverage=1.2,
            )
        )

    with pytest.raises(ValueError, match="must be finite"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=float("nan"),
                capability_coverage=0.5,
            )
        )

    with pytest.raises(ValueError, match="must be finite"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=0.8,
                capability_coverage=float("inf"),
            )
        )

    with pytest.raises(TypeError, match="must be a float or int"):
        calculate_single_skill_gap(
            SkillGapInput(
                requirement_id="REQ-VAL",
                required_proficiency=True,  # bool rejected
                capability_coverage=0.5,
            )
        )
