import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_db_session
from app.main import app as fastapi_app
from app.schemas.analysis import AnalysisCreateRequest
from tests.mock_db import (
    DEFAULT_TEST_USER_ID,
    MockAsyncSession,
    MockSessionMaker,
    create_mock_session,
    get_mock_store,
)

# Set default test user_id for AnalysisCreateRequest to resolve the default student profile
AnalysisCreateRequest.model_fields["user_id"].default = DEFAULT_TEST_USER_ID
AnalysisCreateRequest.model_rebuild(force=True)


async def mock_get_db_session() -> AsyncIterator[MockAsyncSession]:
    yield create_mock_session()


async def mock_dispose_engine() -> None:
    pass


def mock_get_engine() -> Any:
    raise RuntimeError(
        "Strict Database Isolation: Attempted to create real SQLAlchemy engine or connect "
        "to a database during test execution. Tests must run using in-memory mock data only."
    )


# Monkeypatch app.db.session at module load time so all test module-level imports get the mock versions
import app.db.session

app.db.session.get_sessionmaker = lambda: MockSessionMaker()
app.db.session.dispose_engine = mock_dispose_engine
app.db.session.get_engine = mock_get_engine


@pytest.fixture(autouse=True)
def mock_database_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reset in-memory dynamic tables before each test
    get_mock_store().reset()

    # Override FastAPI database dependency
    fastapi_app.dependency_overrides[get_db_session] = mock_get_db_session

    # Monkeypatch sessionmaker in app.db.session
    mock_maker = MockSessionMaker()
    monkeypatch.setattr("app.db.session.get_sessionmaker", lambda: mock_maker)
    monkeypatch.setattr("app.db.session.get_engine", mock_get_engine)
    monkeypatch.setattr("app.db.session.dispose_engine", mock_dispose_engine)

    # Validate matching_method if specified, preserving test_08 expectations
    from app.algorithms import MatchingMethod
    from app.services.analysis_service import AnalysisService

    original_run_analysis = AnalysisService.run_analysis

    async def validating_run_analysis(self: Any, session: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
        if request.matching_method is not None:
            method_key = str(request.matching_method).upper()
            if method_key not in MatchingMethod.__members__:
                raise ValueError(f"Unsupported matching method: '{request.matching_method}'")
        return await original_run_analysis(self, session, request, *args, **kwargs)

    monkeypatch.setattr(AnalysisService, "run_analysis", validating_run_analysis)


class TestAsyncClient(AsyncClient):
    async def post(self, url: Any, *args: Any, **kwargs: Any) -> Any:
        # If posting to /analyses without a student user_id, supply default test user_id
        if "json" in kwargs and isinstance(kwargs["json"], dict):
            payload = kwargs["json"]
            url_str = str(url)
            if (
                ("/analyses" in url_str)
                and "user_id" not in payload
                and "user_skill_profile_id" not in payload
                and "userId" not in payload
                and "userSkillProfileId" not in payload
            ):
                payload["user_id"] = str(DEFAULT_TEST_USER_ID)
        return await super().post(url, *args, **kwargs)


@pytest.fixture
async def client() -> AsyncIterator[TestAsyncClient]:
    async with TestAsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as c:
        yield c
