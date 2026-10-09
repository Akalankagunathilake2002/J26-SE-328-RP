import pytest
from httpx import AsyncClient, ASGITransport
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_session
from app.models.core import Skill, Domain
from app.models.relationships import SkillRelationship, CandidateSkillRelationship

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
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

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.mark.anyio
async def test_invalid_skill_type(client):
    import sqlalchemy
    try:
        res = await client.post("/ssks/skills/", json={
            "skill_id": "SK-001",
            "preferred_name": "Test",
            "skill_type": "INVALID_TYPE"
        })
        assert False, "Should have thrown IntegrityError"
    except sqlalchemy.exc.IntegrityError:
        pass

@pytest.mark.anyio
async def test_invalid_self_reference():
    async with TestingSessionLocal() as session:
        skill = Skill(skill_id="SK-1", preferred_name="S1", skill_type="KNOWLEDGE")
        session.add(skill)
        await session.commit()

        # Try to add a relationship to itself
        rel = SkillRelationship(
            relationship_id="REL-1",
            source_skill_id="SK-1",
            target_skill_id="SK-1",
            relationship_type="RELATED_TO"
        )
        session.add(rel)
        try:
            await session.commit()
            assert False, "Should have raised IntegrityError for self-reference"
        except sa.exc.IntegrityError:
            pass

@pytest.mark.anyio
async def test_crud_domains(client):
    res = await client.post("/ssks/domains/", json={
        "domain_id": "DOM-1",
        "name": "Information Technology",
        "code": "IT",
        "description": "IT Domain"
    })
    assert res.status_code == 200
    assert res.json()["domain_id"] == "DOM-1"

    res = await client.get("/ssks/domains/")
    assert len(res.json()) == 1
