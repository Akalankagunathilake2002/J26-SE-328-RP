from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class MatchingMethod(str, Enum):
    # Standard baseline: awards credit only on exact canonical skill ID or verified alias normalization
    EXACT_BASELINE = "EXACT_BASELINE"
    # Experimental method: augments exact matching with verified SSKS taxonomy relationships
    RELATIONSHIP_AWARE = "RELATIONSHIP_AWARE"


class MatchType(str, Enum):
    EXACT = "EXACT"
    ALIAS = "ALIAS"
    EQUIVALENT = "EQUIVALENT"
    PARTIAL_RELATIONSHIP = "PARTIAL_RELATIONSHIP"
    MISSING = "MISSING"
    UNASSESSED = "UNASSESSED"


class MatchResultStatus(str, Enum):
    MATCHED = "MATCHED"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    MISSING = "MISSING"
    UNASSESSED = "UNASSESSED"


class RelationshipType(str, Enum):
    EQUIVALENT_TO = "EQUIVALENT_TO"
    BROADER_THAN = "BROADER_THAN"
    NARROWER_THAN = "NARROWER_THAN"
    PART_OF = "PART_OF"
    PREREQUISITE_OF = "PREREQUISITE_OF"
    RELATED_TO = "RELATED_TO"


class RelationshipDirection(str, Enum):
    # Student skill is source and required skill is target
    STUDENT_IS_SOURCE = "STUDENT_IS_SOURCE"
    # Student skill is target and required skill is source
    STUDENT_IS_TARGET = "STUDENT_IS_TARGET"


@dataclass(frozen=True)
class RequirementInput:
    requirement_id: UUID | str
    skill_id: str | None
    standard_name: str
    mapping_status: str
    required_proficiency: str = "INTERMEDIATE"
    demand_weight: float = 1.0


@dataclass(frozen=True)
class StudentSkillInput:
    skill_record_id: UUID | str
    skill_id: str | None
    standard_name: str
    primary_observed_term: str = ""
    observed_terms: list[str] = field(default_factory=list)
    mapping_status: str = "RESOLVED"
    proficiency_level: str = "INTERMEDIATE"


@dataclass(frozen=True)
class AliasInput:
    alias_id: str
    skill_id: str
    alias_text: str
    normalized_alias: str


@dataclass(frozen=True)
class RelationshipInput:
    relationship_id: str
    source_skill_id: str
    target_skill_id: str
    relationship_type: str
    verification_status: str = "VERIFIED"
    evidence_note: str | None = None


# Default calibrated partial coverage coefficients by relationship type and direction
DEFAULT_PARTIAL_COEFFICIENTS: dict[tuple[str, str], float] = {
    (RelationshipType.NARROWER_THAN.value, RelationshipDirection.STUDENT_IS_SOURCE.value): 0.75,
    (RelationshipType.BROADER_THAN.value, RelationshipDirection.STUDENT_IS_TARGET.value): 0.75,
    (RelationshipType.PART_OF.value, RelationshipDirection.STUDENT_IS_TARGET.value): 0.75,
    (RelationshipType.PART_OF.value, RelationshipDirection.STUDENT_IS_SOURCE.value): 0.50,
}


# Immutable policy configuration encapsulating matching method and calibrated partial coefficients
@dataclass(frozen=True)
class MatchingPolicy:
    method: MatchingMethod = MatchingMethod.RELATIONSHIP_AWARE
    version: str = "1.0"
    # Stores the approved partial coverage credit for each relationship type and direction.
    partial_coefficients: dict[tuple[str, str], float] = field(
        default_factory=lambda: dict(DEFAULT_PARTIAL_COEFFICIENTS)
    )

    def __post_init__(self) -> None:
        # Partial relationship coefficients must be explicitly validated policy parameters
        for (rel_type, direction), coeff in self.partial_coefficients.items():
            if rel_type in (
                RelationshipType.RELATED_TO.value,
                RelationshipType.PREREQUISITE_OF.value,
            ):
                raise ValueError(
                    f"Relationship type '{rel_type}' cannot award direct readiness coverage by definition"
                )

            if not isinstance(coeff, (int, float)) or not (0.0 < float(coeff) < 1.0):
                raise ValueError(
                    f"Partial coverage coefficient for ({rel_type}, {direction}) must be strictly between 0 and 1, got {coeff}"
                )


