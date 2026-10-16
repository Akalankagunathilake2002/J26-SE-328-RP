import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_check_root(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "readiness-engine"}


@pytest.mark.anyio
async def test_health_check_prefixed(client: AsyncClient):
    response = await client.get("/readiness/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "readiness-engine"}
