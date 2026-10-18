import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from app.algorithms.readiness import (
    RequirementAssessmentStatus,
    RequirementReadinessResult,
)


class GapClassification(str, Enum):
    MISSING = "MISSING"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    COVERED = "COVERED"
    UNASSESSED = "UNASSESSED"


# Input contract for evaluating the skill gap of an industry requirement
@dataclass(frozen=True)
class SkillGapInput:
    requirement_id: UUID | str
    required_proficiency: float
    capability_coverage: float
    coverage_credit: float = 0.0
    student_proficiency: float | None = None
    demand_weight: float = 1.0
    skill_id: str | None = None
    standard_name: str = ""
    assessment_status: str = RequirementAssessmentStatus.ASSESSED.value
    match_type: str = "EXACT"
    evidence_confidence: float | None = None
    explanation: str = ""


# Evaluated capability gap and classification for a single industry requirement
@dataclass(frozen=True)
class SkillGapResult:
    industry_requirement_id: UUID | str
    required_canonical_skill_id: str | None
    required_skill_name: str
    required_proficiency: float
    student_proficiency: float | None
    coverage_credit: float
    capability_coverage: float
    capability_gap: float
    assessment_status: str
    gap_classification: str
    demand_weight: float
    evidence_confidence: float | None
    is_actionable: bool
    explanation: str


# Validate non-negative finite numeric field
def _validate_non_negative(field_name: str, value: Any, requirement_id: Any) -> float:
    if value is None:
        raise ValueError(
            f"Requirement '{requirement_id}': field '{field_name}' cannot be None"
        )
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(
            f"Requirement '{requirement_id}': field '{field_name}' must be a float or int, got {type(value).__name__}"
        )
    float_val = float(value)
    if not math.isfinite(float_val):
        raise ValueError(
            f"Requirement '{requirement_id}': field '{field_name}' must be finite, got {float_val}"
        )
    if float_val < 0.0:
        raise ValueError(
            f"Requirement '{requirement_id}': field '{field_name}' cannot be negative, got {float_val}"
        )
    return float_val


# Validate required proficiency is strictly positive and within unit upper bound
def _validate_required_proficiency(value: Any, requirement_id: Any) -> float:
    float_val = _validate_non_negative("required_proficiency", value, requirement_id)
    if float_val <= 0.0:
        raise ValueError(
            f"Requirement '{requirement_id}': required_proficiency must be strictly greater than 0, got {float_val}"
        )
    if float_val > 1.0:
        raise ValueError(
            f"Requirement '{requirement_id}': required_proficiency cannot exceed 1.0, got {float_val}"
        )
    return float_val


# Validate ratio field strictly bounded between 0 and 1
def _validate_unit_ratio(
    field_name: str, value: Any, requirement_id: Any, allow_none: bool = False
) -> float | None:
    if value is None:
        if allow_none:
            return None
        raise ValueError(
            f"Requirement '{requirement_id}': field '{field_name}' cannot be None"
        )
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(
            f"Requirement '{requirement_id}': field '{field_name}' must be a float or int, got {type(value).__name__}"
        )
    float_val = float(value)
    if not math.isfinite(float_val):
        raise ValueError(
            f"Requirement '{requirement_id}': field '{field_name}' must be finite, got {float_val}"
        )
    if not (0.0 <= float_val <= 1.0):
        raise ValueError(
            f"Requirement '{requirement_id}': field '{field_name}' must be between 0.0 and 1.0, got {float_val}"
        )
    return float_val