@dataclass
class CandidateMatch:
    # 1: EXACT, 2: ALIAS, 3: EQUIVALENT, 4: PARTIAL
    priority: int
    student_skill: StudentSkillInput
    match_type: MatchType
    coverage_credit: float
    relationship: RelationshipInput | None
    explanation: str


@dataclass(frozen=True)
class MatchingResult:
    industry_requirement_id: UUID | str
    required_canonical_skill_id: str | None
    required_skill_name: str
    requirement_mapping_status: str
    selected_student_skill_id: UUID | str | None
    matched_canonical_skill_id: str | None
    matched_skill_name: str | None
    match_type: str
    selected_relationship_id: str | None
    selected_relationship_type: str | None
    relationship_source_skill_id: str | None
    relationship_target_skill_id: str | None
    coverage_credit: float
    result_status: str
    explanation: str
    candidate_diagnostics: list[dict[str, Any]] = field(default_factory=list)


# Check whether an industry requirement has been resolved to an authoritative canonical entity
def is_requirement_assessable(req: RequirementInput) -> bool:
    if not req.skill_id or not str(req.skill_id).strip():
        return False
    status = (req.mapping_status or "").strip().upper()
    return status in ("RESOLVED", "VERIFIED", "CANONICAL")


# Normalize skill term for case-insensitive and whitespace-invariant alias lookup
def normalize_term(term: str | None) -> str:
    if not term:
        return ""
    return term.strip().lower()


# Index verified aliases by normalized alias text mapping to canonical skill ID
def build_alias_index(aliases: Sequence[AliasInput]) -> dict[str, str]:
    # Aliases normalize distinct surface expressions to their shared canonical identity
    index: dict[str, str] = {}
    for a in aliases:
        if a.skill_id and a.normalized_alias:
            index[normalize_term(a.normalized_alias)] = a.skill_id
        elif a.skill_id and a.alias_text:
            index[normalize_term(a.alias_text)] = a.skill_id
    return index


# Index relationships by participating canonical skill IDs for constant-time lookup
def build_relationship_index(
    relationships: Sequence[RelationshipInput],
) -> dict[str, list[RelationshipInput]]:
    index: dict[str, list[RelationshipInput]] = {}
    for r in relationships:
        if not r.source_skill_id or not r.target_skill_id:
            continue
        index.setdefault(r.source_skill_id, []).append(r)
        index.setdefault(r.target_skill_id, []).append(r)
    return index


# Resolve student skill canonical ID directly or through verified alias normalization
def resolve_student_skill_id(
    student_skill: StudentSkillInput,
    alias_index: dict[str, str],
) -> tuple[str | None, bool]:
    # Canonical ID takes precedence over alias dictionary lookup
    if student_skill.skill_id and str(student_skill.skill_id).strip():
        return str(student_skill.skill_id).strip(), False

    # Check observed surface terms against verified aliases
    candidate_terms = [
        student_skill.primary_observed_term,
        student_skill.standard_name,
        *student_skill.observed_terms,
    ]
    for term in candidate_terms:
        norm = normalize_term(term)
        if norm and norm in alias_index:
            return alias_index[norm], True

    return None, False


