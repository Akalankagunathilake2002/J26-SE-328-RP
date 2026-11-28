import uuid
import pytest
from httpx import AsyncClient

from tests.conftest import ADMIN_UUID, HR_UUID


async def create_test_skill(client: AsyncClient, admin_headers: dict, skill_id: str, name: str):
    res = await client.post(
        "/ssks/skills/",
        headers=admin_headers,
        json={
            "skill_id": skill_id,
            "preferred_name": name,
            "skill_type": "PROGRAMMING_LANGUAGE",
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 201
    return res.json()


async def create_test_role(client: AsyncClient, admin_headers: dict, role_id: str, name: str):
    res = await client.post(
        "/ssks/roles/",
        headers=admin_headers,
        json={
            "role_id": role_id,
            "preferred_name": name,
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 201
    return res.json()


async def create_test_domain(client: AsyncClient, admin_headers: dict, domain_id: str, code: str, name: str):
    res = await client.post(
        "/ssks/domains/",
        headers=admin_headers,
        json={
            "domain_id": domain_id,
            "code": code,
            "name": name,
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 201
    return res.json()


@pytest.mark.anyio
async def test_canonical_relationship_creation_and_validations(client: AsyncClient, admin_headers):
    await create_test_skill(client, admin_headers, "SK-101", "Python")
    await create_test_skill(client, admin_headers, "SK-102", "Django")

    res = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-102",
            "target_skill_id": "SK-101",
            "relationship_type": "PREREQUISITE_OF",
            "evidence_note": "Django requires Python",
            "evidence_description": "Official Django docs require Python 3",
            "evidence_url": "https://docs.djangoproject.com/",
        },
    )
    assert res.status_code == 201
    data = res.json()
    uuid.UUID(data["relationship_id"])
    assert data["source_skill_id"] == "SK-102"
    assert data["target_skill_id"] == "SK-101"
    assert data["relationship_type"] == "PREREQUISITE_OF"
    assert data["verification_status"] == "VERIFIED"
    assert data["evidence_note"] == "Django requires Python"
    assert data["evidence_description"] == "Official Django docs require Python 3"
    assert data["evidence_url"] == "https://docs.djangoproject.com/"
    assert data["reviewed_by"] == str(ADMIN_UUID)

    res_self = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-101",
            "target_skill_id": "SK-101",
            "relationship_type": "EQUIVALENT_TO",
        },
    )
    assert res_self.status_code == 422
    assert "different" in res_self.json()["detail"].lower()

    res_no_src = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-999999",
            "target_skill_id": "SK-101",
            "relationship_type": "RELATED_TO",
        },
    )
    assert res_no_src.status_code == 404

    res_invalid_type = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-101",
            "target_skill_id": "SK-102",
            "relationship_type": "INVALID_TYPE",
        },
    )
    assert res_invalid_type.status_code == 422

    res_dup = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-102",
            "target_skill_id": "SK-101",
            "relationship_type": "PREREQUISITE_OF",
        },
    )
    assert res_dup.status_code == 409


