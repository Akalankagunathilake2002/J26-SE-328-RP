import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-that-is-at-least-32-characters-long")

from app.config.settings import get_settings  # noqa: E402
from app.db.session import get_engine, get_sessionmaker  # noqa: E402
from app.main import create_app  # noqa: E402


def _clear_caches() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    """The auth service backed by a fresh SQLite database file, so no PostgreSQL is needed."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'auth.db'}")
    _clear_caches()
    with TestClient(create_app()) as test_client:
        yield test_client
    _clear_caches()


@pytest.fixture
def registered_user(client) -> dict:
    user = {"full_name": "Nimal Perera", "email": "nimal@example.com", "password": "correct-horse-1"}
    assert client.post("/auth/register", json=user).status_code == 201
    return user
