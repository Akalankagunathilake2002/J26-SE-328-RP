from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict


class KnowledgeSourceOut(BaseModel):
    source_id: uuid.UUID
    source_code: str
    source_name: str
    source_version: str
    last_synced_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SkillExternalIdOut(BaseModel):
    external_id: uuid.UUID
    skill_id: str
    source_id: uuid.UUID
    external_identifier: str

    model_config = ConfigDict(from_attributes=True)


class RoleExternalIdOut(BaseModel):
    external_id: uuid.UUID
    role_id: str
    source_id: uuid.UUID
    external_identifier: str

    model_config = ConfigDict(from_attributes=True)
