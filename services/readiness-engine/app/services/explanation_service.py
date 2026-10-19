from datetime import UTC, datetime

from app.models.analysis import Analysis, AnalysisPrioritySkill, AnalysisSkillResult
from app.schemas.report import (
    AnalysisReportResponse,
    PriorityExplanationOut,
    ReadinessSummaryOut,
    RelationshipExplanationOut,
    SkillExplanationOut,
)


# Classify readiness score into qualitative tiers and return interpretive narrative
def interpret_readiness_score(score: float | None) -> tuple[str, str]:
    if score is None:
        return (
            "Not Computed",
            "Readiness score is not available for this analysis.",
        )
    if score >= 85.0:
        return (
            "High Readiness",
            f"The candidate demonstrates strong readiness ({score:.1f}%), meeting or exceeding industry proficiency standards across core requirements.",
        )
    if score >= 70.0:
        return (
            "Moderate Readiness",
            f"The candidate demonstrates solid foundational competence ({score:.1f}%), with specific skill gaps remaining for full industry sufficiency.",
        )
    if score >= 50.0:
        return (
            "Developing Readiness",
            f"The candidate demonstrates developing competence ({score:.1f}%), but exhibits notable capability gaps across critical industry requirements.",
        )
    return (
        "Low Readiness",
        f"The candidate demonstrates early-stage competence ({score:.1f}%), with substantial capability gaps across key role requirements requiring targeted learning.",
    )


# Generate deterministic summary breakdown across all evaluated requirements
def build_readiness_summary(
    readiness_score: float | None,
    skill_results: list[AnalysisSkillResult],
    role_name: str,
) -> ReadinessSummaryOut:
    tier, interpretation = interpret_readiness_score(readiness_score)

    total_reqs = len(skill_results)
    unassessed_count = sum(
        1
        for sr in skill_results
        if sr.match_type == "UNASSESSED" or sr.result_status == "UNASSESSED"
    )
    assessable_reqs = total_reqs - unassessed_count

    satisfied_count = sum(
        1
        for sr in skill_results
        if sr.match_type != "UNASSESSED"
        and (
            sr.result_status in ("COVERED", "SATISFIED")
            or (sr.gap is not None and sr.gap <= 1e-6)
        )
    )
    partial_count = sum(
        1
        for sr in skill_results
        if sr.match_type != "UNASSESSED"
        and sr.result_status in ("PARTIALLY_COVERED", "PARTIAL")
        and not (sr.gap is not None and sr.gap <= 1e-6)
    )
    deficient_count = sum(
        1
        for sr in skill_results
        if sr.match_type != "UNASSESSED"
        and sr.result_status == "DEFICIENT"
        and not (sr.gap is not None and sr.gap <= 1e-6)
    )
    missing_count = sum(
        1
        for sr in skill_results
        if sr.match_type != "UNASSESSED"
        and (sr.match_type == "MISSING" or sr.result_status == "MISSING")
    )

    summary_text = (
        f"Evaluated {total_reqs} requirement(s) for role '{role_name}'. "
        f"{satisfied_count} fully satisfied, {partial_count} partial, "
        f"{deficient_count} deficient, and {missing_count} missing. "
        f"{unassessed_count} requirement(s) excluded due to unverified mapping status."
    )

    return ReadinessSummaryOut(
        readinessScore=readiness_score if readiness_score is not None else 0.0,
        tier=tier,
        interpretation=interpretation,
        totalRequirements=total_reqs,
        assessableRequirements=assessable_reqs,
        satisfiedCount=satisfied_count,
        partialCount=partial_count,
        deficientCount=deficient_count,
        missingCount=missing_count,
        unassessedCount=unassessed_count,
        summaryText=summary_text,
    )