@pytest.mark.anyio
async def test_canonical_relationship_listing_filtering_pagination(
    client: AsyncClient, admin_headers, user_headers
):
    await create_test_skill(client, admin_headers, "SK-201", "JavaScript")
    await create_test_skill(client, admin_headers, "SK-202", "TypeScript")
    await create_test_skill(client, admin_headers, "SK-203", "React")

    await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-202",
            "target_skill_id": "SK-201",
            "relationship_type": "BROADER_THAN",
        },
    )
    await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-203",
            "target_skill_id": "SK-201",
            "relationship_type": "RELATED_TO",
        },
    )

    res = await client.get("/ssks/relationships", headers=user_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 2

    res_src = await client.get("/ssks/relationships?source_skill_id=SK-202", headers=user_headers)
    assert res_src.status_code == 200
    items = res_src.json()
    assert len(items) == 1
    assert items[0]["source_skill_id"] == "SK-202"

    res_type = await client.get("/ssks/relationships?relationship_type=RELATED_TO", headers=user_headers)
    assert res_type.status_code == 200
    items_type = res_type.json()
    assert len(items_type) >= 1
    assert all(r["relationship_type"] == "RELATED_TO" for r in items_type)


@pytest.mark.anyio
async def test_canonical_relationship_get_update_delete(client: AsyncClient, admin_headers, user_headers):
    await create_test_skill(client, admin_headers, "SK-301", "C")
    await create_test_skill(client, admin_headers, "SK-302", "C++")

    custom_uuid = str(uuid.uuid4())
    create_res = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "relationship_id": custom_uuid,
            "source_skill_id": "SK-302",
            "target_skill_id": "SK-301",
            "relationship_type": "RELATED_TO",
            "evidence_note": "Initial note",
        },
    )
    assert create_res.status_code == 201
    rel_id = create_res.json()["relationship_id"]
    assert rel_id == custom_uuid

    get_res = await client.get(f"/ssks/relationships/{rel_id}", headers=user_headers)
    assert get_res.status_code == 200
    assert get_res.json()["evidence_note"] == "Initial note"

    assert (await client.get(f"/ssks/relationships/{uuid.uuid4()}", headers=user_headers)).status_code == 404
    assert (await client.get("/ssks/relationships/not-a-uuid", headers=user_headers)).status_code == 422

    patch_res = await client.patch(
        f"/ssks/relationships/{rel_id}",
        headers=admin_headers,
        json={
            "relationship_type": "BROADER_THAN",
            "evidence_note": "Updated note",
            "evidence_description": "Updated evidence description",
            "evidence_url": "https://isocpp.org/",
        },
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["relationship_type"] == "BROADER_THAN"
    assert patch_res.json()["evidence_note"] == "Updated note"
    assert patch_res.json()["evidence_description"] == "Updated evidence description"
    assert patch_res.json()["evidence_url"] == "https://isocpp.org/"

    del_res = await client.delete(f"/ssks/relationships/{rel_id}", headers=admin_headers)
    assert del_res.status_code == 204

    assert (await client.get(f"/ssks/relationships/{rel_id}", headers=user_headers)).status_code == 404
    assert (await client.delete(f"/ssks/relationships/{rel_id}", headers=admin_headers)).status_code == 404


@pytest.mark.anyio
async def test_candidate_relationship_submission_and_validation(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-401", "Go")
    await create_test_skill(client, admin_headers, "SK-402", "Docker")

    res = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-402",
            "target_skill_id": "SK-401",
            "proposed_relationship_type": "RELATED_TO",
            "confidence_score": 0.85,
            "review_note": "Proposed by automated extractor",
            "evidence_description": "Docker is written in Go",
            "evidence_url": "https://github.com/moby/moby",
        },
    )
    assert res.status_code == 201
    cand = res.json()
    uuid.UUID(cand["candidate_relationship_id"])
    assert cand["review_status"] == "PENDING"
    assert cand["confidence_score"] == 0.85
    assert cand["evidence_description"] == "Docker is written in Go"
    assert cand["evidence_url"] == "https://github.com/moby/moby"

    res_self = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-401",
            "target_skill_id": "SK-401",
            "proposed_relationship_type": "EQUIVALENT_TO",
        },
    )
    assert res_self.status_code == 422

    res_conf = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-401",
            "target_skill_id": "SK-402",
            "proposed_relationship_type": "RELATED_TO",
            "confidence_score": 1.5,
        },
    )
    assert res_conf.status_code == 422

    res_dup = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-402",
            "target_skill_id": "SK-401",
            "proposed_relationship_type": "RELATED_TO",
        },
    )
    assert res_dup.status_code == 409
    assert "pending candidate relationship already exists" in res_dup.json()["detail"]


