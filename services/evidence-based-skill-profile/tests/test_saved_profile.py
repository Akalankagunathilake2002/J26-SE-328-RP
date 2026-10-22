"""Saved profiles (TAF task 8): a built profile is kept for the user and shown again later."""
import pytest
from httpx import AsyncClient

from tests.fakes import MemoryProfileStore

CV_FILE = [("files", ("cv.txt", b"Skills\nPython, Java\n", "text/plain"))]


@pytest.mark.anyio
async def test_a_built_profile_is_saved_and_returned_later(client: AsyncClient):
    built = await client.post("/api/v1/profile/build", files=CV_FILE, data={"user_id": "user-1"})
    assert built.status_code == 200
    assert built.json()["saved_at"] is not None

    saved = await client.get("/api/v1/profile/users/user-1")
    assert saved.status_code == 200
    assert [s["name"] for s in saved.json()["skills"]] == [s["name"] for s in built.json()["skills"]]
    assert saved.json()["saved_at"] is not None


@pytest.mark.anyio
async def test_building_again_replaces_the_saved_profile(client: AsyncClient,
                                                         store: MemoryProfileStore):
    await client.post("/api/v1/profile/build", files=CV_FILE, data={"user_id": "user-1"})
    other = [("files", ("cv.txt", b"Skills\nDocker\n", "text/plain"))]
    await client.post("/api/v1/profile/build", files=other, data={"user_id": "user-1"})

    assert [s.name for s in store.profiles["user-1"].skills] == ["Docker"]


@pytest.mark.anyio
async def test_without_a_user_id_nothing_is_saved(client: AsyncClient, store: MemoryProfileStore):
    built = await client.post("/api/v1/profile/build", files=CV_FILE)
    assert built.json()["saved_at"] is None
    assert store.profiles == {}


@pytest.mark.anyio
async def test_a_user_without_a_saved_profile_gets_404(client: AsyncClient):
    response = await client.get("/api/v1/profile/users/nobody")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_a_database_problem_does_not_lose_the_built_profile(client: AsyncClient,
                                                                  store: MemoryProfileStore):
    store.broken = True
    built = await client.post("/api/v1/profile/build", files=CV_FILE, data={"user_id": "user-1"})
    assert built.status_code == 200
    assert built.json()["skills"] and built.json()["saved_at"] is None

    assert (await client.get("/api/v1/profile/users/user-1")).status_code == 503


@pytest.mark.anyio
async def test_clearing_deletes_the_saved_profile(client: AsyncClient, store: MemoryProfileStore):
    await client.post("/api/v1/profile/build", files=CV_FILE, data={"user_id": "user-1"})

    assert (await client.delete("/api/v1/profile/users/user-1")).status_code == 204
    assert store.profiles == {}
    assert (await client.get("/api/v1/profile/users/user-1")).status_code == 404
    # Clearing again, or a user with nothing saved, is not an error.
    assert (await client.delete("/api/v1/profile/users/user-1")).status_code == 204


@pytest.mark.anyio
async def test_clearing_reports_a_database_problem(client: AsyncClient, store: MemoryProfileStore):
    store.broken = True
    assert (await client.delete("/api/v1/profile/users/user-1")).status_code == 503
