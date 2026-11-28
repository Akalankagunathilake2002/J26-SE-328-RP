from datetime import datetime, timezone
import uuid

import pytest
from httpx import AsyncClient

from app.models.sources import KnowledgeSource, RoleExternalId, SkillExternalId
from tests.conftest import ADMIN_UUID, HR_UUID, TestingSessionLocal


async def _seed_core_and_sources():
    source_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        session.add(
            KnowledgeSource(
                source_id=source_id,
                source_code="ESCO",
                source_name="European Skills, Competences, Qualifications and Occupations",
                source_version="1.2.1",
                last_synced_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
    return source_id


@pytest.mark.anyio
async def test_canonical_update_retire_and_duplicate_name_detection(
    client: AsyncClient, admin_headers, user_headers
):
    # Create domain, update, retire
    d_res = await client.post(
        "/ssks/domains/",
        headers=admin_headers,
        json={"code": "DATA", "name": "Data Science"},
    )
    assert d_res.status_code == 201
    dom_id = d_res.json()["domain_id"]

    assert (await client.get(f"/ssks/domains/{dom_id}", headers=user_headers)).status_code == 200
    d_patch = await client.patch(
        f"/ssks/domains/{dom_id}",
        headers=admin_headers,
        json={"name": "Data & Analytics", "description": "Updated"},
    )
    assert d_patch.status_code == 200
    assert d_patch.json()["name"] == "Data & Analytics"

    d_retire = await client.post(f"/ssks/domains/{dom_id}/retire", headers=admin_headers)
    assert d_retire.status_code == 200
    assert d_retire.json()["status"] == "RETIRED"

    # Create skills and verify normalized duplicate detection
    s1 = await client.post(
        "/ssks/skills/",
        headers=admin_headers,
        json={"preferred_name": "PostgreSQL", "skill_type": "SOFTWARE_OR_TOOL"},
    )
    assert s1.status_code == 201
    s1_id = s1.json()["skill_id"]

    dup_s = await client.post(
        "/ssks/skills/",
        headers=admin_headers,
        json={"preferred_name": "  postgresql  ", "skill_type": "SOFTWARE_OR_TOOL"},
    )
    assert dup_s.status_code == 409

    s2 = await client.post(
        "/ssks/skills/",
        headers=admin_headers,
        json={"preferred_name": "MySQL", "skill_type": "SOFTWARE_OR_TOOL"},
    )
    assert s2.status_code == 201
    s2_id = s2.json()["skill_id"]

    # Updating s2 name to collide with s1 returns 409
    assert (
        await client.patch(f"/ssks/skills/{s2_id}", headers=admin_headers, json={"preferred_name": "POSTGRESQL"})
    ).status_code == 409

    # Valid skill update
    s2_upd = await client.patch(
        f"/ssks/skills/{s2_id}",
        headers=admin_headers,
        json={"description": "Relational database", "skill_nature": "TECHNICAL"},
    )
    assert s2_upd.status_code == 200
    assert s2_upd.json()["description"] == "Relational database"

    # Retire s2; normalization must no longer match MySQL
    s2_retire = await client.post(f"/ssks/skills/{s2_id}/retire", headers=admin_headers)
    assert s2_retire.status_code == 200
    assert s2_retire.json()["status"] == "RETIRED"

    norm_res = await client.post(
        "/ssks/normalize/skills",
        headers=user_headers,
        json={"items": ["PostgreSQL", "MySQL"]},
    )
    assert norm_res.status_code == 200
    results = norm_res.json()["results"]
    assert results[0]["status"] == "MATCHED"
    assert results[0]["canonical_id"] == s1_id
    assert results[1]["status"] == "UNMATCHED"

    # Role create, duplicate check, update, retire
    r1 = await client.post("/ssks/roles/", headers=admin_headers, json={"preferred_name": "Data Analyst"})
    assert r1.status_code == 201
    r1_id = r1.json()["role_id"]
    assert (
        await client.post("/ssks/roles/", headers=admin_headers, json={"preferred_name": "data   analyst"})
    ).status_code == 409
    r1_upd = await client.patch(
        f"/ssks/roles/{r1_id}", headers=admin_headers, json={"description": "Analytics role"}
    )
    assert r1_upd.status_code == 200
    assert r1_upd.json()["description"] == "Analytics role"
    r1_ret = await client.post(f"/ssks/roles/{r1_id}/retire", headers=admin_headers)
    assert r1_ret.status_code == 200
    assert r1_ret.json()["status"] == "RETIRED"


@pytest.mark.anyio
async def test_alias_crud_verification_and_normalization(client: AsyncClient, admin_headers, user_headers):
    source_id = await _seed_core_and_sources()
    sk = (
        await client.post(
            "/ssks/skills/",
            headers=admin_headers,
            json={"preferred_name": "Kubernetes", "skill_type": "SOFTWARE_OR_TOOL"},
        )
    ).json()
    rl = (
        await client.post("/ssks/roles/", headers=admin_headers, json={"preferred_name": "Site Reliability Engineer"})
    ).json()
    sk_id, rl_id = sk["skill_id"], rl["role_id"]

    # Create unverified skill alias
    a_res = await client.post(
        f"/ssks/skills/{sk_id}/aliases",
        headers=admin_headers,
        json={"alias_text": "K8s", "source_id": str(source_id), "verification_status": "UNVERIFIED"},
    )
    assert a_res.status_code == 201
    alias = a_res.json()
    alias_id = alias["alias_id"]
    assert alias["normalized_alias"] == "k8s"
    assert alias["verification_status"] == "UNVERIFIED"

    # Unverified alias does not match in normalization
    norm1 = await client.post("/ssks/normalize/skills", headers=user_headers, json={"items": ["K8s"]})
    assert norm1.json()["results"][0]["status"] != "MATCHED"

    # Verify alias -> normalization now matches
    ver_res = await client.patch(
        f"/ssks/aliases/skills/{alias_id}/verify",
        headers=admin_headers,
        json={"verification_status": "VERIFIED"},
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["verification_status"] == "VERIFIED"

    norm2 = await client.post("/ssks/normalize/skills", headers=user_headers, json={"items": ["k8s"]})
    assert norm2.json()["results"][0]["status"] == "MATCHED"
    assert norm2.json()["results"][0]["canonical_id"] == sk_id
    assert norm2.json()["results"][0]["matching_method"] == "VERIFIED_ALIAS"

    # Update alias text and check list/get
    upd_res = await client.patch(
        f"/ssks/aliases/skills/{alias_id}",
        headers=admin_headers,
        json={"alias_text": "Kube"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["normalized_alias"] == "kube"
    assert len((await client.get("/ssks/aliases/skills", headers=user_headers)).json()) == 1
    assert (await client.get(f"/ssks/aliases/skills/{alias_id}", headers=user_headers)).status_code == 200

    # Role alias CRUD & verify
    ra_res = await client.post(
        f"/ssks/roles/{rl_id}/aliases",
        headers=admin_headers,
        json={"alias_text": "SRE", "verification_status": "VERIFIED"},
    )
    assert ra_res.status_code == 201
    ra_id = ra_res.json()["alias_id"]
    assert (await client.get(f"/ssks/roles/{rl_id}/aliases", headers=user_headers)).json()[0]["alias_text"] == "SRE"
    assert (
        await client.patch(
            f"/ssks/aliases/roles/{ra_id}/verify",
            headers=admin_headers,
            json={"verification_status": "UNVERIFIED"},
        )
    ).json()["verification_status"] == "UNVERIFIED"
    assert (await client.get(f"/ssks/aliases/roles/{ra_id}", headers=user_headers)).status_code == 403

    # Delete aliases
    assert (await client.delete(f"/ssks/aliases/skills/{alias_id}", headers=admin_headers)).status_code == 204
    assert (await client.delete(f"/ssks/aliases/roles/{ra_id}", headers=admin_headers)).status_code == 204
    assert (await client.get(f"/ssks/aliases/skills/{alias_id}", headers=admin_headers)).status_code == 404


@pytest.mark.anyio
async def test_candidate_merge_as_alias_for_pending_and_approved_candidates(
    client: AsyncClient, admin_headers, hr_headers, user_headers
):
    sk = (
        await client.post(
            "/ssks/skills/",
            headers=admin_headers,
            json={"preferred_name": "PostgreSQL", "skill_type": "SOFTWARE_OR_TOOL"},
        )
    ).json()
    rl = (
        await client.post("/ssks/roles/", headers=admin_headers, json={"preferred_name": "Software Engineer"})
    ).json()

    # 1. Pending skill candidate merged directly as alias
    c_skill = (
        await client.post(
            "/ssks/candidates/entities",
            headers=hr_headers,
            json={
                "entity_type": "SKILL",
                "submitted_name": "Postgres",
                "proposed_skill_type": "SOFTWARE_OR_TOOL",
            },
        )
    ).json()
    m1 = await client.post(
        f"/ssks/candidates/entities/{c_skill['candidate_entity_id']}/merge-as-alias",
        headers=admin_headers,
        json={"target_entity_id": sk["skill_id"], "review_note": "Postgres is an alias of PostgreSQL"},
    )
    assert m1.status_code == 200
    m1_data = m1.json()
    assert m1_data["target_entity_id"] == sk["skill_id"]
    assert m1_data["candidate"]["review_status"] == "APPROVED"
    assert m1_data["candidate"]["matched_entity_id"] == sk["skill_id"]
    assert m1_data["candidate"]["reviewed_by"] == str(ADMIN_UUID)
    assert m1_data["retired_entity_id"] is None

    norm = await client.post("/ssks/normalize/skills", headers=user_headers, json={"items": ["Postgres"]})
    assert norm.json()["results"][0]["canonical_id"] == sk["skill_id"]

    # 2. Approved role candidate merged into canonical role -> retires redundant role
    c_role = (
        await client.post(
            "/ssks/candidates/entities",
            headers=hr_headers,
            json={"entity_type": "ROLE", "submitted_name": "SWE"},
        )
    ).json()
    approved_role = (
        await client.patch(
            f"/ssks/candidates/entities/{c_role['candidate_entity_id']}/review",
            headers=hr_headers,
            json={"action": "APPROVE"},
        )
    ).json()
    assert approved_role["reviewed_by"] == str(HR_UUID)
    redundant_role_id = approved_role["matched_entity_id"]

    m2 = await client.post(
        f"/ssks/candidates/entities/{c_role['candidate_entity_id']}/merge-as-alias",
        headers=admin_headers,
        json={"target_entity_id": rl["role_id"], "review_note": "Merge SWE into Software Engineer"},
    )
    assert m2.status_code == 200
    m2_data = m2.json()
    assert m2_data["retired_entity_id"] == redundant_role_id
    retired_role = (await client.get(f"/ssks/roles/{redundant_role_id}", headers=user_headers)).json()
    assert retired_role["status"] == "RETIRED"

    # 3. Rejected candidate cannot be merged as alias
    c_rej = (
        await client.post(
            "/ssks/candidates/entities",
            headers=hr_headers,
            json={"entity_type": "ROLE", "submitted_name": "Bogus Role"},
        )
    ).json()
    await client.patch(
        f"/ssks/candidates/entities/{c_rej['candidate_entity_id']}/review",
        headers=hr_headers,
        json={"action": "REJECT"},
    )
    assert (
        await client.post(
            f"/ssks/candidates/entities/{c_rej['candidate_entity_id']}/merge-as-alias",
            headers=admin_headers,
            json={"target_entity_id": rl["role_id"]},
        )
    ).status_code == 409


@pytest.mark.anyio
async def test_sources_external_ids_and_source_existence_validation(
    client: AsyncClient, admin_headers, hr_headers, user_headers
):
    source_id = await _seed_core_and_sources()
    sk = (
        await client.post(
            "/ssks/skills/",
            headers=admin_headers,
            json={"preferred_name": "Python", "skill_type": "PROGRAMMING_LANGUAGE"},
        )
    ).json()
    sk2 = (
        await client.post(
            "/ssks/skills/",
            headers=admin_headers,
            json={"preferred_name": "FastAPI", "skill_type": "SOFTWARE_OR_TOOL"},
        )
    ).json()
    rl = (
        await client.post("/ssks/roles/", headers=admin_headers, json={"preferred_name": "Backend Developer"})
    ).json()

    async with TestingSessionLocal() as session:
        session.add(
            SkillExternalId(
                external_id=uuid.uuid4(),
                skill_id=sk["skill_id"],
                source_id=source_id,
                external_identifier="http://data.europa.eu/esco/skill/python",
            )
        )
        session.add(
            RoleExternalId(
                external_id=uuid.uuid4(),
                role_id=rl["role_id"],
                source_id=source_id,
                external_identifier="http://data.europa.eu/esco/occupation/backend",
            )
        )
        await session.commit()

    sources = await client.get("/ssks/sources", headers=user_headers)
    assert sources.status_code == 200
    assert len(sources.json()) == 1
    assert (await client.get(f"/ssks/sources/{source_id}", headers=user_headers)).json()["source_code"] == "ESCO"
    assert (await client.get(f"/ssks/sources/{uuid.uuid4()}", headers=user_headers)).status_code == 404
    assert (await client.get("/ssks/sources/bad-uuid", headers=user_headers)).status_code == 422

    sk_exts = await client.get(f"/ssks/skills/{sk['skill_id']}/external-ids", headers=user_headers)
    assert sk_exts.status_code == 200
    assert len(sk_exts.json()) == 1
    assert (await client.get("/ssks/external-ids/skills", headers=user_headers)).status_code == 200

    rl_exts = await client.get(f"/ssks/roles/{rl['role_id']}/external-ids", headers=user_headers)
    assert rl_exts.status_code == 200
    assert len(rl_exts.json()) == 1
    assert (await client.get("/ssks/external-ids/roles", headers=user_headers)).status_code == 200

    # Nonexistent source_id returns 404 across relationships, candidate relationships, and aliases
    missing_source = str(uuid.uuid4())
    assert (
        await client.post(
            "/ssks/relationships",
            headers=admin_headers,
            json={
                "source_skill_id": sk2["skill_id"],
                "target_skill_id": sk["skill_id"],
                "relationship_type": "PREREQUISITE_OF",
                "source_id": missing_source,
            },
        )
    ).status_code == 404
    assert (
        await client.post(
            "/ssks/candidates/relationships",
            headers=hr_headers,
            json={
                "source_skill_id": sk2["skill_id"],
                "target_skill_id": sk["skill_id"],
                "proposed_relationship_type": "PREREQUISITE_OF",
                "source_id": missing_source,
            },
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/ssks/skills/{sk['skill_id']}/aliases",
            headers=admin_headers,
            json={"alias_text": "Py", "source_id": missing_source},
        )
    ).status_code == 404


@pytest.mark.anyio
async def test_embeddings_crud_and_validation(client: AsyncClient, admin_headers, service_headers):
    sk = (
        await client.post(
            "/ssks/skills/",
            headers=admin_headers,
            json={"preferred_name": "Docker", "skill_type": "SOFTWARE_OR_TOOL"},
        )
    ).json()
    sk_id = sk["skill_id"]
    vec = [0.01 * (i % 10) for i in range(384)]
    text_hash = "b" * 64

    # Invalid dimension -> 422
    assert (
        await client.put(
            f"/ssks/embeddings/skills/{sk_id}",
            headers=admin_headers,
            json={"embedding_model": "all-MiniLM-L6-v2", "embedding_text_hash": text_hash, "embedding": [0.1] * 10},
        )
    ).status_code == 422

    # Valid upsert
    up = await client.put(
        f"/ssks/embeddings/skills/{sk_id}",
        headers=admin_headers,
        json={"embedding_model": "all-MiniLM-L6-v2", "embedding_text_hash": text_hash, "embedding": vec},
    )
    assert up.status_code == 200
    assert up.json()["embedding_dimension"] == 384
    assert len(up.json()["embedding"]) == 384

    # Summary vs full vector list
    summary_list = await client.get("/ssks/embeddings/skills", headers=service_headers)
    assert summary_list.status_code == 200
    assert "embedding" not in summary_list.json()[0]

    full_list = await client.get("/ssks/embeddings/skills?include_vector=true", headers=service_headers)
    assert full_list.status_code == 200
    assert len(full_list.json()[0]["embedding"]) == 384

    # Delete embedding
    assert (await client.delete(f"/ssks/embeddings/skills/{sk_id}", headers=admin_headers)).status_code == 204
    assert (await client.get(f"/ssks/embeddings/skills/{sk_id}", headers=service_headers)).status_code == 404


@pytest.mark.anyio
async def test_snapshots_endpoints_removed(client: AsyncClient, admin_headers):
    assert (await client.get("/ssks/snapshots/export", headers=admin_headers)).status_code == 404
    assert (await client.post("/ssks/snapshots/export", headers=admin_headers)).status_code == 404
    assert (await client.get("/ssks/snapshots/metadata", headers=admin_headers)).status_code == 404
    assert (await client.get("/ssks/snapshots/validate?version=v1", headers=admin_headers)).status_code == 404
