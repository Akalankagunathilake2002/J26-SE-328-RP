import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from app.algorithms.matching import MatchingResult

DEFAULT_SCORING_VERSION = "1.0"


class ScoringStatus(str, Enum):
    CALCULATED = "CALCULATED"
    UNAVAILABLE = "UNAVAILABLE"
    NO_ASSESSABLE_REQUIREMENTS = "NO_ASSESSABLE_REQUIREMENTS"
    ZERO_DEMAND_WEIGHT = "ZERO_DEMAND_WEIGHT"


class RequirementAssessmentStatus(str, Enum):
    ASSESSED = "ASSESSED"
    UNASSESSED = "UNASSESSED"
    MISSING = "MISSING"


# Input contract for calculating readiness of a single industry requirement
@dataclass(frozen=True)
class RequirementReadinessInput:
    requirement_id: UUID | str
    demand_weight: float
    required_proficiency: float
    coverage_credit: float
    student_proficiency: float | None = None
    evidence_confidence: float | None = None
    skill_id: str | None = None
    standard_name: str = ""
    is_assessable: bool = True
    match_type: str = "EXACT"
    selected_student_skill_id: UUID | str | None = None
    explanation: str = ""


# Calculated intermediate readiness values and contribution for a single requirement
@dataclass(frozen=True)
class RequirementReadinessResult:
    industry_requirement_id: UUID | str
    required_canonical_skill_id: str | None
    required_skill_name: str
    matching_method: str
    match_type: str
    coverage_credit: float
    required_proficiency: float
    student_proficiency: float | None
    evidence_confidence: float | None
    proficiency_alignment: float
    capability_coverage: float
    readiness_satisfaction: float
    demand_weight: float
    weighted_contribution: float
    assessment_status: str
    explanation: str


# Aggregated role readiness score across all assessable industry requirements
@dataclass(frozen=True)
class OverallReadinessResult:
    overall_readiness: float | None
    matching_method: str
    scoring_formula_version: str
    assessable_requirements_count: int
    unassessed_requirements_count: int
    total_included_demand_weight: float
    sum_weighted_contributions: float
    status: str
    is_calculated: bool
    requirement_results: list[RequirementReadinessResult] = field(default_factory=list)
    explanation: str = ""


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


# Validate required proficiency is strictly positive and does not exceed unit upper bound
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


