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
    matching_method: str = Field(
        "RELATIONSHIP_AWARE",
        validation_alias=AliasChoices("matching_method", "matchingMethod"),
        description="Matching method: RELATIONSHIP_AWARE or EXACT_BASELINE",
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
    matching_method: str
    scoring_config_version: str
    readiness_score: float | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    skill_results: list[SkillResultDetailOut] = Field(default_factory=list)
    priority_skills: list[PrioritySkillOut] = Field(default_factory=list)
    c04_payload: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


# Analysis history list item containing lightweight metadata
class AnalysisHistoryItem(BaseModel):
    analysisId: str = Field(..., description="Unique UUID string of the analysis")
    user_id: str = Field(..., description="User UUID string")
    roleId: str = Field(
        ..., description="Role identifier from the target industry profile"
    )
    roleName: str | None = Field(None, description="Role title if available")
    readinessScore: float | None = Field(
        None, description="Overall career readiness score on a 0-100 percentage scale"
    )
    status: str = Field(
        ..., description="Analysis status: PENDING, RUNNING, COMPLETED, or FAILED"
    )
    createdAt: datetime = Field(
        ..., description="Timestamp when analysis was created or started"
    )
    completedAt: datetime | None = Field(
        None, description="Timestamp when analysis completed or failed, if available"
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
