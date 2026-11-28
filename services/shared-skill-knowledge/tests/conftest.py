from datetime import datetime, timedelta, timezone
import os
import sys
import tempfile
import uuid
from pathlib import Path

import jwt
import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")
os.environ.setdefault("INTERNAL_SERVICE_KEY", "test-internal-service-key-at-least-32-chars-long")

from app.config.settings import get_settings

get_settings.cache_clear()

import app.models  # noqa: F401,E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"ssks_test_{os.getpid()}.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"

test_engine = create_async_engine(TEST_DB_URL, echo=False)


@sa.event.listens_for(test_engine.sync_engine, "connect")
def _enable_sqlite_fks(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


def make_jwt(
    *,
    role: str | None = "user",
    user_id: uuid.UUID | str | None = None,
    secret: str | None = None,
    issuer: str | None = None,
    audience: str | None = None,
    expires_delta: timedelta = timedelta(minutes=30),
    include_iat: bool = True,
    include_exp: bool = True,
    include_role: bool = True,
    include_sub: bool = True,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict = {}
    if include_sub:
        payload["sub"] = str(user_id or uuid.uuid4())
    if include_role and role is not None:
        payload["role"] = role
    if issuer is not None:
        payload["iss"] = issuer
    if audience is not None:
        payload["aud"] = audience
    if include_iat:
        payload["iat"] = now
    if include_exp:
        payload["exp"] = now + expires_delta
    return jwt.encode(payload, secret or settings.jwt_secret, algorithm=settings.jwt_algorithm)


def auth_headers(role: str, user_id: uuid.UUID | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_jwt(role=role, user_id=user_id)}"}


ADMIN_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
HR_UUID = uuid.UUID("22222222-2222-2222-2222-222222222222")
USER_UUID = uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return auth_headers("admin", ADMIN_UUID)


@pytest.fixture
def hr_headers() -> dict[str, str]:
    return auth_headers("hr", HR_UUID)


@pytest.fixture
def user_headers() -> dict[str, str]:
    return auth_headers("user", USER_UUID)


@pytest.fixture
def service_headers() -> dict[str, str]:
    return {"X-Internal-Service-Key": get_settings().internal_service_key}


@pytest.fixture
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def pytest_sessionfinish(session, exitstatus):
    test_engine.sync_engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass


@pytest.fixture
async def client(setup_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
