from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.relationships import SkillRelationshipType


class SnapshotCounts(BaseModel):
    skills: int = 0
    aliases: int = 0
    relationships: int = 0
    domains: int = 0
    external_ids: int = 0
    sources: int = 0


class SnapshotSourceItem(BaseModel):
    source_id: str
    source_code: str
    source_name: str
    source_version: str
    last_synced_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SnapshotMetadata(BaseModel):
    snapshot_id: str
    consumer: str = "SkillGap"
    version: str
    generated_at: datetime
    status: str = "ACTIVE"
    counts: SnapshotCounts
    source_metadata: list[SnapshotSourceItem] = Field(default_factory=list)


class SnapshotSkillItem(BaseModel):
    skill_id: str
    preferred_name: str
    description: str | None = None
    skill_type: str
    skill_nature: str | None = None
    domain_codes: list[str] = Field(default_factory=list)
    domain_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SnapshotAliasItem(BaseModel):
    alias_id: str
    skill_id: str
    alias_text: str
    normalized_alias: str

    model_config = ConfigDict(from_attributes=True)


class SnapshotRelationshipItem(BaseModel):
    relationship_id: str
    source_skill_id: str
    target_skill_id: str
    relationship_type: SkillRelationshipType
    verification_status: str = "VERIFIED"
    evidence_note: str | None = None
    source_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SnapshotExternalIdItem(BaseModel):
    external_id_id: str
    skill_id: str
    source_id: str
    source_code: str | None = None
    external_identifier: str

    model_config = ConfigDict(from_attributes=True)


class SnapshotDomainItem(BaseModel):
    domain_id: str
    code: str
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSnapshotExport(BaseModel):
    metadata: SnapshotMetadata
    skills: list[SnapshotSkillItem]
    aliases: list[SnapshotAliasItem]
    relationships: list[SnapshotRelationshipItem]
    external_ids: list[SnapshotExternalIdItem]
    domains: list[SnapshotDomainItem]
    sources: list[SnapshotSourceItem]


class SnapshotValidationResult(BaseModel):
    consumer: str
    requested_version: str
    current_version: str
    is_current: bool
    generated_at: datetime
    counts: SnapshotCounts
    message: str
