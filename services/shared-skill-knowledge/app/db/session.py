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
    from sqlalchemy import text
    import app.models.core
    import app.models.sources
    import app.models.aliases
    import app.models.relationships
    import app.models.candidates

    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if connection.dialect.name == "postgresql":
            statements = [
                "ALTER TABLE candidate_skill_relationships ADD COLUMN IF NOT EXISTS evidence_description TEXT;",
                "ALTER TABLE candidate_skill_relationships ADD COLUMN IF NOT EXISTS evidence_url VARCHAR(500);",
                "ALTER TABLE candidate_skill_relationships ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);",
                "ALTER TABLE candidate_skill_relationships ADD COLUMN IF NOT EXISTS canonical_relationship_id VARCHAR(50);",
                "ALTER TABLE skill_relationships ADD COLUMN IF NOT EXISTS evidence_description TEXT;",
                "ALTER TABLE skill_relationships ADD COLUMN IF NOT EXISTS evidence_url VARCHAR(500);",
                "ALTER TABLE skill_relationships ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);",
            ]
            for stmt in statements:
                try:
                    await connection.execute(text(stmt))
                except Exception:
                    pass

async def dispose_engine() -> None:
    await get_engine().dispose()
