from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from app.db.base import Base

@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)

@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)

async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session

async def create_tables() -> None:
    import app.models.core
    import app.models.sources
    import app.models.aliases
    import app.models.relationships

    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

async def dispose_engine() -> None:
    await get_engine().dispose()
