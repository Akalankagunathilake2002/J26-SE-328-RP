"""Tests for C02 Evidence-Based Student Skill Profile Builder."""
import os

# Tests never load the large GLiNER or SetFit models; they pass fakes where the AI layer is tested.
os.environ["USE_NEURAL_EXTRACTION"] = "false"
os.environ["EVIDENCE_CLASSIFIER"] = "rules"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
