from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

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


async def create_tables(engine: AsyncEngine | None = None) -> None:
    # Registers models on metadata before creating tables
    import app.models  # noqa: F401

    target_engine = engine or get_engine()
    async with target_engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await connection.execute(
                text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            )
        await connection.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    engine = get_engine()
    await engine.dispose()