# Calculate readiness metrics for a single industry requirement
def calculate_single_requirement_readiness(
    item: RequirementReadinessInput,
    matching_method: str = "RELATIONSHIP_AWARE",
) -> RequirementReadinessResult:
    demand_weight = _validate_non_negative(
        "demand_weight", item.demand_weight, item.requirement_id
    )
    required_proficiency = _validate_required_proficiency(
        item.required_proficiency, item.requirement_id
    )
    coverage_credit = _validate_unit_ratio(
        "coverage_credit", item.coverage_credit, item.requirement_id, allow_none=False
    )
    assert coverage_credit is not None

    student_proficiency = _validate_unit_ratio(
        "student_proficiency",
        item.student_proficiency,
        item.requirement_id,
        allow_none=True,
    )
    evidence_confidence = _validate_unit_ratio(
        "evidence_confidence",
        item.evidence_confidence,
        item.requirement_id,
        allow_none=True,
    )

    # Unassessed requirements are excluded from readiness scoring to avoid penalizing students for unmapped taxonomy
    if not item.is_assessable or (item.match_type or "").upper() == "UNASSESSED":
        return RequirementReadinessResult(
            industry_requirement_id=item.requirement_id,
            required_canonical_skill_id=item.skill_id,
            required_skill_name=item.standard_name,
            matching_method=matching_method,
            match_type="UNASSESSED",
            coverage_credit=0.0,
            required_proficiency=required_proficiency,
            student_proficiency=student_proficiency,
            evidence_confidence=evidence_confidence,
            proficiency_alignment=0.0,
            capability_coverage=0.0,
            readiness_satisfaction=0.0,
            demand_weight=demand_weight,
            weighted_contribution=0.0,
            assessment_status=RequirementAssessmentStatus.UNASSESSED.value,
            explanation=item.explanation
            or "Requirement is unassessed in SSKS taxonomy and excluded from scoring",
        )

    # Missing requirement case: assessable requirement with no matching student skill
    is_missing = (
        coverage_credit <= 0.0
        or student_proficiency is None
        or (item.match_type or "").upper() == "MISSING"
    )

    if is_missing:
        # Intermediate alignment is calculated if proficiency exists, but capability coverage remains zero
        alignment = (
            min(1.0, student_proficiency / required_proficiency)
            if student_proficiency is not None
            else 0.0
        )
        return RequirementReadinessResult(
            industry_requirement_id=item.requirement_id,
            required_canonical_skill_id=item.skill_id,
            required_skill_name=item.standard_name,
            matching_method=matching_method,
            match_type=item.match_type or "MISSING",
            coverage_credit=coverage_credit,
            required_proficiency=required_proficiency,
            student_proficiency=student_proficiency,
            evidence_confidence=evidence_confidence,
            proficiency_alignment=alignment,
            capability_coverage=0.0,
            readiness_satisfaction=0.0,
            demand_weight=demand_weight,
            weighted_contribution=0.0,
            assessment_status=RequirementAssessmentStatus.MISSING.value,
            explanation=item.explanation
            or "No valid matching student skill covers this requirement",
        )

    # Step 1: Proficiency alignment capped at 1.0 when student meets or exceeds target
    proficiency_alignment = min(1.0, student_proficiency / required_proficiency)

    # Step 2: Capability coverage adjusts proficiency by matching credit
    capability_coverage = coverage_credit * proficiency_alignment

    # Step 3: Readiness satisfaction discounts coverage by evidence confidence
    confidence_factor = evidence_confidence if evidence_confidence is not None else 0.0
    readiness_satisfaction = capability_coverage * confidence_factor

    # Step 4: Weighted contribution weights satisfaction by industry importance
    weighted_contribution = demand_weight * readiness_satisfaction

    return RequirementReadinessResult(
        industry_requirement_id=item.requirement_id,
        required_canonical_skill_id=item.skill_id,
        required_skill_name=item.standard_name,
        matching_method=matching_method,
        match_type=item.match_type,
        coverage_credit=coverage_credit,
        required_proficiency=required_proficiency,
        student_proficiency=student_proficiency,
        evidence_confidence=evidence_confidence,
        proficiency_alignment=proficiency_alignment,
        capability_coverage=capability_coverage,
        readiness_satisfaction=readiness_satisfaction,
        demand_weight=demand_weight,
        weighted_contribution=weighted_contribution,
        assessment_status=RequirementAssessmentStatus.ASSESSED.value,
        explanation=item.explanation
        or f"Satisfied at {readiness_satisfaction:.2f} (alignment={proficiency_alignment:.2f}, coverage={capability_coverage:.2f})",
    )


# Calculate overall career readiness score across all prepared requirement inputs
def calculate_readiness(
    items: Sequence[RequirementReadinessInput],
    matching_method: str = "RELATIONSHIP_AWARE",
    scoring_version: str = DEFAULT_SCORING_VERSION,
) -> OverallReadinessResult:
    per_requirement_results: list[RequirementReadinessResult] = [
        calculate_single_requirement_readiness(item, matching_method=matching_method)
        for item in items
    ]

    assessable_results = [
        r
        for r in per_requirement_results
        if r.assessment_status != RequirementAssessmentStatus.UNASSESSED.value
    ]
    unassessed_results = [
        r
        for r in per_requirement_results
        if r.assessment_status == RequirementAssessmentStatus.UNASSESSED.value
    ]

    # Return unavailable when no assessable requirements exist to distinguish from a true 0.0 readiness score
    if not assessable_results:
        return OverallReadinessResult(
            overall_readiness=None,
            matching_method=matching_method,
            scoring_formula_version=scoring_version,
            assessable_requirements_count=0,
            unassessed_requirements_count=len(unassessed_results),
            total_included_demand_weight=0.0,
            sum_weighted_contributions=0.0,
            status=ScoringStatus.NO_ASSESSABLE_REQUIREMENTS.value,
            is_calculated=False,
            requirement_results=per_requirement_results,
            explanation="No assessable industry requirements found for readiness scoring",
        )

    total_included_weight = sum(r.demand_weight for r in assessable_results)
    sum_contributions = sum(r.weighted_contribution for r in assessable_results)

    # Demand weight sum of zero cannot form a valid weighted average denominator
    if total_included_weight <= 0.0:
        return OverallReadinessResult(
            overall_readiness=None,
            matching_method=matching_method,
            scoring_formula_version=scoring_version,
            assessable_requirements_count=len(assessable_results),
            unassessed_requirements_count=len(unassessed_results),
            total_included_demand_weight=0.0,
            sum_weighted_contributions=sum_contributions,
            status=ScoringStatus.ZERO_DEMAND_WEIGHT.value,
            is_calculated=False,
            requirement_results=per_requirement_results,
            explanation="Total assessable demand weight is zero; cannot compute weighted readiness score",
        )

    # Step 5: Overall readiness normalized on a 0 to 100 percentage scale
    overall_readiness = 100.0 * (sum_contributions / total_included_weight)

    return OverallReadinessResult(
        overall_readiness=round(overall_readiness, 4),
        matching_method=matching_method,
        scoring_formula_version=scoring_version,
        assessable_requirements_count=len(assessable_results),
        unassessed_requirements_count=len(unassessed_results),
        total_included_demand_weight=round(total_included_weight, 4),
        sum_weighted_contributions=round(sum_contributions, 4),
        status=ScoringStatus.CALCULATED.value,
        is_calculated=True,
        requirement_results=per_requirement_results,
        explanation=f"Overall readiness score: {overall_readiness:.2f}% across {len(assessable_results)} assessable requirements",
    )


