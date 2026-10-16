import pytest
from httpx import AsyncClient


async def seed_knowledge_data(client: AsyncClient):
    # 1. Create Domain
    dom_res = await client.post(
        "/ssks/domains/",
        json={"domain_id": "DOM-TEST-1", "code": "ENG", "name": "Engineering"},
    )
    assert dom_res.status_code == 200

    # 2. Create Active Skills
    s1_res = await client.post(
        "/ssks/skills/",
        json={
            "skill_id": "SK-SNAP-1",
            "preferred_name": "Python Programming",
            "skill_type": "PROGRAMMING_LANGUAGE",
            "skill_nature": "TECHNICAL",
            "status": "ACTIVE",
        },
    )
    assert s1_res.status_code == 200

    s2_res = await client.post(
        "/ssks/skills/",
        json={
            "skill_id": "SK-SNAP-2",
            "preferred_name": "FastAPI Framework",
            "skill_type": "SOFTWARE_OR_TOOL",
            "skill_nature": "TECHNICAL",
            "status": "ACTIVE",
        },
    )
    assert s2_res.status_code == 200

    # 3. Associate Skill with Domain
    sd_res = await client.put("/ssks/skills/SK-SNAP-1/domains/DOM-TEST-1")
    assert sd_res.status_code == 200

    # 4. Create Verified Relationship
    rel_res = await client.post(
        "/ssks/relationships",
        json={
            "relationship_id": "REL-SNAP-1",
            "source_skill_id": "SK-SNAP-2",
            "target_skill_id": "SK-SNAP-1",
            "relationship_type": "PREREQUISITE_OF",
            "evidence_note": "FastAPI is built on Python",
        },
    )
    assert rel_res.status_code == 201

    # 5. Create Candidate Proposal (Must NOT appear in snapshot!)
    cand_rel_res = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-SNAP-1",
            "target_skill_id": "SK-SNAP-2",
            "proposed_relationship_type": "RELATED_TO",
        },
    )
    assert cand_rel_res.status_code == 201

    # 6. Create Candidate Entity (Must NOT appear in snapshot!)
    cand_ent_res = await client.post(
        "/ssks/candidates/entities",
        json={
            "entity_type": "SKILL",
            "submitted_name": "Unapproved Experimental Tech",
            "proposed_skill_type": "SOFTWARE_OR_TOOL",
            "proposed_skill_nature": "TECHNICAL",
        },
    )
    assert cand_ent_res.status_code == 201


@pytest.mark.anyio
async def test_snapshot_export_contents_and_schema(client: AsyncClient):
    await seed_knowledge_data(client)

    # Test default consumer (SkillGap)
    res_def = await client.get("/ssks/snapshots/export")
    assert res_def.status_code == 200
    assert res_def.json()["metadata"]["consumer"] == "SkillGap"
    assert res_def.json()["metadata"]["snapshot_id"].startswith("SNAP-SkillGap-v")

    # Test explicit consumer parameter (SkillGap)
    res = await client.get("/ssks/snapshots/export?consumer=SkillGap")
    assert res.status_code == 200
    data = res.json()

    # Metadata checks
    metadata = data["metadata"]
    assert metadata["consumer"] == "SkillGap"
    assert metadata["status"] == "ACTIVE"
    assert metadata["snapshot_id"].startswith("SNAP-SkillGap-v")
    assert "version" in metadata
    assert "generated_at" in metadata

    # Counts
    counts = metadata["counts"]
    assert counts["skills"] == len(data["skills"])
    assert counts["relationships"] == len(data["relationships"])
    assert counts["domains"] == len(data["domains"])

    # Skills payload
    skill_ids = [s["skill_id"] for s in data["skills"]]
    assert "SK-SNAP-1" in skill_ids
    assert "SK-SNAP-2" in skill_ids

    s1 = next(s for s in data["skills"] if s["skill_id"] == "SK-SNAP-1")
    assert s1["preferred_name"] == "Python Programming"
    assert s1["skill_type"] == "PROGRAMMING_LANGUAGE"
    assert s1["skill_nature"] == "TECHNICAL"
    assert "ENG" in s1["domain_codes"]
    assert "DOM-TEST-1" in s1["domain_ids"]

    # Relationships payload
    rel = data["relationships"][0]
    assert rel["relationship_id"] == "REL-SNAP-1"
    assert rel["source_skill_id"] == "SK-SNAP-2"
    assert rel["target_skill_id"] == "SK-SNAP-1"
    assert rel["relationship_type"] == "PREREQUISITE_OF"
    assert rel["verification_status"] == "VERIFIED"


