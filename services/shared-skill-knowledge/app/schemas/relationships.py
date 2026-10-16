from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SkillRelationshipType = Literal[
    "EQUIVALENT_TO",
    "BROADER_THAN",
    "NARROWER_THAN",
    "PART_OF",
    "PREREQUISITE_OF",
    "RELATED_TO",
]

RelationshipVerificationStatus = Literal["VERIFIED", "UNVERIFIED"]
CandidateRelationshipReviewStatus = Literal["PENDING", "APPROVED", "REJECTED"]
CandidateRelationshipReviewAction = Literal["APPROVE", "REJECT", "APPROVED", "REJECTED"]

Id50 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]

class SkillRelationshipBase(BaseModel):
    source_skill_id: Id50
    target_skill_id: Id50
    relationship_type: SkillRelationshipType
    verification_status: RelationshipVerificationStatus = "VERIFIED"
    source_id: Id50 | None = None
    evidence_note: str | None = None

class SkillRelationshipCreate(SkillRelationshipBase):
    relationship_id: Id50 | None = None

class SkillRelationshipUpdate(BaseModel):
    relationship_type: SkillRelationshipType | None = None
    verification_status: RelationshipVerificationStatus | None = None
    source_id: Id50 | None = None
    evidence_note: str | None = None

class SkillRelationshipOut(BaseModel):
    relationship_id: str
    source_skill_id: str
    target_skill_id: str
    relationship_type: SkillRelationshipType
    verification_status: str
    source_id: str | None = None
    evidence_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CandidateRelationshipCreate(BaseModel):
    source_skill_id: Id50
    target_skill_id: Id50
    proposed_relationship_type: SkillRelationshipType
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    source_id: Id50 | None = None
    review_note: str | None = None

class CandidateRelationshipReview(BaseModel):
    action: CandidateRelationshipReviewAction
    review_note: str | None = None

class CandidateRelationshipOut(BaseModel):
    candidate_relationship_id: str
    source_skill_id: str
    target_skill_id: str
    proposed_relationship_type: SkillRelationshipType
    confidence_score: float | None = None
    review_status: CandidateRelationshipReviewStatus
    source_id: str | None = None
    review_note: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class SkillDomainAssociationOut(BaseModel):
    skill_id: str
    domain_id: str

    model_config = ConfigDict(from_attributes=True)

class RoleDomainAssociationOut(BaseModel):
    role_id: str
    domain_id: str

    model_config = ConfigDict(from_attributes=True)