# Extract field value from object attribute or dictionary
def _extract_val(obj: Any, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
        if hasattr(obj, k):
            val = getattr(obj, k)
            if val is not None:
                return val
    return default


# Adapter coordinating industry requirements, matching results, and student skill proficiency
def score_readiness(
    requirements: Sequence[Any],
    matching_results: Sequence[MatchingResult],
    student_skills: Sequence[Any] = (),
    matching_method: str = "RELATIONSHIP_AWARE",
    scoring_version: str = DEFAULT_SCORING_VERSION,
) -> OverallReadinessResult:
    # Index matching results by requirement ID
    matching_map: dict[str, MatchingResult] = {
        str(m.industry_requirement_id): m for m in matching_results
    }

    # Index student skills by record ID
    student_map: dict[str, Any] = {}
    for s in student_skills:
        s_id = _extract_val(s, "skill_record_id", "id")
        if s_id is not None:
            student_map[str(s_id)] = s

    scoring_inputs: list[RequirementReadinessInput] = []

    for req in requirements:
        req_id = _extract_val(req, "requirement_id", "id")
        demand_weight = _extract_val(req, "demand_weight", default=1.0)
        req_prof = _extract_val(
            req, "required_proficiency", "required_proficiency_score", default=1.0
        )
        skill_id = _extract_val(req, "skill_id")
        standard_name = _extract_val(req, "standard_name", default="")
        mapping_status = _extract_val(req, "mapping_status", default="RESOLVED")

        match_res = matching_map.get(str(req_id))

        if match_res is not None:
            if skill_id is None:
                skill_id = match_res.required_canonical_skill_id
            if not standard_name:
                standard_name = match_res.required_skill_name
            coverage_credit = match_res.coverage_credit
            match_type = match_res.match_type
            selected_student_id = match_res.selected_student_skill_id
            explanation = match_res.explanation
            is_assessable = match_type.upper() != "UNASSESSED"
        else:
            coverage_credit = 0.0
            match_type = "MISSING"
            selected_student_id = None
            explanation = "No matching result provided"
            is_assessable = (
                mapping_status.upper() in ("RESOLVED", "VERIFIED")
                and skill_id is not None
            )

        student_prof = None
        evidence_conf = None

        if selected_student_id is not None:
            stu = student_map.get(str(selected_student_id))
            if stu is not None:
                student_prof = _extract_val(
                    stu, "student_proficiency", "proficiency_score", default=0.0
                )
                evidence_conf = _extract_val(stu, "evidence_confidence", default=1.0)

        scoring_inputs.append(
            RequirementReadinessInput(
                requirement_id=req_id,
                demand_weight=demand_weight,
                required_proficiency=req_prof,
                coverage_credit=coverage_credit,
                student_proficiency=student_prof,
                evidence_confidence=evidence_conf,
                skill_id=skill_id,
                standard_name=standard_name,
                is_assessable=is_assessable,
                match_type=match_type,
                selected_student_skill_id=selected_student_id,
                explanation=explanation,
            )
        )

    return calculate_readiness(
        scoring_inputs,
        matching_method=matching_method,
        scoring_version=scoring_version,
    )