@pytest.mark.anyio
async def test_snapshot_strict_verified_filtering(client: AsyncClient):
    await seed_knowledge_data(client)

    res = await client.get("/ssks/snapshots/export?consumer=SkillGap")
    assert res.status_code == 200
    data = res.json()

    # 1. Candidate proposals must NOT appear in snapshot
    all_rel_types = [r["relationship_type"] for r in data["relationships"]]
    assert all_rel_types == ["PREREQUISITE_OF"]

    # 2. Candidate entities must NOT appear in snapshot
    all_skill_names = [s["preferred_name"] for s in data["skills"]]
    assert "Unapproved Experimental Tech" not in all_skill_names

    # 3. Only verified relationships included
    assert all(r["verification_status"] == "VERIFIED" for r in data["relationships"])


@pytest.mark.anyio
async def test_snapshot_relationship_directionality_preserved(client: AsyncClient):
    await seed_knowledge_data(client)

    res = await client.get("/ssks/snapshots/export?consumer=SkillGap")
    assert res.status_code == 200
    data = res.json()

    # Direction: SK-SNAP-2 is PREREQUISITE_OF SK-SNAP-1
    forward_rels = [
        r for r in data["relationships"]
        if r["source_skill_id"] == "SK-SNAP-2" and r["target_skill_id"] == "SK-SNAP-1"
    ]
    assert len(forward_rels) == 1

    # Reverse must NOT exist
    reverse_rels = [
        r for r in data["relationships"]
        if r["source_skill_id"] == "SK-SNAP-1" and r["target_skill_id"] == "SK-SNAP-2"
    ]
    assert len(reverse_rels) == 0


@pytest.mark.anyio
async def test_snapshot_metadata_and_validation_endpoints(client: AsyncClient):
    await seed_knowledge_data(client)

    # 1. Metadata endpoint
    meta_res = await client.get("/ssks/snapshots/metadata?consumer=SkillGap")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["consumer"] == "SkillGap"
    assert meta["counts"]["skills"] >= 2
    assert meta["counts"]["relationships"] >= 1
    current_version = meta["version"]

    # 2. Validation with current version
    val_cur_res = await client.get(f"/ssks/snapshots/validate?version={current_version}&consumer=SkillGap")
    assert val_cur_res.status_code == 200
    val_cur = val_cur_res.json()
    assert val_cur["is_current"] is True
    assert val_cur["requested_version"] == current_version
    assert "up to date" in val_cur["message"]

    # 3. Validation with outdated version
    val_out_res = await client.get("/ssks/snapshots/validate?version=v20200101-outdated00&consumer=SkillGap")
    assert val_out_res.status_code == 200
    val_out = val_out_res.json()
    assert val_out["is_current"] is False
    assert val_out["current_version"] == current_version
    assert "outdated" in val_out["message"]


@pytest.mark.anyio
async def test_snapshot_repeatable_and_idempotent_requests(client: AsyncClient):
    await seed_knowledge_data(client)

    # First export via GET
    res1 = await client.get("/ssks/snapshots/export?consumer=SkillGap")
    assert res1.status_code == 200
    v1 = res1.json()["metadata"]["version"]
    snap_id1 = res1.json()["metadata"]["snapshot_id"]

    # Second export via GET without data changes
    res2 = await client.get("/ssks/snapshots/export?consumer=SkillGap")
    assert res2.status_code == 200
    v2 = res2.json()["metadata"]["version"]
    snap_id2 = res2.json()["metadata"]["snapshot_id"]

    # Third export via POST (for Postman/client flexibility)
    res3 = await client.post("/ssks/snapshots/export?consumer=SkillGap")
    assert res3.status_code == 200
    v3 = res3.json()["metadata"]["version"]
    snap_id3 = res3.json()["metadata"]["snapshot_id"]

    # Identical deterministic versions
    assert v1 == v2 == v3
    assert snap_id1 == snap_id2 == snap_id3


@pytest.mark.anyio
async def test_snapshot_custom_consumer_parameter(client: AsyncClient):
    await seed_knowledge_data(client)

    # Custom or legacy consumer identifier (e.g. C03 or another engine)
    res = await client.get("/ssks/snapshots/export?consumer=C03")
    assert res.status_code == 200
    meta = res.json()["metadata"]
    assert meta["consumer"] == "C03"
    assert meta["snapshot_id"].startswith("SNAP-C03-v")
