from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from app.schemas.core import SkillType, SkillNature

CandidateEntityType = Literal["SKILL", "ROLE"]
CandidateReviewStatus = Literal["PENDING", "APPROVED", "REJECTED"]
ReviewAction = Literal["APPROVE", "REJECT"]

SubmittedName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]

class CandidateEntityCreate(BaseModel):
    entity_type: CandidateEntityType
    submitted_name: SubmittedName
    description: str | None = None
    proposed_skill_type: SkillType | None = None
    proposed_skill_nature: SkillNature | None = None
    source_component: str | None = None
    source_reference: str | None = None

    @model_validator(mode="after")
    def validate_role_fields(self):
        if self.entity_type == "ROLE":
            if self.proposed_skill_type is not None or self.proposed_skill_nature is not None:
                raise ValueError("Skill-specific fields (proposed_skill_type, proposed_skill_nature) cannot be set for ROLE candidates")
        return self

class CandidateEntityReview(BaseModel):
    action: ReviewAction
    review_note: str | None = None
    skill_type: SkillType | None = None
    skill_nature: SkillNature | None = None

class CandidateEntityOut(BaseModel):
    candidate_entity_id: str
    entity_type: CandidateEntityType
    submitted_name: str
    normalized_name: str
    description: str | None = None
    proposed_skill_type: str | None = None
    proposed_skill_nature: str | None = None
    source_component: str | None = None
    source_reference: str | None = None
    review_status: CandidateReviewStatus
    review_note: str | None = None
    matched_entity_id: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

