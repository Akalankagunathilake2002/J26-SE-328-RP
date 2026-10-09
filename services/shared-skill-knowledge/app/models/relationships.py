from datetime import datetime
from sqlalchemy import String, DateTime, Text, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class SkillDomain(Base):
    __tablename__ = "skill_domains"
    
    skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(50), ForeignKey("domains.domain_id", ondelete="CASCADE"), primary_key=True)

class RoleDomain(Base):
    __tablename__ = "role_domains"
    
    role_id: Mapped[str] = mapped_column(String(50), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(50), ForeignKey("domains.domain_id", ondelete="CASCADE"), primary_key=True)

class SkillRelationship(Base):
    __tablename__ = "skill_relationships"
    
    relationship_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), index=True)
    target_skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(50))
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")
    source_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("knowledge_sources.source_id", ondelete="SET NULL"), nullable=True)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("source_skill_id != target_skill_id", name="check_no_self_reference"),
        CheckConstraint("relationship_type IN ('EQUIVALENT_TO', 'BROADER_THAN', 'NARROWER_THAN', 'PART_OF', 'PREREQUISITE_OF', 'RELATED_TO')", name="check_valid_relationship_type"),
    )

class CandidateSkillRelationship(Base):
    __tablename__ = "candidate_skill_relationships"
    
    candidate_relationship_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), index=True)
    target_skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), index=True)
    proposed_relationship_type: Mapped[str] = mapped_column(String(50))
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="PENDING")
    source_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("knowledge_sources.source_id", ondelete="SET NULL"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("source_skill_id != target_skill_id", name="check_candidate_no_self_reference"),
        CheckConstraint("proposed_relationship_type IN ('EQUIVALENT_TO', 'BROADER_THAN', 'NARROWER_THAN', 'PART_OF', 'PREREQUISITE_OF', 'RELATED_TO')", name="check_valid_candidate_relationship_type"),
        CheckConstraint("review_status IN ('PENDING', 'APPROVED', 'REJECTED')", name="check_valid_review_status"),
    )
