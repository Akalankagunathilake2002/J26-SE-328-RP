import uuid
from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


# Request payload for initiating a career readiness analysis run
class AnalysisCreateRequest(BaseModel):
    user_skill_profile_id: uuid.UUID | None = Field(
        None,
        validation_alias=AliasChoices("user_skill_profile_id", "userSkillProfileId"),
        description="UUID of the student's UserSkillProfile",
    )
    industry_profile_id: uuid.UUID | None = Field(
        None,
        validation_alias=AliasChoices("industry_profile_id", "industryProfileId"),
        description="UUID of the target IndustryProfile",
    )
    user_id: uuid.UUID | None = Field(
        None,
        validation_alias=AliasChoices("user_id", "userId"),
        description="User UUID used to resolve the latest active student profile",
    )
    role_id: str | None = Field(
        None,
        validation_alias=AliasChoices("role_id", "roleId"),
        description="Canonical or candidate role identifier (e.g., RL-000003)",
    )
    matching_method: str | None = Field(
        None,
        validation_alias=AliasChoices("matching_method", "matchingMethod"),
        description="Optional matching method override; backend automatically controls dual matching",
    )
    scoring_config_version: str = Field(
        "1.0",
        validation_alias=AliasChoices("scoring_config_version", "scoringConfigVersion"),
        description="Configuration version for deterministic scoring reproducibility",
    )
    snapshot_id: uuid.UUID | None = Field(
        None,
        validation_alias=AliasChoices("snapshot_id", "snapshotId"),
        description="Optional SSKS knowledge snapshot UUID; defaults to active snapshot",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # Prevent ambiguous profile selection by requiring explicit student and role targets
    @model_validator(mode="after")
    def validate_profile_selection(self) -> "AnalysisCreateRequest":
        if self.user_skill_profile_id is None and self.user_id is None:
            raise ValueError(
                "Ambiguous profile selection: either 'user_skill_profile_id' or 'user_id' must be specified to select a student profile"
            )
        if self.industry_profile_id is None and self.role_id is None:
            raise ValueError(
                "Ambiguous profile selection: either 'industry_profile_id' or 'role_id' must be specified to select a target industry profile"
            )
        return self


# Item in the C04 prioritySkills list conforming to the agreed external contract
class PrioritySkillOut(BaseModel):
    skillId: str = Field(..., description="Canonical skill identifier from SSKS")
    skillName: str = Field(..., description="Standardized preferred name of the skill")
    priorityRank: int = Field(..., description="1-indexed rank of learning priority")
    learningPriority: float = Field(
        ..., description="Computed priority score = demand_weight * gap"
    )
    gap: float = Field(
        ..., description="Remaining capability gap to achieve required proficiency"
    )

    model_config = ConfigDict(populate_by_name=True)


# Target C04 external JSON response shape matching to-C04 contract
class C04AnalysisResponse(BaseModel):
    analysisId: str = Field(
        ..., description="Unique UUID string of the completed analysis"
    )
    user_id: str = Field(..., description="User UUID string")
    roleId: str = Field(..., description="Target role identifier")
    roleName: str = Field(..., description="Target role title")
    readinessScore: float | None = Field(
        None, description="Overall career readiness score on a 0-100 percentage scale"
    )
    baselineReadinessScore: float | None = Field(
        None, description="Baseline readiness score using exact matching only"
    )
    prioritySkills: list[PrioritySkillOut] = Field(
        default_factory=list,
        description="Ranked list of actionable skill gaps for learning",
    )

    model_config = ConfigDict(populate_by_name=True)


# Per-skill detailed assessment output for diagnostics and audit
class SkillResultDetailOut(BaseModel):
    id: uuid.UUID
    industry_requirement_id: uuid.UUID | None
    required_skill_name: str
    matched_skill_name: str | None
    match_type: str
    relationship_id: str | None
    coverage_credit: float
    required_proficiency: str
    user_proficiency: str | None
    evidence_confidence: float | None
    industry_weight: float | None
    satisfaction: float | None
    gap: float | None
    result_status: str

    model_config = ConfigDict(from_attributes=True)


# Detailed analysis status and persistence record
class AnalysisDetailResponse(BaseModel):
    analysis_id: uuid.UUID
    user_id: uuid.UUID
    user_skill_profile_id: uuid.UUID
    industry_profile_id: uuid.UUID
    snapshot_id: uuid.UUID
    role_id: str | None = None
    role_name: str | None = None
    career_level: str | None = None
    matching_method: str
    scoring_config_version: str
    readiness_score: float | None
    baseline_readiness_score: float | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    skill_results: list[SkillResultDetailOut] = Field(default_factory=list)
    priority_skills: list[PrioritySkillOut] = Field(default_factory=list)
    c04_payload: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


# Summary item returned by analysis history endpoints with canonical fields and legacy aliases
class AnalysisHistoryItem(BaseModel):
    # Core identifiers and profile relationships
    analysis_id: uuid.UUID = Field(
        ..., description="Unique UUID identifier of the analysis"
    )
    analysisId: str = Field(..., description="Legacy alias for analysis_id")
    user_id: uuid.UUID = Field(
        ..., description="User UUID associated with student skill profile"
    )
    user_skill_profile_id: uuid.UUID = Field(
        ..., description="UUID of the student skill profile evaluated"
    )
    industry_profile_id: uuid.UUID = Field(
        ..., description="UUID of the target industry profile evaluated"
    )
    snapshot_id: uuid.UUID | None = Field(
        None, description="Knowledge snapshot UUID used for taxonomy and matching"
    )

    # Target role information
    role_id: str = Field(
        ..., description="Target role identifier (e.g. RL-000003)"
    )
    roleId: str = Field(..., description="Legacy alias for role_id")
    role_name: str | None = Field(
        None, description="Target role title if available"
    )
    roleName: str | None = Field(None, description="Legacy alias for role_name")
    career_level: str | None = Field(
        None, description="Career level of the target role (e.g. ENTRY_LEVEL)"
    )

    # Configuration, scoring results, and lifecycle status
    matching_method: str = Field(
        "RELATIONSHIP_AWARE", description="Matching method used in analysis"
    )
    scoring_config_version: str | None = Field(
        None, description="Scoring configuration version"
    )
    readiness_score: float | None = Field(
        None, description="Overall career readiness score"
    )
    readinessScore: float | None = Field(
        None, description="Legacy alias for readiness_score"
    )
    baseline_readiness_score: float | None = Field(
        None, description="Baseline readiness score using exact matching"
    )
    baselineReadinessScore: float | None = Field(
        None, description="Legacy alias for baseline_readiness_score"
    )
    status: str = Field(
        ..., description="Analysis status: PENDING, RUNNING, COMPLETED, or FAILED"
    )
    started_at: datetime = Field(
        ..., description="Timestamp when analysis was created or started"
    )
    createdAt: datetime = Field(..., description="Legacy alias for started_at")
    completed_at: datetime | None = Field(
        None, description="Timestamp when analysis completed or failed"
    )
    completedAt: datetime | None = Field(
        None, description="Legacy alias for completed_at"
    )

    model_config = ConfigDict(populate_by_name=True)


# Paginated list of analysis history items
class AnalysisHistoryResponse(BaseModel):
    items: list[AnalysisHistoryItem] = Field(
        default_factory=list, description="Paginated analysis history items"
    )
    total: int = Field(..., ge=0, description="Total number of matching analyses")
    limit: int = Field(..., ge=1, description="Page size limit")
    offset: int = Field(..., ge=0, description="Page offset")

    model_config = ConfigDict(populate_by_name=True)


# Candidate discovery execution record for audit and tracking
class CandidateDiscoveryRunOut(BaseModel):
    id: uuid.UUID
    analysis_id: uuid.UUID
    embedding_model: str
    similarity_threshold: float
    status: str
    candidates_submitted_count: int
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
