from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class SkillAlias(Base):
    __tablename__ = "skill_aliases"
    
    alias_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    skill_id: Mapped[str] = mapped_column(String(50), ForeignKey("skills.skill_id", ondelete="CASCADE"), index=True)
    alias_text: Mapped[str] = mapped_column(String(255))
    normalized_alias: Mapped[str] = mapped_column(String(255), index=True)
    source_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("knowledge_sources.source_id", ondelete="SET NULL"), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED")

class RoleAlias(Base):
    __tablename__ = "role_aliases"
    
    alias_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(50), ForeignKey("roles.role_id", ondelete="CASCADE"), index=True)
    alias_text: Mapped[str] = mapped_column(String(255))
    normalized_alias: Mapped[str] = mapped_column(String(255), index=True)
    source_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("knowledge_sources.source_id", ondelete="SET NULL"), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED")
