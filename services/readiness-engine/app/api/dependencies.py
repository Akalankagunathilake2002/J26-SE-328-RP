from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.db.session import get_session


def get_current_settings() -> Settings:
    return get_settings()


async def get_db_session(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AsyncIterator[AsyncSession]:
    yield session
