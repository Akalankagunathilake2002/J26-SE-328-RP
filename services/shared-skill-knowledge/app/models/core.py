from datetime import datetime
from sqlalchemy import String, Text, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    preferred_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "skill_type IN ('PROGRAMMING_LANGUAGE', 'PROGRAMMING_SKILL', 'PROGRAMMING_PARADIGM', 'SOFTWARE_OR_TOOL', 'KNOWLEDGE', 'OTHER_SKILL')",
            name="check_valid_skill_type"
        ),
    )

class Role(Base):
    __tablename__ = "roles"
    
    role_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    preferred_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Domain(Base):
    __tablename__ = "domains"
    
    domain_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