# Extract field value supporting dataclasses, objects, and dictionaries
def _extract_val(obj: Any, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
        if hasattr(obj, k):
            val = getattr(obj, k)
            if val is not None:
                return val
    return default


# Calculate capability gap and classification for a single industry requirement
def calculate_single_skill_gap(
    item: SkillGapInput | RequirementReadinessResult | Any,
) -> SkillGapResult:
    req_id = _extract_val(item, "industry_requirement_id", "requirement_id", "id")
    skill_id = _extract_val(item, "required_canonical_skill_id", "skill_id")
    standard_name = _extract_val(
        item, "required_skill_name", "standard_name", default=""
    )
    assessment_status = str(
        _extract_val(
            item,
            "assessment_status",
            default=RequirementAssessmentStatus.ASSESSED.value,
        )
    )
    match_type = str(_extract_val(item, "match_type", default="EXACT"))
    explanation = str(_extract_val(item, "explanation", default=""))

    raw_req_prof = _extract_val(
        item, "required_proficiency", "required_proficiency_score"
    )
    raw_cap_cov = _extract_val(item, "capability_coverage")
    raw_cov_credit = _extract_val(item, "coverage_credit", default=0.0)
    raw_stu_prof = _extract_val(item, "student_proficiency", "proficiency_score")
    raw_demand_weight = _extract_val(
        item, "demand_weight", "industry_weight", default=1.0
    )
    raw_evidence_conf = _extract_val(item, "evidence_confidence")

    # Validate numerical inputs against domain constraints
    required_proficiency = _validate_required_proficiency(raw_req_prof, req_id)
    capability_coverage = _validate_unit_ratio(
        "capability_coverage", raw_cap_cov, req_id, allow_none=False
    )
    assert capability_coverage is not None

    coverage_credit = (
        _validate_unit_ratio(
            "coverage_credit", raw_cov_credit, req_id, allow_none=False
        )
        or 0.0
    )
    student_proficiency = _validate_unit_ratio(
        "student_proficiency", raw_stu_prof, req_id, allow_none=True
    )
    demand_weight = _validate_non_negative("demand_weight", raw_demand_weight, req_id)
    evidence_confidence = _validate_unit_ratio(
        "evidence_confidence", raw_evidence_conf, req_id, allow_none=True
    )

    # Exclude unassessed taxonomy requirements from actionable skill gaps
    if (
        assessment_status == RequirementAssessmentStatus.UNASSESSED.value
        or match_type.upper() == "UNASSESSED"
    ):
        return SkillGapResult(
            industry_requirement_id=req_id,
            required_canonical_skill_id=skill_id,
            required_skill_name=standard_name,
            required_proficiency=required_proficiency,
            student_proficiency=student_proficiency,
            coverage_credit=0.0,
            capability_coverage=0.0,
            capability_gap=0.0,
            assessment_status=RequirementAssessmentStatus.UNASSESSED.value,
            gap_classification=GapClassification.UNASSESSED.value,
            demand_weight=demand_weight,
            evidence_confidence=evidence_confidence,
            is_actionable=False,
            explanation=explanation
            or "Requirement is unassessed in SSKS taxonomy and excluded from actionable gap results",
        )

    # Algorithm 3A: capability_gap = required_proficiency * (1.0 - capability_coverage)
    # Evidence confidence is excluded from gap calculation to prevent penalizing evidence quality as skill deficiency
    raw_gap = required_proficiency * (1.0 - capability_coverage)
    capability_gap = max(0.0, round(raw_gap, 6))

    # Classify assessable requirements into MISSING, PARTIALLY_COVERED, or COVERED
    if capability_coverage <= 1e-9:
        gap_classification = GapClassification.MISSING.value
        is_actionable = True
        default_explanation = (
            f"Missing skill: full gap of {capability_gap:.2f} required"
        )
    elif capability_gap <= 1e-9 or capability_coverage >= (1.0 - 1e-9):
        capability_gap = 0.0
        gap_classification = GapClassification.COVERED.value
        is_actionable = False
        default_explanation = "Skill fully covered; no remaining development gap"
    else:
        gap_classification = GapClassification.PARTIALLY_COVERED.value
        is_actionable = True
        default_explanation = f"Partially covered ({capability_coverage:.2f}): remaining gap is {capability_gap:.2f}"

    return SkillGapResult(
        industry_requirement_id=req_id,
        required_canonical_skill_id=skill_id,
        required_skill_name=standard_name,
        required_proficiency=required_proficiency,
        student_proficiency=student_proficiency,
        coverage_credit=coverage_credit,
        capability_coverage=capability_coverage,
        capability_gap=capability_gap,
        assessment_status=assessment_status,
        gap_classification=gap_classification,
        demand_weight=demand_weight,
        evidence_confidence=evidence_confidence,
        is_actionable=is_actionable,
        explanation=explanation or default_explanation,
    )


# Calculate skill gaps for a sequence of requirements or readiness results
def calculate_skill_gaps(
    items: Sequence[SkillGapInput | RequirementReadinessResult | Any],
) -> list[SkillGapResult]:
    return [calculate_single_skill_gap(item) for item in items]
