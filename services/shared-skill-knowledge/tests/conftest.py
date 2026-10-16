import os
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import app.models.core
import app.models.sources
import app.models.aliases
import app.models.relationships
import app.models.candidates

from app.main import app
from app.db.base import Base
from app.db.session import get_session

TEST_DB_PATH = Path(__file__).parent / "test_temp.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(autouse=True, scope="function")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session", autouse=True)
def cleanup_file():
    yield
    test_engine.sync_engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
