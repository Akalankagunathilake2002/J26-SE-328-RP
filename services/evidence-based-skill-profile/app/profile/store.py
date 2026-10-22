"""Saving each user's profile in profile_db, so it is still there after a refresh (TAF task 8)."""
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import create_tables, get_sessionmaker
from app.models.profile import SavedProfile
from app.schemas.profile import SkillProfile

# What a missing or unreachable database raises.
STORE_ERRORS = (SQLAlchemyError, OSError)


class ProfileStore(Protocol):
    async def save(self, user_id: str, profile: SkillProfile) -> datetime: ...

    async def load(self, user_id: str) -> SkillProfile | None: ...

    async def delete(self, user_id: str) -> bool: ...


class DatabaseProfileStore:
    """Keeps one profile per user in the user_profiles table."""

    _tables_ready = False

    async def _ensure_tables(self) -> None:
        # Created on first use, so the service also starts when the database is not up yet.
        if not DatabaseProfileStore._tables_ready:
            await create_tables()
            DatabaseProfileStore._tables_ready = True

    async def save(self, user_id: str, profile: SkillProfile) -> datetime:
        await self._ensure_tables()
        saved_at = datetime.now(UTC)
        data = profile.model_dump(mode="json", exclude={"saved_at"})
        async with get_sessionmaker()() as session:
            row = await session.get(SavedProfile, user_id)
            if row is None:
                session.add(SavedProfile(user_id=user_id, profile=data, updated_at=saved_at))
            else:
                row.profile, row.updated_at = data, saved_at
            await session.commit()
        return saved_at

    async def load(self, user_id: str) -> SkillProfile | None:
        await self._ensure_tables()
        async with get_sessionmaker()() as session:
            row = await session.get(SavedProfile, user_id)
        if row is None:
            return None
        return SkillProfile.model_validate({**row.profile, "saved_at": row.updated_at})

    async def delete(self, user_id: str) -> bool:
        """Remove the user's saved profile; False when there was none."""
        await self._ensure_tables()
        async with get_sessionmaker()() as session:
            row = await session.get(SavedProfile, user_id)
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
        return True


def default_profile_store() -> ProfileStore:
    return DatabaseProfileStore()
