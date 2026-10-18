import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.algorithms.readiness import (
    OverallReadinessResult,
    RequirementAssessmentStatus,
)
from app.algorithms.skill_gaps import (
    GapClassification,
    SkillGapResult,
    calculate_skill_gaps,
)


# Evaluated and ranked learning priority item for downstream consumption
@dataclass(frozen=True)
class PrioritySkillResult:
    priority_rank: int
    industry_requirement_id: UUID | str
    required_canonical_skill_id: str
    required_skill_name: str
    learning_priority: float
    capability_gap: float
    demand_weight: float
    required_proficiency: float
    student_proficiency: float | None
    gap_classification: str
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


# Rank assessable skill gaps by industry importance and gap size
def calculate_learning_priorities(
    skill_gaps: Sequence[SkillGapResult | Any],
    include_covered: bool = False,
) -> list[PrioritySkillResult]:
    candidates: list[dict[str, Any]] = []

    for item in skill_gaps:
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
        gap_class = str(
            _extract_val(
                item,
                "gap_classification",
                default=GapClassification.MISSING.value,
            )
        )
        explanation = str(_extract_val(item, "explanation", default=""))
        req_prof = _extract_val(
            item, "required_proficiency", "required_proficiency_score", default=1.0
        )
        stu_prof = _extract_val(item, "student_proficiency", "proficiency_score")

        # Unassessed requirements must be excluded from learning priority ranking
        if (
            assessment_status == RequirementAssessmentStatus.UNASSESSED.value
            or gap_class == GapClassification.UNASSESSED.value
        ):
            continue

        raw_gap = _extract_val(item, "capability_gap", "gap")
        raw_demand_weight = _extract_val(
            item, "demand_weight", "industry_weight", default=1.0
        )

        capability_gap = _validate_non_negative("capability_gap", raw_gap, req_id)
        demand_weight = _validate_non_negative(
            "demand_weight", raw_demand_weight, req_id
        )

        # Exclude fully covered skills from actionable priority list unless explicitly requested
        is_covered = (
            gap_class == GapClassification.COVERED.value or capability_gap <= 1e-9
        )
        if is_covered and not include_covered:
            continue

        # Algorithm 3B: learning_priority = demand_weight * capability_gap
        learning_priority = round(demand_weight * capability_gap, 6)

        candidates.append(
            {
                "requirement_id": req_id,
                "skill_id": str(skill_id or ""),
                "skill_name": standard_name,
                "learning_priority": learning_priority,
                "capability_gap": capability_gap,
                "demand_weight": demand_weight,
                "required_proficiency": float(req_prof),
                "student_proficiency": float(stu_prof)
                if stu_prof is not None
                else None,
                "gap_classification": gap_class,
                "explanation": explanation,
            }
        )

    # Deterministic sorting: descending priority, descending demand weight, ascending canonical skill ID
    candidates.sort(
        key=lambda c: (
            -c["learning_priority"],
            -c["demand_weight"],
            c["skill_id"],
            str(c["requirement_id"]),
        )
    )

    # 1-indexed priority ranking starting at 1
    ranked_results: list[PrioritySkillResult] = []
    for rank, cand in enumerate(candidates, start=1):
        ranked_results.append(
            PrioritySkillResult(
                priority_rank=rank,
                industry_requirement_id=cand["requirement_id"],
                required_canonical_skill_id=cand["skill_id"],
                required_skill_name=cand["skill_name"],
                learning_priority=cand["learning_priority"],
                capability_gap=cand["capability_gap"],
                demand_weight=cand["demand_weight"],
                required_proficiency=cand["required_proficiency"],
                student_proficiency=cand["student_proficiency"],
                gap_classification=cand["gap_classification"],
                explanation=cand["explanation"]
                or f"Rank #{rank}: priority {cand['learning_priority']:.4f} (weight={cand['demand_weight']:.2f}, gap={cand['capability_gap']:.2f})",
            )
        )

    return ranked_results


# Compute prioritized skill gaps directly from an overall readiness result
def prioritize_from_readiness(
    overall_readiness: OverallReadinessResult,
    include_covered: bool = False,
) -> list[PrioritySkillResult]:
    skill_gaps = calculate_skill_gaps(overall_readiness.requirement_results)
    return calculate_learning_priorities(skill_gaps, include_covered=include_covered)


# Convert prioritized results into the agreed external C04 target payload structure
def format_c04_payload(
    priority_skills: Sequence[PrioritySkillResult],
    role_name: str,
    readiness_score: float | None,
    analysis_id: UUID | str | None = None,
    user_id: UUID | str | None = None,
    role_id: UUID | str | None = None,
) -> dict[str, Any]:
    return {
        "analysisId": str(analysis_id) if analysis_id is not None else None,
        "user_id": str(user_id) if user_id is not None else None,
        "roleId": str(role_id) if role_id is not None else None,
        "roleName": str(role_name),
        "readinessScore": (
            round(float(readiness_score), 4) if readiness_score is not None else None
        ),
        "prioritySkills": [
            {
                "skillId": item.required_canonical_skill_id,
                "skillName": item.required_skill_name,
                "priorityRank": item.priority_rank,
                "learningPriority": round(float(item.learning_priority), 4),
                "gap": round(float(item.capability_gap), 4),
            }
            for item in priority_skills
        ],
    }
