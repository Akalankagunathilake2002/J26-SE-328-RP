import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.cache import KnowledgeSnapshot
    from app.models.profiles import (
        IndustryProfile,
        IndustryProfileRequirement,
        UserSkillProfile,
        UserSkillProfileSkill,
    )


class Analysis(Base):
    __tablename__ = "analyses"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_skill_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_skill_profiles.id"), nullable=False, index=True
    )
    industry_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industry_profiles.id"), nullable=False, index=True
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_snapshots.snapshot_id"),
        nullable=False,
        index=True,
    )
    matching_method: Mapped[str] = mapped_column(String(50), default="RELATIONSHIP_AWARE")
    scoring_config_version: Mapped[str] = mapped_column(String(50), default="1.0")
    readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_skill_profile: Mapped["UserSkillProfile"] = relationship("UserSkillProfile")
    industry_profile: Mapped["IndustryProfile"] = relationship("IndustryProfile")
    snapshot: Mapped["KnowledgeSnapshot"] = relationship("KnowledgeSnapshot")

    skill_results: Mapped[list["AnalysisSkillResult"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    priority_skills: Mapped[list["AnalysisPrioritySkill"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    reports: Mapped[list["AnalysisReport"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    candidate_discovery_runs: Mapped[list["CandidateDiscoveryRun"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class AnalysisSkillResult(Base):
    __tablename__ = "analysis_skill_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    industry_requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("industry_profile_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_skill_profile_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_skill_profile_skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    required_skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_skill_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coverage_credit: Mapped[float] = mapped_column(Float, default=0.0)
    required_proficiency: Mapped[str] = mapped_column(String(50), nullable=False)
    user_proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    industry_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    satisfaction: Mapped[float | None] = mapped_column(Float, nullable=True)
    gap: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_status: Mapped[str] = mapped_column(String(50), nullable=False)

    analysis: Mapped["Analysis"] = relationship(back_populates="skill_results")
    industry_requirement: Mapped["IndustryProfileRequirement | None"] = relationship(
        "IndustryProfileRequirement"
    )
    user_skill_profile_skill: Mapped["UserSkillProfileSkill | None"] = relationship(
        "UserSkillProfileSkill"
    )


class AnalysisPrioritySkill(Base):
    __tablename__ = "analysis_priority_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str] = mapped_column(String(50), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    gap: Mapped[float] = mapped_column(Float, nullable=False)
    required_proficiency: Mapped[str] = mapped_column(String(50), nullable=False)
    user_proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)

    analysis: Mapped["Analysis"] = relationship(back_populates="priority_skills")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_version: Mapped[str] = mapped_column(String(50), default="1.0")
    report_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    generation_method: Mapped[str] = mapped_column(String(50), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(30), default="READY")

    analysis: Mapped["Analysis"] = relationship(back_populates="reports")


class CandidateDiscoveryRun(Base):
    __tablename__ = "candidate_discovery_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED")
    candidates_submitted_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    analysis: Mapped["Analysis"] = relationship(back_populates="candidate_discovery_runs")
