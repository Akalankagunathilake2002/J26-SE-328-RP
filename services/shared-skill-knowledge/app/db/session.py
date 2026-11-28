from collections.abc import AsyncIterator
from functools import lru_cache
import re

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings

_VALID_SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    connect_args: dict = {}
    if settings.database_url.startswith("postgresql") and settings.db_schema:
        schema = settings.db_schema.strip()
        if not _VALID_SCHEMA_RE.match(schema):
            raise ValueError(f"Invalid DB_SCHEMA value: {schema!r}")
        connect_args["server_settings"] = {"search_path": f"{schema}, public"}

    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    await get_engine().dispose()
