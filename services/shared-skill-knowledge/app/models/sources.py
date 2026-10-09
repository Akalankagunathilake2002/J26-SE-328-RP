from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    
    source_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_version: Mapped[str] = mapped_column(String(100))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class SkillExternalId(Base):
    __tablename__ = "skill_external_ids"
    
    external_id_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(String(50), ForeignKey("knowledge_sources.source_id", ondelete="CASCADE"))
    external_identifier: Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint("source_id", "external_identifier", name="uq_skill_ext_id_source"),
    )

class RoleExternalId(Base):
    __tablename__ = "role_external_ids"
    
    external_id_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(50), ForeignKey("roles.role_id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(String(50), ForeignKey("knowledge_sources.source_id", ondelete="CASCADE"))
    external_identifier: Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint("source_id", "external_identifier", name="uq_role_ext_id_source"),
    )
