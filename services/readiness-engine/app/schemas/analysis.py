import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Request payload for initiating a career readiness analysis run
class AnalysisCreateRequest(BaseModel):
    user_skill_profile_id: uuid.UUID | None = Field(
        None, description="UUID of the student's UserSkillProfile"
    )
    industry_profile_id: uuid.UUID | None = Field(
        None, description="UUID of the target IndustryProfile"
    )
    user_id: uuid.UUID | None = Field(
        None, description="User UUID used to resolve the latest active student profile"
    )
    role_id: str | None = Field(
        None, description="Canonical or candidate role identifier (e.g., RL-000003)"
    )
    matching_method: str = Field(
        "RELATIONSHIP_AWARE",
        description="Matching method: RELATIONSHIP_AWARE or EXACT_BASELINE",
    )
    scoring_config_version: str = Field(
        "1.0",
        description="Configuration version for deterministic scoring reproducibility",
    )
    snapshot_id: uuid.UUID | None = Field(
        None,
        description="Optional SSKS knowledge snapshot UUID; defaults to active snapshot",
    )

    model_config = ConfigDict(from_attributes=True)


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
