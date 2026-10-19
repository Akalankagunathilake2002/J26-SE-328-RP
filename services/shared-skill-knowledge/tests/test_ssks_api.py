import pytest
import sqlalchemy as sa
from app.models.core import Skill, Domain
from app.models.relationships import SkillDomain, RoleDomain, SkillRelationship, CandidateSkillRelationship
from tests.conftest import TestingSessionLocal

@pytest.mark.anyio
async def test_invalid_skill_type(client):
    res = await client.post("/ssks/skills/", json={
        "skill_id": "SK-001",
        "preferred_name": "Test",
        "skill_type": "INVALID_TYPE"
    })
    assert res.status_code == 422

@pytest.mark.anyio
async def test_invalid_self_reference(setup_db):
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


async def _seed_domains():
    async with TestingSessionLocal() as session:
        session.add_all([
            Domain(domain_id="DOM-IT", name="Information Technology", code="IT"),
            Domain(domain_id="DOM-HR", name="Human Resources", code="HR"),
            Domain(domain_id="DOM-BUS", name="Business", code="BUS"),
        ])
        await session.commit()


def _skill(skill_id="SK-1", **extra):
    return {"skill_id": skill_id, "preferred_name": f"Skill {skill_id}", "skill_type": "KNOWLEDGE", **extra}


@pytest.mark.anyio
async def test_domain_duplicates_and_required_fields(client):
    await _seed_domains()
    before = (await client.get("/ssks/domains/")).json()
    assert [d["domain_id"] for d in before] == ["DOM-BUS", "DOM-HR", "DOM-IT"]

    dup_id = await client.post("/ssks/domains/", json={"domain_id": "DOM-IT", "name": "X", "code": "X1"})
    assert dup_id.status_code == 409
    dup_code = await client.post("/ssks/domains/", json={"domain_id": "DOM-X", "name": "X", "code": "IT"})
    assert dup_code.status_code == 409
    missing = await client.post("/ssks/domains/", json={"domain_id": "DOM-X", "name": "X"})
    assert missing.status_code == 422
    blank = await client.post("/ssks/domains/", json={"domain_id": "DOM-X", "name": "  ", "code": "X"})
    assert blank.status_code == 422

    assert (await client.get("/ssks/domains/")).json() == before


@pytest.mark.anyio
async def test_skill_create_get_and_errors(client):
    res = await client.post("/ssks/skills/", json=_skill("SK-1", skill_nature="TECHNICAL"))
    assert res.status_code == 200
    assert res.json()["skill_nature"] == "TECHNICAL"
    assert res.json()["status"] == "ACTIVE"

    got = await client.get("/ssks/skills/SK-1")
    assert got.status_code == 200
    assert got.json()["skill_id"] == "SK-1"

    assert (await client.get("/ssks/skills/NOPE")).status_code == 404
    assert (await client.post("/ssks/skills/", json=_skill("SK-1"))).status_code == 409
    assert (await client.post("/ssks/skills/", json=_skill("SK-2", skill_nature="BAD"))).status_code == 422
    assert (await client.post("/ssks/skills/", json={"skill_id": "SK-3"})).status_code == 422
    assert (await client.post("/ssks/skills/", json=_skill("SK-4", skill_nature=None))).status_code == 200


@pytest.mark.anyio
@pytest.mark.parametrize("skill_type", [
    "PROGRAMMING_LANGUAGE", "PROGRAMMING_SKILL", "PROGRAMMING_PARADIGM",
    "SOFTWARE_OR_TOOL", "KNOWLEDGE", "OTHER_SKILL",
])
async def test_skill_type_allowed_values(client, skill_type):
    res = await client.post("/ssks/skills/", json=_skill("SK-T", skill_type=skill_type))
    assert res.status_code == 200


@pytest.mark.anyio
async def test_skill_pagination_and_filters(client):
    await _seed_domains()
    await client.post("/ssks/skills/", json=_skill("SK-1", skill_type="KNOWLEDGE", skill_nature="TECHNICAL"))
    await client.post("/ssks/skills/", json=_skill("SK-2", skill_type="PROGRAMMING_LANGUAGE", skill_nature="TECHNICAL"))
    await client.post("/ssks/skills/", json=_skill("SK-3", skill_type="KNOWLEDGE", skill_nature="BEHAVIOURAL", status="INACTIVE"))
    async with TestingSessionLocal() as session:
        session.add(SkillDomain(skill_id="SK-2", domain_id="DOM-IT"))
        await session.commit()

    ids = lambda r: [s["skill_id"] for s in r.json()]
    assert ids(await client.get("/ssks/skills/")) == ["SK-1", "SK-2", "SK-3"]
    assert ids(await client.get("/ssks/skills/?limit=2")) == ["SK-1", "SK-2"]
    assert ids(await client.get("/ssks/skills/?limit=2&offset=2")) == ["SK-3"]
    assert ids(await client.get("/ssks/skills/?status=INACTIVE")) == ["SK-3"]
    assert ids(await client.get("/ssks/skills/?skill_type=KNOWLEDGE")) == ["SK-1", "SK-3"]
    assert ids(await client.get("/ssks/skills/?skill_nature=BEHAVIOURAL")) == ["SK-3"]
    assert ids(await client.get("/ssks/skills/?domain_id=DOM-IT")) == ["SK-2"]
    assert (await client.get("/ssks/skills/?skill_type=BAD")).status_code == 422
    assert (await client.get("/ssks/skills/?limit=0")).status_code == 422
    assert (await client.get("/ssks/skills/?offset=-1")).status_code == 422


