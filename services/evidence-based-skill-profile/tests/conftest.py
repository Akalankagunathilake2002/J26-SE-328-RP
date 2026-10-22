"""Tests for C02 Evidence-Based Student Skill Profile Builder."""
import os

# Tests never load the large GLiNER model; they pass fakes where the AI layer is tested.
os.environ["USE_NEURAL_EXTRACTION"] = "false"
os.environ["EVIDENCE_CLASSIFIER"] = "rules"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


def name_based_detector(data: bytes, name: str):
    """Stand-in for the type detector: "cert" in the file name means a certificate, else a CV."""
    from app.collection.document_type import DetectedType
    from app.schemas.evidence import SourceType

    if "cert" in name.lower():
        return DetectedType(SourceType.CERTIFICATE, 0.9, "meaning")
    return DetectedType(SourceType.CV, 1.0, "structure")


@pytest.fixture
def store():
    from tests.fakes import MemoryProfileStore

    return MemoryProfileStore()


@pytest.fixture
async def client(store):
    from app.profile.builder import default_type_detector
    from app.profile.store import default_profile_store

    app.dependency_overrides[default_type_detector] = lambda: name_based_detector
    app.dependency_overrides[default_profile_store] = lambda: store
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(default_type_detector, None)
    app.dependency_overrides.pop(default_profile_store, None)