@pytest.mark.anyio
async def test_candidate_relationship_review_workflow(
    client: AsyncClient, admin_headers, hr_headers, user_headers
):
    await create_test_skill(client, admin_headers, "SK-501", "HTML")
    await create_test_skill(client, admin_headers, "SK-502", "CSS")
    await create_test_skill(client, admin_headers, "SK-503", "Sass")

    c1_res = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-503",
            "target_skill_id": "SK-502",
            "proposed_relationship_type": "PREREQUISITE_OF",
        },
    )
    c1_id = c1_res.json()["candidate_relationship_id"]

    res_no_auth = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        json={"action": "APPROVED"},
    )
    assert res_no_auth.status_code == 401

    res_user = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        headers=user_headers,
        json={"action": "APPROVED"},
    )
    assert res_user.status_code == 403

    approve_res = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        headers=hr_headers,
        json={"action": "APPROVED", "review_note": "Verified by HR reviewer"},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["review_status"] == "APPROVED"
    assert approve_res.json()["reviewed_at"] is not None
    assert approve_res.json()["reviewed_by"] == str(HR_UUID)

    rel_res = await client.get(
        "/ssks/relationships?source_skill_id=SK-503&target_skill_id=SK-502",
        headers=user_headers,
    )
    assert rel_res.status_code == 200
    rels = rel_res.json()
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "PREREQUISITE_OF"
    assert rels[0]["verification_status"] == "VERIFIED"
    assert rels[0]["reviewed_by"] == str(HR_UUID)

    already_rev = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        headers=hr_headers,
        json={"action": "REJECTED"},
    )
    assert already_rev.status_code == 409

    c2_res = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-501",
            "target_skill_id": "SK-503",
            "proposed_relationship_type": "BROADER_THAN",
        },
    )
    c2_id = c2_res.json()["candidate_relationship_id"]

    reject_res = await client.patch(
        f"/ssks/candidates/relationships/{c2_id}/review",
        headers=hr_headers,
        json={"action": "REJECTED", "review_note": "Not broader than Sass"},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["review_status"] == "REJECTED"

    rel_check = await client.get(
        "/ssks/relationships?source_skill_id=SK-501&target_skill_id=SK-503",
        headers=user_headers,
    )
    assert rel_check.status_code == 200
    assert len(rel_check.json()) == 0


@pytest.mark.anyio
async def test_skill_and_role_domain_associations(client: AsyncClient, admin_headers, user_headers):
    await create_test_domain(client, admin_headers, "DOM-10", "CLOUD", "Cloud Computing")
    await create_test_skill(client, admin_headers, "SK-601", "Kubernetes")
    await create_test_role(client, admin_headers, "RL-601", "Cloud Architect")

    assert (await client.get("/ssks/skills/SK-601/domains", headers=user_headers)).json() == []

    res_s_put = await client.put("/ssks/skills/SK-601/domains/DOM-10", headers=admin_headers)
    assert res_s_put.status_code == 200
    assert res_s_put.json() == {"skill_id": "SK-601", "domain_id": "DOM-10"}

    assert (await client.put("/ssks/skills/SK-601/domains/DOM-10", headers=admin_headers)).status_code == 200

    res_s_list = await client.get("/ssks/skills/SK-601/domains", headers=user_headers)
    assert res_s_list.status_code == 200
    assert len(res_s_list.json()) == 1
    assert res_s_list.json()[0]["domain_id"] == "DOM-10"

    assert (await client.delete("/ssks/skills/SK-601/domains/DOM-10", headers=admin_headers)).status_code == 204
    assert (await client.get("/ssks/skills/SK-601/domains", headers=user_headers)).json() == []
    assert (await client.delete("/ssks/skills/SK-601/domains/DOM-10", headers=admin_headers)).status_code == 404

    assert (await client.put("/ssks/skills/SK-NONEXISTENT/domains/DOM-10", headers=admin_headers)).status_code == 404
    assert (await client.put("/ssks/skills/SK-601/domains/DOM-NONEXISTENT", headers=admin_headers)).status_code == 404

    assert (await client.get("/ssks/roles/RL-601/domains", headers=user_headers)).json() == []
    res_r_put = await client.put("/ssks/roles/RL-601/domains/DOM-10", headers=admin_headers)
    assert res_r_put.status_code == 200
    assert res_r_put.json() == {"role_id": "RL-601", "domain_id": "DOM-10"}
    assert (await client.put("/ssks/roles/RL-601/domains/DOM-10", headers=admin_headers)).status_code == 200

    res_r_list = await client.get("/ssks/roles/RL-601/domains", headers=user_headers)
    assert len(res_r_list.json()) == 1
    assert res_r_list.json()[0]["code"] == "CLOUD"

    assert (await client.delete("/ssks/roles/RL-601/domains/DOM-10", headers=admin_headers)).status_code == 204
    assert (await client.get("/ssks/roles/RL-601/domains", headers=user_headers)).json() == []
    assert (await client.delete("/ssks/roles/RL-601/domains/DOM-10", headers=admin_headers)).status_code == 404

    assert (await client.put("/ssks/roles/RL-NONEXISTENT/domains/DOM-10", headers=admin_headers)).status_code == 404
    assert (await client.put("/ssks/roles/RL-601/domains/DOM-NONEXISTENT", headers=admin_headers)).status_code == 404


@pytest.mark.anyio
async def test_openapi_schema_contains_all_endpoints_and_no_snapshots(client: AsyncClient):
    res = await client.get("/ssks/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]

    expected_endpoints = [
        "/ssks/relationships",
        "/ssks/relationships/{relationship_id}",
        "/ssks/candidates/relationships",
        "/ssks/candidates/relationships/{candidate_relationship_id}",
        "/ssks/candidates/relationships/{candidate_relationship_id}/review",
        "/ssks/skills/{skill_id}/domains",
        "/ssks/skills/{skill_id}/domains/{domain_id}",
        "/ssks/roles/{role_id}/domains",
        "/ssks/roles/{role_id}/domains/{domain_id}",
        "/ssks/skills/{skill_id}/aliases",
        "/ssks/roles/{role_id}/aliases",
        "/ssks/aliases/skills",
        "/ssks/aliases/roles",
        "/ssks/sources",
        "/ssks/embeddings/skills",
    ]
    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Expected endpoint {endpoint} not found in OpenAPI paths"

    assert not any("snapshot" in p for p in paths), "Snapshot endpoints must be completely removed"


@pytest.mark.anyio
async def test_directionality_not_reversed_automatically(client: AsyncClient, admin_headers, user_headers):
    await create_test_skill(client, admin_headers, "SK-701", "Math")
    await create_test_skill(client, admin_headers, "SK-702", "Calculus")

    res = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-702",
            "target_skill_id": "SK-701",
            "relationship_type": "PART_OF",
        },
    )
    assert res.status_code == 201

    res_reverse = await client.get("/ssks/relationships?source_skill_id=SK-701", headers=user_headers)
    assert res_reverse.status_code == 200
    assert len(res_reverse.json()) == 0

    res_forward = await client.get("/ssks/relationships?source_skill_id=SK-702", headers=user_headers)
    assert res_forward.status_code == 200
    assert len(res_forward.json()) == 1
    assert res_forward.json()[0]["target_skill_id"] == "SK-701"


@pytest.mark.anyio
async def test_candidate_approval_rollback_on_canonical_conflict(
    client: AsyncClient, admin_headers, hr_headers
):
    await create_test_skill(client, admin_headers, "SK-801", "Kotlin")
    await create_test_skill(client, admin_headers, "SK-802", "Java")

    cand_res = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
        json={
            "source_skill_id": "SK-801",
            "target_skill_id": "SK-802",
            "proposed_relationship_type": "RELATED_TO",
        },
    )
    assert cand_res.status_code == 201
    cand_id = cand_res.json()["candidate_relationship_id"]

    rel_res = await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={
            "source_skill_id": "SK-801",
            "target_skill_id": "SK-802",
            "relationship_type": "RELATED_TO",
        },
    )
    assert rel_res.status_code == 201

    approve_res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        headers=hr_headers,
        json={"action": "APPROVED"},
    )
    assert approve_res.status_code == 409
    assert "already exists" in approve_res.json()["detail"].lower()

    get_cand = await client.get(f"/ssks/candidates/relationships/{cand_id}", headers=hr_headers)
    assert get_cand.status_code == 200
    assert get_cand.json()["review_status"] == "PENDING"