# Evaluate directional eligibility for verified hierarchical or compositional relationships
def evaluate_relationship_eligibility(
    rel: RelationshipInput,
    student_canonical_id: str,
    required_canonical_id: str,
    policy: MatchingPolicy,
) -> tuple[bool, float, str, str]:
    # Unverified relationships are rejected to uphold knowledge snapshot integrity
    if (rel.verification_status or "").upper() != "VERIFIED":
        return False, 0.0, "", "Relationship is unverified in knowledge snapshot"

    rel_type = (rel.relationship_type or "").upper()

    # RELATED_TO is an informal topical association that does not guarantee capability
    if rel_type == RelationshipType.RELATED_TO.value:
        return (
            False,
            0.0,
            "",
            "RELATED_TO relationships provide no direct readiness coverage",
        )

    # PREREQUISITE_OF specifies curricular sequencing, not skill substitutability
    if rel_type == RelationshipType.PREREQUISITE_OF.value:
        return (
            False,
            0.0,
            "",
            "PREREQUISITE_OF specifies learning order, not requirement satisfaction",
        )

    # EQUIVALENT_TO represents bidirectional semantic equivalence across taxonomies
    if rel_type == RelationshipType.EQUIVALENT_TO.value:
        is_match = (
            rel.source_skill_id == student_canonical_id
            and rel.target_skill_id == required_canonical_id
        ) or (
            rel.source_skill_id == required_canonical_id
            and rel.target_skill_id == student_canonical_id
        )
        if is_match:
            return True, 1.0, "EQUIVALENT", "Verified equivalent skill relationship"
        return False, 0.0, "", "Relationship does not connect candidate and requirement"

    # Determine relationship direction relative to student and industry requirement
    direction: RelationshipDirection | None = None
    if (
        rel.source_skill_id == student_canonical_id
        and rel.target_skill_id == required_canonical_id
    ):
        direction = RelationshipDirection.STUDENT_IS_SOURCE
    elif (
        rel.source_skill_id == required_canonical_id
        and rel.target_skill_id == student_canonical_id
    ):
        direction = RelationshipDirection.STUDENT_IS_TARGET

    if not direction:
        return False, 0.0, "", "Relationship endpoints do not match skills"

    # Validate directional semantics to prevent invalid generalization assumptions
    is_direction_valid = False
    if (
        rel_type == RelationshipType.NARROWER_THAN.value
        and direction == RelationshipDirection.STUDENT_IS_SOURCE
    ):
        # Student possesses a specialized skill (e.g. React) satisfying a general requirement (e.g. JavaScript)
        is_direction_valid = True
    elif (
        rel_type == RelationshipType.BROADER_THAN.value
        and direction == RelationshipDirection.STUDENT_IS_TARGET
    ):
        # Requirement is broad (source) and student possesses a narrower specialization (target)
        is_direction_valid = True
    elif (
        rel_type == RelationshipType.PART_OF.value
        and direction == RelationshipDirection.STUDENT_IS_TARGET
    ):
        # Student possesses a composite stack (e.g. MERN) containing the required component (e.g. MongoDB)
        is_direction_valid = True
    elif (
        rel_type == RelationshipType.PART_OF.value
        and direction == RelationshipDirection.STUDENT_IS_SOURCE
    ):
        # Student possesses a component skill (e.g. React) partially satisfying a composite stack requirement (e.g. MERN Stack)
        is_direction_valid = True

    if not is_direction_valid:
        return (
            False,
            0.0,
            "",
            f"Inverse direction for {rel_type} ({direction.value}) does not justify requirement coverage",
        )

    # Check whether an approved numeric coefficient has been configured for this type and direction
    policy_key = (rel_type, direction.value)
    if policy_key in policy.partial_coefficients:
        credit = float(policy.partial_coefficients[policy_key])
        return (
            True,
            credit,
            "PARTIAL_RELATIONSHIP",
            f"Verified {rel_type} relationship in valid direction ({direction.value}) with calibrated credit {credit}",
        )

    return (
        False,
        0.0,
        "",
        f"Verified {rel_type} relationship found, but no approved partial coefficient configured for {policy_key}",
    )


