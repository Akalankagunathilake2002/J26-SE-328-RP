import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KnowledgeSnapshot(Base):
    __tablename__ = "knowledge_snapshots"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    ssks_snapshot_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consumer: Mapped[str] = mapped_column(String(50), default="ReadinessEngine")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    skill_count: Mapped[int] = mapped_column(Integer, default=0)
    alias_count: Mapped[int] = mapped_column(Integer, default=0)
    relationship_count: Mapped[int] = mapped_column(Integer, default=0)
    domain_count: Mapped[int] = mapped_column(Integer, default=0)

    skills: Mapped[list["CachedSkill"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["CachedAlias"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["CachedRelationship"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["CachedSkillEmbedding"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class CachedSkill(Base):
    __tablename__ = "cached_skills"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_snapshots.snapshot_id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    preferred_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_type: Mapped[str] = mapped_column(String(100), nullable=False)
    skill_nature: Mapped[str | None] = mapped_column(String(50), nullable=True)
    domain_codes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    domain_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    snapshot: Mapped["KnowledgeSnapshot"] = relationship(back_populates="skills")
    aliases: Mapped[list["CachedAlias"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan", overlaps="aliases"
    )
    embeddings: Mapped[list["CachedSkillEmbedding"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan", overlaps="embeddings"
    )


class CachedAlias(Base):
    __tablename__ = "cached_aliases"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    alias_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(50), nullable=False)
    alias_text: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Scoped composite foreign key to guarantee alias resolves to skill in the same snapshot
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id"],
            ["knowledge_snapshots.snapshot_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "skill_id"],
            ["cached_skills.snapshot_id", "cached_skills.skill_id"],
            ondelete="CASCADE",
        ),
    )

    snapshot: Mapped["KnowledgeSnapshot"] = relationship(back_populates="aliases", overlaps="aliases")
    skill: Mapped["CachedSkill"] = relationship(back_populates="aliases", overlaps="aliases,snapshot")


class CachedRelationship(Base):
    __tablename__ = "cached_relationships"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    relationship_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_skill_id: Mapped[str] = mapped_column(String(50), nullable=False)
    target_skill_id: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), default="VERIFIED")
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Scoped composite foreign keys to guarantee source and target belong to the same snapshot
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id"],
            ["knowledge_snapshots.snapshot_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "source_skill_id"],
            ["cached_skills.snapshot_id", "cached_skills.skill_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "target_skill_id"],
            ["cached_skills.snapshot_id", "cached_skills.skill_id"],
            ondelete="CASCADE",
        ),
        Index("ix_cached_rel_source", "snapshot_id", "source_skill_id"),
        Index("ix_cached_rel_target", "snapshot_id", "target_skill_id"),
        Index("ix_cached_rel_type", "snapshot_id", "relationship_type"),
    )

    snapshot: Mapped["KnowledgeSnapshot"] = relationship(back_populates="relationships")


class CachedSkillEmbedding(Base):
    __tablename__ = "cached_skill_embeddings"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    embedding_model: Mapped[str] = mapped_column(String(100), primary_key=True)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id"],
            ["knowledge_snapshots.snapshot_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "skill_id"],
            ["cached_skills.snapshot_id", "cached_skills.skill_id"],
            ondelete="CASCADE",
        ),
    )

    snapshot: Mapped["KnowledgeSnapshot"] = relationship(back_populates="embeddings", overlaps="embeddings")
    skill: Mapped["CachedSkill"] = relationship(back_populates="embeddings", overlaps="embeddings,snapshot")