@pytest.mark.anyio
async def test_role_crud_pagination_and_filters(client):
    await _seed_domains()
    for rid, status in [("RL-1", "ACTIVE"), ("RL-2", "ACTIVE"), ("RL-3", "INACTIVE")]:
        res = await client.post("/ssks/roles/", json={"role_id": rid, "preferred_name": rid, "status": status})
        assert res.status_code == 200
    async with TestingSessionLocal() as session:
        session.add(RoleDomain(role_id="RL-2", domain_id="DOM-HR"))
        await session.commit()

    ids = lambda r: [x["role_id"] for x in r.json()]
    assert (await client.get("/ssks/roles/RL-1")).json()["role_id"] == "RL-1"
    assert (await client.get("/ssks/roles/NOPE")).status_code == 404
    assert (await client.post("/ssks/roles/", json={"role_id": "RL-1", "preferred_name": "Dup"})).status_code == 409
    assert (await client.post("/ssks/roles/", json={"role_id": "RL-9"})).status_code == 422
    assert ids(await client.get("/ssks/roles/?limit=2&offset=1")) == ["RL-2", "RL-3"]
    assert ids(await client.get("/ssks/roles/?status=INACTIVE")) == ["RL-3"]
    assert ids(await client.get("/ssks/roles/?domain_id=DOM-HR")) == ["RL-2"]


@pytest.mark.anyio
async def test_repository_rolls_back_on_conflict(setup_db):
    from app.repositories.core import SkillRepository, ConflictError
    from app.schemas.core import SkillCreate
    async with TestingSessionLocal() as session:
        repo = SkillRepository(session)
        await repo.create(SkillCreate(**_skill("SK-1")))
        with pytest.raises(ConflictError):
            await repo.create(SkillCreate(**_skill("SK-1")))
        # Session must stay usable after the rollback
        await repo.create(SkillCreate(**_skill("SK-2")))
        assert len(await repo.get_all()) == 2


@pytest.mark.anyio
async def test_auto_generated_ids_and_search(client):
    # Auto-generate domain ID from code if not provided
    res_dom = await client.post("/ssks/domains/", json={
        "name": "Artificial Intelligence",
        "code": "AI",
        "description": "AI and ML Domain"
    })
    assert res_dom.status_code == 200
    dom_data = res_dom.json()
    assert dom_data["domain_id"] == "DOM-AI"

    # Auto-generate skill ID
    res_skill1 = await client.post("/ssks/skills/", json={
        "preferred_name": "Deep Learning",
        "skill_type": "KNOWLEDGE",
        "skill_nature": "TECHNICAL"
    })
    assert res_skill1.status_code == 200
    skill1_data = res_skill1.json()
    assert skill1_data["skill_id"].startswith("SK-")

    res_skill2 = await client.post("/ssks/skills/", json={
        "preferred_name": "Neural Networks",
        "skill_type": "KNOWLEDGE",
        "skill_nature": "TECHNICAL"
    })
    assert res_skill2.status_code == 200
    skill2_data = res_skill2.json()
    assert skill2_data["skill_id"].startswith("SK-")
    assert skill1_data["skill_id"] != skill2_data["skill_id"]

    # Search skills
    search_res = await client.get("/ssks/skills/?search=Neural")
    assert search_res.status_code == 200
    assert any(s["skill_id"] == skill2_data["skill_id"] for s in search_res.json())

    # Auto-generate role ID
    res_role = await client.post("/ssks/roles/", json={
        "preferred_name": "AI Engineer",
        "description": "Designs neural models"
    })
    assert res_role.status_code == 200
    role_data = res_role.json()
    assert role_data["role_id"].startswith("RL-")

    # Search roles
    role_search = await client.get("/ssks/roles/?search=Engineer")
    assert role_search.status_code == 200
    assert any(r["role_id"] == role_data["role_id"] for r in role_search.json())

    # Auto-generate relationship ID
    res_rel = await client.post("/ssks/relationships", json={
        "source_skill_id": skill1_data["skill_id"],
        "target_skill_id": skill2_data["skill_id"],
        "relationship_type": "RELATED_TO"
    })
    assert res_rel.status_code == 201
    rel_data = res_rel.json()
    assert rel_data["relationship_id"].startswith("REL-")

    # Search relationships
    rel_search = await client.get(f"/ssks/relationships?search={rel_data['relationship_id']}")
    assert rel_search.status_code == 200
    assert len(rel_search.json()) == 1
    assert rel_search.json()[0]["relationship_id"] == rel_data["relationship_id"]
