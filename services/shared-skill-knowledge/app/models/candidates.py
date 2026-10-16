from datetime import datetime
from sqlalchemy import String, Text, DateTime, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class CandidateEntity(Base):
    __tablename__ = "candidate_entities"

    candidate_entity_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20))
    submitted_name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_skill_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proposed_skill_nature: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_component: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="PENDING")
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('SKILL', 'ROLE')",
            name="check_valid_candidate_entity_type"
        ),
        CheckConstraint(
            "review_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="check_valid_candidate_review_status"
        ),
        CheckConstraint(
            "proposed_skill_type IN ('PROGRAMMING_LANGUAGE', 'PROGRAMMING_SKILL', 'PROGRAMMING_PARADIGM', 'SOFTWARE_OR_TOOL', 'KNOWLEDGE', 'OTHER_SKILL') OR proposed_skill_type IS NULL",
            name="check_valid_proposed_skill_type"
        ),
        CheckConstraint(
            "proposed_skill_nature IN ('TECHNICAL', 'BEHAVIOURAL', 'OTHER') OR proposed_skill_nature IS NULL",
            name="check_valid_proposed_skill_nature"
        ),
        CheckConstraint(
            "(entity_type = 'SKILL') OR (proposed_skill_type IS NULL AND proposed_skill_nature IS NULL)",
            name="check_candidate_role_no_skill_fields"
        ),
    )
