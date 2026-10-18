import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserSkillProfile(Base):
    __tablename__ = "user_skill_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # User ID from C02 / shared auth system; not an FK because auth_db is a separate PostgreSQL database
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    profile_version: Mapped[str] = mapped_column(String(100), nullable=False)
    domain_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    domain_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "profile_version", name="uq_user_skill_profile_version"
        ),
    )

    skills: Mapped[list["UserSkillProfileSkill"]] = relationship(
        back_populates="user_skill_profile", cascade="all, delete-orphan"
    )


class UserSkillProfileSkill(Base):
    __tablename__ = "user_skill_profile_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_skill_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_skill_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    candidate_skill_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    standard_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_observed_term: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_terms: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    mapping_status: Mapped[str] = mapped_column(String(50), nullable=False)
    skill_type: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency_level: Mapped[str] = mapped_column(String(50), nullable=False)
    proficiency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED")

    __table_args__ = (
        Index(
            "ix_user_skill_profile_skill_lookup", "user_skill_profile_id", "skill_id"
        ),
    )

    user_skill_profile: Mapped["UserSkillProfile"] = relationship(
        back_populates="skills"
    )
    evidence: Mapped[list["SkillEvidence"]] = relationship(
        back_populates="profile_skill", cascade="all, delete-orphan"
    )


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_skill_profile_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_skill_profile_skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    profile_skill: Mapped["UserSkillProfileSkill"] = relationship(
        back_populates="evidence"
    )


class IndustryProfile(Base):
    __tablename__ = "industry_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    candidate_role_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    role_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_observed_title: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_titles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    mapping_status: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_status: Mapped[str] = mapped_column(String(50), default="active")
    domain_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    domain_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    career_level: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(100), nullable=False)
    job_posting_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observation_period_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    observation_period_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Scoped partial unique indexes ensure uniqueness without merging distinct unresolved candidate roles
    __table_args__ = (
        Index(
            "uq_industry_profile_verified_version",
            "role_id",
            "profile_version",
            unique=True,
            postgresql_where=(role_id.is_not(None)),
        ),
        Index(
            "uq_industry_profile_candidate_version",
            "candidate_role_id",
            "profile_version",
            unique=True,
            postgresql_where=(candidate_role_id.is_not(None)),
        ),
    )

    requirements: Mapped[list["IndustryProfileRequirement"]] = relationship(
        back_populates="industry_profile", cascade="all, delete-orphan"
    )


class IndustryProfileRequirement(Base):
    __tablename__ = "industry_profile_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    industry_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("industry_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    candidate_skill_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    standard_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_observed_term: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_terms: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    mapping_status: Mapped[str] = mapped_column(String(50), nullable=False)
    skill_type: Mapped[str] = mapped_column(String(100), nullable=False)
    required_proficiency_level: Mapped[str] = mapped_column(String(50), nullable=False)
    required_proficiency_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    demand_weight: Mapped[float] = mapped_column(Float, nullable=False)
    demand_frequency: Mapped[float | None] = mapped_column(Float, nullable=True)
    job_ads_containing_skill: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mentioned_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_industry_req_lookup", "industry_profile_id", "skill_id"),
    )

    industry_profile: Mapped["IndustryProfile"] = relationship(
        back_populates="requirements"
    )
    sample_evidence: Mapped[list["IndustrySkillEvidence"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )


class IndustrySkillEvidence(Base):
    __tablename__ = "industry_skill_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("industry_profile_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    requirement: Mapped["IndustryProfileRequirement"] = relationship(
        back_populates="sample_evidence"
    )
