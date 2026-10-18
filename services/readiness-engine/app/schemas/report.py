from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Deterministic explanation and impact metrics for an evaluated skill requirement
class SkillExplanationOut(BaseModel):
    industryRequirementId: str | None = Field(
        None, description="UUID string of target industry requirement"
    )
    skillName: str = Field(..., description="Required skill standard name")
    matchedSkillName: str | None = Field(
        None, description="Student demonstrated skill name if matched"
    )
    matchType: str = Field(
        ...,
        description="Matching category: EXACT, RELATIONSHIP, MISSING, or UNASSESSED",
    )
    relationshipId: str | None = Field(
        None, description="Verified SSKS relationship identifier if relationship match"
    )
    coverageCredit: float = Field(
        ..., description="Capability coverage credit between 0.0 and 1.0"
    )
    requiredProficiency: str = Field(
        ..., description="Target proficiency tier required by industry"
    )
    userProficiency: str | None = Field(
        None, description="Demonstrated proficiency tier from student profile"
    )
    evidenceConfidence: float | None = Field(
        None, description="Confidence score of student skill evidence (0.0 to 1.0)"
    )
    industryWeight: float | None = Field(
        None, description="Demand weight assigned to the industry requirement"
    )
    satisfaction: float | None = Field(
        None, description="Proficiency satisfaction ratio (0.0 to 1.0)"
    )
    gap: float | None = Field(None, description="Remaining capability gap (0.0 to 1.0)")
    resultStatus: str = Field(
        ...,
        description="Assessment status: SATISFIED, PARTIAL, DEFICIENT, MISSING, or UNASSESSED",
    )
    readinessContribution: float | None = Field(
        None,
        description="Absolute score points contributed by this skill to overall readiness",
    )
    maxPotentialContribution: float | None = Field(
        None,
        description="Maximum potential score points this requirement could contribute",
    )
    explanation: str = Field(
        ..., description="Deterministic human-readable explanation of match and gap"
    )
    contributionExplanation: str = Field(
        ..., description="Deterministic explanation of readiness contribution"
    )

    model_config = ConfigDict(populate_by_name=True)


# Deterministic rationale for a ranked learning priority recommendation
class PriorityExplanationOut(BaseModel):
    skillId: str = Field(
        ..., description="Canonical skill identifier from SSKS (e.g., SK-000088)"
    )
    skillName: str = Field(..., description="Standardized preferred skill name")
    priorityRank: int = Field(..., description="1-indexed rank of learning priority")
    learningPriority: float = Field(
        ..., description="Computed priority score = demand_weight * gap"
    )
    gap: float = Field(
        ..., description="Remaining capability gap to achieve required proficiency"
    )
    requiredProficiency: str = Field(..., description="Required proficiency tier")
    userProficiency: str | None = Field(
        None, description="Demonstrated proficiency tier if present"
    )
    demandWeight: float | None = Field(
        None, description="Industry demand weight of the requirement"
    )
    explanation: str = Field(
        ..., description="Deterministic explanation for learning priority ranking"
    )

    model_config = ConfigDict(populate_by_name=True)


# Explanation of a verified semantic relationship used during matching
class RelationshipExplanationOut(BaseModel):
    relationshipId: str = Field(
        ..., description="Verified SSKS relationship identifier"
    )
    requiredSkillName: str = Field(
        ..., description="Target required industry skill name"
    )
    matchedSkillName: str = Field(
        ..., description="Demonstrated student skill name providing coverage"
    )
    coverageCredit: float = Field(
        ..., description="Coverage credit granted by the verified relationship"
    )
    explanation: str = Field(
        ..., description="Deterministic explanation of verified relationship match"
    )

    model_config = ConfigDict(populate_by_name=True)


# Qualitative summary and requirement breakdown of the overall readiness score
class ReadinessSummaryOut(BaseModel):
    readinessScore: float = Field(
        ..., description="Overall career readiness score on a 0-100 percentage scale"
    )
    tier: str = Field(
        ...,
        description="Qualitative tier: High Readiness, Moderate Readiness, Developing Readiness, or Low Readiness",
    )
    interpretation: str = Field(
        ..., description="Deterministic interpretation of the overall score"
    )
    totalRequirements: int = Field(
        ..., description="Total industry requirements evaluated"
    )
    assessableRequirements: int = Field(
        ..., description="Assessable requirements included in readiness scoring"
    )
    satisfiedCount: int = Field(
        ..., description="Number of requirements fully satisfied"
    )
    partialCount: int = Field(
        ..., description="Number of requirements partially satisfied"
    )
    deficientCount: int = Field(
        ..., description="Number of requirements with deficient satisfaction"
    )
    missingCount: int = Field(
        ..., description="Number of requirements with no demonstrated skills"
    )
    unassessedCount: int = Field(
        ..., description="Number of requirements excluded due to unresolved mapping"
    )
    summaryText: str = Field(
        ..., description="Comprehensive deterministic summary narrative"
    )

    model_config = ConfigDict(populate_by_name=True)


# Complete explanation report response payload for C04 and diagnostic consumers
class AnalysisReportResponse(BaseModel):
    analysisId: str = Field(
        ..., description="Unique UUID string of the completed analysis"
    )
    user_id: str = Field(..., description="User UUID string")
    roleId: str = Field(..., description="Target industry role identifier")
    roleName: str = Field(..., description="Target industry role title")
    status: str = Field(..., description="Analysis lifecycle status (COMPLETED)")
    startedAt: datetime = Field(
        ..., description="Timestamp when analysis was created or started"
    )
    completedAt: datetime | None = Field(
        None, description="Timestamp when analysis finished"
    )
    reportVersion: str = Field(
        "1.0", description="Version of the explanation report schema"
    )
    generatedAt: datetime = Field(
        ..., description="Timestamp when explanation report was generated"
    )
    readinessSummary: ReadinessSummaryOut = Field(
        ..., description="Overall readiness evaluation and qualitative summary"
    )
    skillExplanations: list[SkillExplanationOut] = Field(
        default_factory=list,
        description="Per-skill match, gap, and contribution explanations",
    )
    priorityExplanations: list[PriorityExplanationOut] = Field(
        default_factory=list,
        description="Ranked learning priority explanations",
    )
    relationshipExplanations: list[RelationshipExplanationOut] = Field(
        default_factory=list,
        description="Verified skill relationship explanations",
    )

    model_config = ConfigDict(populate_by_name=True)