# Build deterministic explanation and readiness contribution for a single skill result
def build_skill_explanation(
    sr: AnalysisSkillResult,
    total_assessable_weight: float,
) -> SkillExplanationOut:
    # 1. Compute contribution to 0-100 overall readiness score
    is_unassessed = sr.match_type == "UNASSESSED" or sr.result_status == "UNASSESSED"
    is_satisfied = sr.result_status in ("COVERED", "SATISFIED") or (
        sr.gap is not None and sr.gap <= 1e-6
    )
    weight = sr.industry_weight or 0.0
    satisfaction = sr.satisfaction if sr.satisfaction is not None else 0.0

    if is_unassessed or total_assessable_weight <= 0.0:
        contribution = 0.0
        max_potential = 0.0
        contribution_expl = (
            "Contributed 0.0 points to readiness score because unassessed "
            "requirements are excluded from the scoring denominator."
        )
    else:
        weight_share = (weight / total_assessable_weight) * 100.0
        max_potential = round(weight_share, 2)
        contribution = round(
            (weight * satisfaction / total_assessable_weight) * 100.0, 2
        )

        if is_satisfied:
            contribution_expl = (
                f"Contributed {contribution:.1f} points ({weight_share:.1f}% role weight share) "
                f"with 100% proficiency satisfaction."
            )
        elif satisfaction > 0.0:
            contribution_expl = (
                f"Contributed {contribution:.1f} out of {max_potential:.1f} potential points "
                f"({weight_share:.1f}% role weight share) based on {satisfaction * 100:.0f}% satisfaction."
            )
        else:
            contribution_expl = (
                f"Contributed 0.0 out of {max_potential:.1f} potential points "
                f"({weight_share:.1f}% role weight share) due to zero demonstrated coverage."
            )

    # 2. Build deterministic match and proficiency gap explanation
    req_name = sr.required_skill_name
    req_prof = sr.required_proficiency
    user_prof = sr.user_proficiency
    gap_val = sr.gap if sr.gap is not None else 0.0

    if is_unassessed:
        match_expl = (
            f"Skill requirement '{req_name}' could not be evaluated because its mapping "
            f"status is unresolved. It has been excluded from scoring and learning priorities."
        )
    elif sr.match_type == "MISSING" or sr.result_status == "MISSING":
        match_expl = (
            f"No demonstrated skill found matching required skill '{req_name}' "
            f"(Required: {req_prof}). Leaves a full capability gap of {gap_val:.2f}."
        )
    elif sr.match_type in ("EXACT", "ALIAS"):
        match_prefix = "Verified alias match" if sr.match_type == "ALIAS" else "Direct exact match"
        if is_satisfied:
            match_expl = (
                f"{match_prefix} for '{req_name}'. Demonstrated proficiency "
                f"({user_prof or 'UNSPECIFIED'}) meets or exceeds required proficiency "
                f"({req_prof}) with full coverage credit (1.00)."
            )
        else:
            match_expl = (
                f"{match_prefix} for '{req_name}'. Demonstrated proficiency "
                f"({user_prof or 'None'}) leaves a capability gap of {gap_val:.2f} "
                f"against required proficiency ({req_prof})."
            )
    elif sr.match_type in ("RELATIONSHIP", "EQUIVALENT", "PARTIAL_RELATIONSHIP") or sr.relationship_id:
        rel_id = sr.relationship_id or "VERIFIED_RELATIONSHIP"
        matched_name = sr.matched_skill_name or "Related Skill"
        if is_satisfied:
            match_expl = (
                f"Satisfied via verified semantic relationship '{rel_id}' from demonstrated skill "
                f"'{matched_name}'. Full coverage credit ({sr.coverage_credit:.2f}) achieved "
                f"against required proficiency ({req_prof})."
            )
        else:
            match_expl = (
                f"Matched via verified semantic relationship '{rel_id}' from demonstrated skill "
                f"'{matched_name}' with {sr.coverage_credit * 100:.0f}% coverage credit. "
                f"Demonstrated proficiency ({user_prof or 'None'}) leaves a capability gap of "
                f"{gap_val:.2f} against required proficiency ({req_prof})."
            )
    else:
        match_expl = f"Evaluated skill requirement '{req_name}' with status '{sr.result_status}'."

    return SkillExplanationOut(
        industryRequirementId=(
            str(sr.industry_requirement_id) if sr.industry_requirement_id else None
        ),
        skillName=req_name,
        matchedSkillName=sr.matched_skill_name,
        matchType=sr.match_type,
        relationshipId=sr.relationship_id,
        coverageCredit=sr.coverage_credit,
        requiredProficiency=req_prof,
        userProficiency=user_prof,
        evidenceConfidence=sr.evidence_confidence,
        industryWeight=sr.industry_weight,
        satisfaction=sr.satisfaction,
        gap=sr.gap,
        resultStatus=sr.result_status,
        readinessContribution=contribution,
        maxPotentialContribution=max_potential,
        explanation=match_expl,
        contributionExplanation=contribution_expl,
    )


