import pytest
from httpx import AsyncClient

URL = "/api/v1/profile/extract"


@pytest.mark.anyio
async def test_extract_returns_skills_with_confidence(client: AsyncClient):
    cv = b"Skills\nPython, JavaScript\nProjects\nBuilt a web scraper in Python.\n"
    response = await client.post(URL, files={"file": ("cv.txt", cv, "text/plain")})
    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "cv"
    python = next(s for s in body["skills"] if s["name"] == "Python")
    assert python["evidence_types"] == ["cv_self_reported", "project_demonstrated"]
    assert python["confidence_level"] == "weak"  # CV only
    assert 0 < python["confidence"] < 1


@pytest.mark.anyio
async def test_extract_accepts_a_source_type(client: AsyncClient):
    response = await client.post(
        URL, files={"file": ("cert.txt", b"Python for Everybody", "text/plain")},
        data={"source_type": "certificate"},
    )
    assert response.status_code == 200
    assert response.json()["skills"][0]["evidence_types"] == ["certificate_supported"]


@pytest.mark.anyio
async def test_extract_rejects_unsupported_files(client: AsyncClient):
    response = await client.post(URL, files={"file": ("cv.png", b"x", "image/png")})
    assert response.status_code == 422