# Find the single winning student skill for an industry requirement
def match_single_requirement(
    req: RequirementInput,
    student_skills: Sequence[StudentSkillInput],
    alias_index: dict[str, str],
    rel_index: dict[str, list[RelationshipInput]],
    policy: MatchingPolicy,
    exact_req_skill_ids: set[str] | None = None,
) -> MatchingResult:
    # Unresolved requirements cannot be verified fairly and are flagged as unassessed
    if not is_requirement_assessable(req):
        return MatchingResult(
            industry_requirement_id=req.requirement_id,
            required_canonical_skill_id=req.skill_id,
            required_skill_name=req.standard_name,
            requirement_mapping_status=req.mapping_status,
            selected_student_skill_id=None,
            matched_canonical_skill_id=None,
            matched_skill_name=None,
            match_type=MatchType.UNASSESSED.value,
            selected_relationship_id=None,
            selected_relationship_type=None,
            relationship_source_skill_id=None,
            relationship_target_skill_id=None,
            coverage_credit=0.0,
            result_status=MatchResultStatus.UNASSESSED.value,
            explanation="Requirement is unmapped or unresolved in SSKS taxonomy and cannot be assessed",
            candidate_diagnostics=[],
        )

    required_canonical_id = str(req.skill_id).strip()
    candidates: list[CandidateMatch] = []

    # Evaluate each student skill independently against the current requirement
    for student_skill in student_skills:
        student_canonical_id, matched_via_alias = resolve_student_skill_id(
            student_skill, alias_index
        )

        if not student_canonical_id:
            continue

        # 1. Exact canonical identity
        if student_canonical_id == required_canonical_id:
            if not matched_via_alias:
                candidates.append(
                    CandidateMatch(
                        priority=1,
                        student_skill=student_skill,
                        match_type=MatchType.EXACT,
                        coverage_credit=1.0,
                        relationship=None,
                        explanation=f"Exact canonical skill match ({required_canonical_id})",
                    )
                )
            else:
                candidates.append(
                    CandidateMatch(
                        priority=2,
                        student_skill=student_skill,
                        match_type=MatchType.ALIAS,
                        coverage_credit=1.0,
                        relationship=None,
                        explanation=f"Verified alias resolved to required canonical skill ({required_canonical_id})",
                    )
                )
            continue

        # Exact baseline mode strictly prohibits relationship and similarity credit
        if policy.method == MatchingMethod.EXACT_BASELINE:
            continue

        # 2. Relationship-aware matching using verified SSKS graph edges
        related_edges = rel_index.get(student_canonical_id, [])
        for rel in related_edges:
            eligible, credit, match_cat, reason = evaluate_relationship_eligibility(
                rel=rel,
                student_canonical_id=student_canonical_id,
                required_canonical_id=required_canonical_id,
                policy=policy,
            )
            if eligible:
                prio = 3 if match_cat == "EQUIVALENT" else 4
                mtype = (
                    MatchType.EQUIVALENT
                    if match_cat == "EQUIVALENT"
                    else MatchType.PARTIAL_RELATIONSHIP
                )
                candidates.append(
                    CandidateMatch(
                        priority=prio,
                        student_skill=student_skill,
                        match_type=mtype,
                        coverage_credit=credit,
                        relationship=rel,
                        explanation=reason,
                    )
                )

    # Missing requirement case when no candidate satisfies the criteria
    if not candidates:
        return MatchingResult(
            industry_requirement_id=req.requirement_id,
            required_canonical_skill_id=req.skill_id,
            required_skill_name=req.standard_name,
            requirement_mapping_status=req.mapping_status,
            selected_student_skill_id=None,
            matched_canonical_skill_id=None,
            matched_skill_name=None,
            match_type=MatchType.MISSING.value,
            selected_relationship_id=None,
            selected_relationship_type=None,
            relationship_source_skill_id=None,
            relationship_target_skill_id=None,
            coverage_credit=0.0,
            result_status=MatchResultStatus.MISSING.value,
            explanation="No matching student skill found for this requirement",
            candidate_diagnostics=[],
        )

    # Sort candidates by:
    # 1. Priority ascending (1 - EXACT, 2 - ALIAS, 3 - EQUIVALENT, 4 - PARTIAL)
    # 2. Coverage credit descending (strongest contribution wins within priority)
    # 3. Prefer candidates not already fulfilling an exact match on another requirement
    # 4. Deterministic relationship ID ascending
    # 5. Stable skill record ID ascending (deterministic tie-breaker)
    other_exact_skills = (exact_req_skill_ids or set()) - {required_canonical_id}
    candidates.sort(
        key=lambda c: (
            c.priority,
            -c.coverage_credit,
            (
                1
                if (
                    c.priority > 2
                    and c.student_skill.skill_id
                    and str(c.student_skill.skill_id).strip() in other_exact_skills
                )
                else 0
            ),
            (c.relationship.relationship_id if c.relationship else ""),
            str(c.student_skill.skill_record_id),
        )
    )

    winner = candidates[0]
    matched_canonical_id, _ = resolve_student_skill_id(
        winner.student_skill, alias_index
    )

    # Compile diagnostic records for all evaluated candidates
    diagnostics = [
        {
            "student_skill_record_id": str(c.student_skill.skill_record_id),
            "student_skill_name": c.student_skill.standard_name,
            "match_type": c.match_type.value,
            "coverage_credit": c.coverage_credit,
            "is_selected": (c is winner),
            "explanation": c.explanation,
        }
        for c in candidates
    ]

    result_status = (
        MatchResultStatus.MATCHED.value
        if winner.coverage_credit >= 1.0
        else MatchResultStatus.PARTIALLY_COVERED.value
    )

    return MatchingResult(
        industry_requirement_id=req.requirement_id,
        required_canonical_skill_id=req.skill_id,
        required_skill_name=req.standard_name,
        requirement_mapping_status=req.mapping_status,
        selected_student_skill_id=winner.student_skill.skill_record_id,
        matched_canonical_skill_id=matched_canonical_id,
        matched_skill_name=winner.student_skill.standard_name,
        match_type=winner.match_type.value,
        selected_relationship_id=winner.relationship.relationship_id
        if winner.relationship
        else None,
        selected_relationship_type=winner.relationship.relationship_type
        if winner.relationship
        else None,
        relationship_source_skill_id=winner.relationship.source_skill_id
        if winner.relationship
        else None,
        relationship_target_skill_id=winner.relationship.target_skill_id
        if winner.relationship
        else None,
        coverage_credit=winner.coverage_credit,
        result_status=result_status,
        explanation=winner.explanation,
        candidate_diagnostics=diagnostics,
    )


# Pure matching engine evaluating industry requirements against student profile skills
def match_skills(
    requirements: Sequence[RequirementInput],
    student_skills: Sequence[StudentSkillInput],
    aliases: Sequence[AliasInput] = (),
    relationships: Sequence[RelationshipInput] = (),
    policy: MatchingPolicy | None = None,
) -> list[MatchingResult]:
    # Industry requirements are the starting point; student skills must never dictate requirements
    if not requirements:
        return []

    active_policy = policy or MatchingPolicy()
    alias_index = build_alias_index(aliases)
    rel_index = build_relationship_index(relationships)
    exact_req_skill_ids = {
        str(r.skill_id).strip()
        for r in requirements
        if is_requirement_assessable(r)
    }

    # Iterate over every industry requirement to guarantee full demand coverage
    results: list[MatchingResult] = []
    for req in requirements:
        result = match_single_requirement(
            req=req,
            student_skills=student_skills,
            alias_index=alias_index,
            rel_index=rel_index,
            policy=active_policy,
            exact_req_skill_ids=exact_req_skill_ids,
        )
        results.append(result)

    return results
