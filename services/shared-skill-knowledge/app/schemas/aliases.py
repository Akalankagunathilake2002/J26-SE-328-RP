from typing import Literal
import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.core import Name255

AliasVerificationStatus = Literal["VERIFIED", "UNVERIFIED"]


class AliasCreate(BaseModel):
    alias_text: Name255
    source_id: uuid.UUID | None = None
    verification_status: AliasVerificationStatus = "UNVERIFIED"


class AliasUpdate(BaseModel):
    alias_text: Name255 | None = None
    source_id: uuid.UUID | None = None
    verification_status: AliasVerificationStatus | None = None


class AliasVerifyRequest(BaseModel):
    verification_status: AliasVerificationStatus


class SkillAliasOut(BaseModel):
    alias_id: uuid.UUID
    skill_id: str
    alias_text: str
    normalized_alias: str
    source_id: uuid.UUID | None = None
    verification_status: AliasVerificationStatus

    model_config = ConfigDict(from_attributes=True)


class RoleAliasOut(BaseModel):
    alias_id: uuid.UUID
    role_id: str
    alias_text: str
    normalized_alias: str
    source_id: uuid.UUID | None = None
    verification_status: AliasVerificationStatus

    model_config = ConfigDict(from_attributes=True)
