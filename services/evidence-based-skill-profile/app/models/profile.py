from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedProfile(Base):
    """A user's latest skill profile (TAF task 8); building again replaces it."""

    __tablename__ = "user_profiles"

    # The auth-service ID of the logged-in user.
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # The whole SkillProfile as JSON: skills, evidence, documents and unlinked phrases.
    profile: Mapped[dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
