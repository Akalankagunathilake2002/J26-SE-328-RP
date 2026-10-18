import pytest
from httpx import AsyncClient

EXPECTED = {"status": "healthy", "service": "evidence-based-skill-profile"}


@pytest.mark.anyio
async def test_health_check_root(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == EXPECTED


@pytest.mark.anyio
async def test_health_check_prefixed(client: AsyncClient):
    response = await client.get("/api/v1/profile/health")
    assert response.status_code == 200
    assert response.json() == EXPECTED