# Build deterministic learning priority explanation grounded in gap and demand weight
def build_priority_explanation(
    ps: AnalysisPrioritySkill,
    demand_weight_map: dict[str, float],
) -> PriorityExplanationOut:
    demand_weight = demand_weight_map.get(ps.skill_name)
    user_prof_str = ps.user_proficiency if ps.user_proficiency else "None"

    if demand_weight is not None:
        expl = (
            f"Ranked #{ps.priority_rank} learning priority with score {ps.learning_priority_score:.4f}. "
            f"Driven by a capability gap of {ps.gap:.2f} (Required: {ps.required_proficiency}, "
            f"Demonstrated: {user_prof_str}) and an industry demand weight of {demand_weight:.2f}."
        )
    else:
        expl = (
            f"Ranked #{ps.priority_rank} learning priority with score {ps.learning_priority_score:.4f}. "
            f"Driven by a capability gap of {ps.gap:.2f} (Required: {ps.required_proficiency}, "
            f"Demonstrated: {user_prof_str})."
        )

    return PriorityExplanationOut(
        skillId=ps.skill_id,
        skillName=ps.skill_name,
        priorityRank=ps.priority_rank,
        learningPriority=ps.learning_priority_score,
        gap=ps.gap,
        requiredProficiency=ps.required_proficiency,
        userProficiency=ps.user_proficiency,
        demandWeight=demand_weight,
        explanation=expl,
    )


# Generate explanation records for verified relationships that contributed to matching
def build_relationship_explanations(
    skill_results: list[AnalysisSkillResult],
) -> list[RelationshipExplanationOut]:
    relationships = []
    seen_relations: set[str] = set()

    for sr in skill_results:
        if (
            sr.relationship_id
            or sr.match_type in ("RELATIONSHIP", "EQUIVALENT", "PARTIAL_RELATIONSHIP")
        ) and sr.relationship_id:
            rel_key = (
                f"{sr.relationship_id}:{sr.matched_skill_name}:{sr.required_skill_name}"
            )
            if rel_key not in seen_relations:
                seen_relations.add(rel_key)
                expl = (
                    f"Verified semantic relationship '{sr.relationship_id}' mapped demonstrated "
                    f"skill '{sr.matched_skill_name}' to required skill '{sr.required_skill_name}', "
                    f"granting {sr.coverage_credit * 100:.0f}% coverage credit."
                )

                relationships.append(
                    RelationshipExplanationOut(
                        relationshipId=sr.relationship_id,
                        requiredSkillName=sr.required_skill_name,
                        matchedSkillName=sr.matched_skill_name or "Unknown Skill",
                        coverageCredit=sr.coverage_credit,
                        explanation=expl,
                    )
                )

    return relationships


# Orchestrate generation of complete explanation report payload from persisted analysis
def build_analysis_explanation_report(analysis: Analysis) -> AnalysisReportResponse:
    ind_prof = analysis.industry_profile
    role_id_str = (
        (ind_prof.role_id or ind_prof.candidate_role_id or str(ind_prof.id))
        if ind_prof
        else str(analysis.industry_profile_id)
    )
    role_name_str = (
        (
            ind_prof.primary_observed_title
            or ind_prof.role_name
            or "Target Industry Role"
        )
        if ind_prof
        else "Target Industry Role"
    )

    # Calculate total assessable weight for relative readiness contribution
    total_assessable_weight = sum(
        sr.industry_weight or 0.0
        for sr in analysis.skill_results
        if sr.match_type != "UNASSESSED" and sr.result_status != "UNASSESSED"
    )

    # Map skill name to industry demand weight for priority explanation enrichment
    demand_weight_map = {
        sr.required_skill_name: sr.industry_weight
        for sr in analysis.skill_results
        if sr.industry_weight is not None
    }

    # Build readiness summary narrative
    readiness_summary = build_readiness_summary(
        readiness_score=analysis.readiness_score,
        skill_results=analysis.skill_results,
        role_name=role_name_str,
    )

    # Build per-skill explanations ordered by requirement standard name
    skill_explanations = [
        build_skill_explanation(sr, total_assessable_weight)
        for sr in sorted(analysis.skill_results, key=lambda s: s.required_skill_name)
    ]

    # Build priority explanations ordered by sequential rank
    priority_explanations = [
        build_priority_explanation(ps, demand_weight_map)
        for ps in sorted(analysis.priority_skills, key=lambda p: p.priority_rank)
    ]

    # Build relationship explanations
    relationship_explanations = build_relationship_explanations(analysis.skill_results)

    return AnalysisReportResponse(
        analysisId=str(analysis.analysis_id),
        user_id=str(analysis.user_id),
        roleId=role_id_str,
        roleName=role_name_str,
        status=analysis.status,
        startedAt=analysis.started_at,
        completedAt=analysis.completed_at,
        reportVersion="1.0",
        generatedAt=datetime.now(UTC),
        readinessSummary=readiness_summary,
        skillExplanations=skill_explanations,
        priorityExplanations=priority_explanations,
        relationshipExplanations=relationship_explanations,
    )
