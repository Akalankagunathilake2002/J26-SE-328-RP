import pytest
from httpx import AsyncClient


async def create_test_skill(client: AsyncClient, skill_id: str, name: str):
    res = await client.post(
        "/ssks/skills/",
        json={
            "skill_id": skill_id,
            "preferred_name": name,
            "skill_type": "PROGRAMMING_LANGUAGE",
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 200
    return res.json()


async def create_test_role(client: AsyncClient, role_id: str, name: str):
    res = await client.post(
        "/ssks/roles/",
        json={
            "role_id": role_id,
            "preferred_name": name,
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 200
    return res.json()


async def create_test_domain(client: AsyncClient, domain_id: str, code: str, name: str):
    res = await client.post(
        "/ssks/domains/",
        json={
            "domain_id": domain_id,
            "code": code,
            "name": name,
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 200
    return res.json()


@pytest.mark.anyio
async def test_canonical_relationship_creation_and_validations(client: AsyncClient):
    await create_test_skill(client, "SK-101", "Python")
    await create_test_skill(client, "SK-102", "Django")

    # 1. Successful creation
    res = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-102",
            "target_skill_id": "SK-101",
            "relationship_type": "PREREQUISITE_OF",
            "evidence_note": "Django requires Python",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["relationship_id"].startswith("REL-")
    assert data["source_skill_id"] == "SK-102"
    assert data["target_skill_id"] == "SK-101"
    assert data["relationship_type"] == "PREREQUISITE_OF"
    assert data["verification_status"] == "VERIFIED"
    assert data["evidence_note"] == "Django requires Python"

    # 2. Self reference rejection
    res_self = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-101",
            "target_skill_id": "SK-101",
            "relationship_type": "EQUIVALENT_TO",
        },
    )
    assert res_self.status_code == 422
    assert "different" in res_self.json()["detail"].lower()

    # 3. Nonexistent skill
    res_no_src = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-999999",
            "target_skill_id": "SK-101",
            "relationship_type": "RELATED_TO",
        },
    )
    assert res_no_src.status_code == 404

    # 4. Invalid relationship type
    res_invalid_type = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-101",
            "target_skill_id": "SK-102",
            "relationship_type": "INVALID_TYPE",
        },
    )
    assert res_invalid_type.status_code == 422

    # 5. Duplicate relationship
    res_dup = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-102",
            "target_skill_id": "SK-101",
            "relationship_type": "PREREQUISITE_OF",
        },
    )
    assert res_dup.status_code == 409


@pytest.mark.anyio
async def test_canonical_relationship_listing_filtering_pagination(client: AsyncClient):
    await create_test_skill(client, "SK-201", "JavaScript")
    await create_test_skill(client, "SK-202", "TypeScript")
    await create_test_skill(client, "SK-203", "React")

    # Create 2 relationships
    await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-202",
            "target_skill_id": "SK-201",
            "relationship_type": "BROADER_THAN",
        },
    )
    await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-203",
            "target_skill_id": "SK-201",
            "relationship_type": "RELATED_TO",
        },
    )

    # List all
    res = await client.get("/ssks/relationships")
    assert res.status_code == 200
    assert len(res.json()) >= 2

    # Filter by source_skill_id
    res_src = await client.get("/ssks/relationships?source_skill_id=SK-202")
    assert res_src.status_code == 200
    items = res_src.json()
    assert len(items) == 1
    assert items[0]["source_skill_id"] == "SK-202"

    # Filter by relationship_type
    res_type = await client.get("/ssks/relationships?relationship_type=RELATED_TO")
    assert res_type.status_code == 200
    items_type = res_type.json()
    assert len(items_type) >= 1
    assert all(r["relationship_type"] == "RELATED_TO" for r in items_type)


@pytest.mark.anyio
async def test_canonical_relationship_get_update_delete(client: AsyncClient):
    await create_test_skill(client, "SK-301", "C")
    await create_test_skill(client, "SK-302", "C++")

    create_res = await client.post(
        "/ssks/relationships",
        json={
            "relationship_id": "REL-CUSTOM-1",
            "source_skill_id": "SK-302",
            "target_skill_id": "SK-301",
            "relationship_type": "RELATED_TO",
            "evidence_note": "Initial note",
        },
    )
    assert create_res.status_code == 201
    rel_id = create_res.json()["relationship_id"]
    assert rel_id == "REL-CUSTOM-1"

    # Get by ID
    get_res = await client.get(f"/ssks/relationships/{rel_id}")
    assert get_res.status_code == 200
    assert get_res.json()["evidence_note"] == "Initial note"

    # Get non-existent
    assert (await client.get("/ssks/relationships/REL-NONEXISTENT")).status_code == 404

    # PATCH update
    patch_res = await client.patch(
        f"/ssks/relationships/{rel_id}",
        json={
            "relationship_type": "BROADER_THAN",
            "evidence_note": "Updated note",
        },
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["relationship_type"] == "BROADER_THAN"
    assert patch_res.json()["evidence_note"] == "Updated note"

    # DELETE
    del_res = await client.delete(f"/ssks/relationships/{rel_id}")
    assert del_res.status_code == 204

    # Verify deleted
    assert (await client.get(f"/ssks/relationships/{rel_id}")).status_code == 404
    assert (await client.delete(f"/ssks/relationships/{rel_id}")).status_code == 404


@pytest.mark.anyio
async def test_candidate_relationship_submission_and_validation(client: AsyncClient):
    await create_test_skill(client, "SK-401", "Go")
    await create_test_skill(client, "SK-402", "Docker")

    # 1. Success
    res = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-402",
            "target_skill_id": "SK-401",
            "proposed_relationship_type": "RELATED_TO",
            "confidence_score": 0.85,
            "review_note": "Proposed by automated extractor",
        },
    )
    assert res.status_code == 201
    cand = res.json()
    assert cand["candidate_relationship_id"].startswith("CR-")
    assert cand["review_status"] == "PENDING"
    assert cand["confidence_score"] == 0.85

    # 2. Self reference
    res_self = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-401",
            "target_skill_id": "SK-401",
            "proposed_relationship_type": "EQUIVALENT_TO",
        },
    )
    assert res_self.status_code == 422

    # 3. Invalid confidence score
    res_conf = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-401",
            "target_skill_id": "SK-402",
            "proposed_relationship_type": "RELATED_TO",
            "confidence_score": 1.5,
        },
    )
    assert res_conf.status_code == 422

    # 4. Duplicate pending candidate
    res_dup = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-402",
            "target_skill_id": "SK-401",
            "proposed_relationship_type": "RELATED_TO",
        },
    )
    assert res_dup.status_code == 409
    assert "pending candidate relationship already exists" in res_dup.json()["detail"]


@pytest.mark.anyio
async def test_candidate_relationship_review_workflow(client: AsyncClient):
    await create_test_skill(client, "SK-501", "HTML")
    await create_test_skill(client, "SK-502", "CSS")
    await create_test_skill(client, "SK-503", "Sass")

    # Submit candidate 1
    c1_res = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-503",
            "target_skill_id": "SK-502",
            "proposed_relationship_type": "PREREQUISITE_OF",
        },
    )
    c1_id = c1_res.json()["candidate_relationship_id"]

    # 1. Review without reviewer header -> 403 Forbidden
    res_no_auth = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        json={"action": "APPROVED"},
    )
    assert res_no_auth.status_code == 403

    # 2. Approve candidate 1
    approve_res = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        headers={"X-Reviewer-Id": "reviewer-alice"},
        json={
            "action": "APPROVED",
            "review_note": "Verified by reviewer Alice",
        },
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["review_status"] == "APPROVED"
    assert approve_res.json()["reviewed_at"] is not None

    # Check that canonical relationship was created atomically
    rel_res = await client.get(
        f"/ssks/relationships?source_skill_id=SK-503&target_skill_id=SK-502"
    )
    assert rel_res.status_code == 200
    rels = rel_res.json()
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "PREREQUISITE_OF"
    assert rels[0]["verification_status"] == "VERIFIED"

    # 3. Already reviewed candidate -> 409 Conflict
    already_rev = await client.patch(
        f"/ssks/candidates/relationships/{c1_id}/review",
        headers={"X-Reviewer-Id": "reviewer-alice"},
        json={"action": "REJECTED"},
    )
    assert already_rev.status_code == 409

    # 4. Rejection workflow for candidate 2
    c2_res = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-501",
            "target_skill_id": "SK-503",
            "proposed_relationship_type": "BROADER_THAN",
        },
    )
    c2_id = c2_res.json()["candidate_relationship_id"]

    reject_res = await client.patch(
        f"/ssks/candidates/relationships/{c2_id}/review",
        headers={"X-Reviewer-Id": "reviewer-bob"},
        json={
            "action": "REJECTED",
            "review_note": "Not broader than Sass",
        },
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["review_status"] == "REJECTED"

    # Ensure no canonical relationship was created for candidate 2
    rel_check = await client.get(
        f"/ssks/relationships?source_skill_id=SK-501&target_skill_id=SK-503"
    )
    assert rel_check.status_code == 200
    assert len(rel_check.json()) == 0


@pytest.mark.anyio
async def test_skill_and_role_domain_associations(client: AsyncClient):
    await create_test_domain(client, "DOM-10", "CLOUD", "Cloud Computing")
    await create_test_skill(client, "SK-601", "Kubernetes")
    await create_test_role(client, "RL-601", "Cloud Architect")

    # --- Skill Domain Associations ---
    # Initially empty
    res_s_init = await client.get("/ssks/skills/SK-601/domains")
    assert res_s_init.status_code == 200
    assert res_s_init.json() == []

    # Associate skill with domain (PUT)
    res_s_put = await client.put("/ssks/skills/SK-601/domains/DOM-10")
    assert res_s_put.status_code == 200
    assert res_s_put.json() == {"skill_id": "SK-601", "domain_id": "DOM-10"}

    # Duplicate association is idempotent
    res_s_dup = await client.put("/ssks/skills/SK-601/domains/DOM-10")
    assert res_s_dup.status_code == 200
    assert res_s_dup.json() == {"skill_id": "SK-601", "domain_id": "DOM-10"}

    # List skill domains
    res_s_list = await client.get("/ssks/skills/SK-601/domains")
    assert res_s_list.status_code == 200
    assert len(res_s_list.json()) == 1
    assert res_s_list.json()[0]["domain_id"] == "DOM-10"

    # Remove skill domain association
    res_s_del = await client.delete("/ssks/skills/SK-601/domains/DOM-10")
    assert res_s_del.status_code == 204

    # Verify deleted
    assert (await client.get("/ssks/skills/SK-601/domains")).json() == []
    assert (await client.delete("/ssks/skills/SK-601/domains/DOM-10")).status_code == 404

    # Invalid skill / domain
    assert (await client.put("/ssks/skills/SK-NONEXISTENT/domains/DOM-10")).status_code == 404
    assert (await client.put("/ssks/skills/SK-601/domains/DOM-NONEXISTENT")).status_code == 404

    # --- Role Domain Associations ---
    # Initially empty
    assert (await client.get("/ssks/roles/RL-601/domains")).json() == []

    # Associate role with domain (PUT)
    res_r_put = await client.put("/ssks/roles/RL-601/domains/DOM-10")
    assert res_r_put.status_code == 200
    assert res_r_put.json() == {"role_id": "RL-601", "domain_id": "DOM-10"}

    # Duplicate idempotent
    assert (await client.put("/ssks/roles/RL-601/domains/DOM-10")).status_code == 200

    # List role domains
    res_r_list = await client.get("/ssks/roles/RL-601/domains")
    assert len(res_r_list.json()) == 1
    assert res_r_list.json()[0]["code"] == "CLOUD"

    # Remove role domain association
    assert (await client.delete("/ssks/roles/RL-601/domains/DOM-10")).status_code == 204
    assert (await client.get("/ssks/roles/RL-601/domains")).json() == []
    assert (await client.delete("/ssks/roles/RL-601/domains/DOM-10")).status_code == 404

    # Invalid role / domain
    assert (await client.put("/ssks/roles/RL-NONEXISTENT/domains/DOM-10")).status_code == 404
    assert (await client.put("/ssks/roles/RL-601/domains/DOM-NONEXISTENT")).status_code == 404


@pytest.mark.anyio
async def test_openapi_schema_contains_all_endpoints(client: AsyncClient):
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
    ]
    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Expected endpoint {endpoint} not found in OpenAPI paths"

@pytest.mark.anyio
async def test_directionality_not_reversed_automatically(client: AsyncClient):
    await create_test_skill(client, "SK-701", "Math")
    await create_test_skill(client, "SK-702", "Calculus")

    # SK-702 (Calculus) is PART_OF SK-701 (Math)
    res = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-702",
            "target_skill_id": "SK-701",
            "relationship_type": "PART_OF",
        },
    )
    assert res.status_code == 201

    # Directionality: Query with source_skill_id=SK-701 must NOT return any relationship
    res_reverse = await client.get("/ssks/relationships?source_skill_id=SK-701")
    assert res_reverse.status_code == 200
    assert len(res_reverse.json()) == 0

    # Query with source_skill_id=SK-702 returns the forward relationship
    res_forward = await client.get("/ssks/relationships?source_skill_id=SK-702")
    assert res_forward.status_code == 200
    assert len(res_forward.json()) == 1
    assert res_forward.json()[0]["target_skill_id"] == "SK-701"


@pytest.mark.anyio
async def test_candidate_approval_rollback_on_canonical_conflict(client: AsyncClient):
    await create_test_skill(client, "SK-801", "Kotlin")
    await create_test_skill(client, "SK-802", "Java")

    # Submit candidate
    cand_res = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": "SK-801",
            "target_skill_id": "SK-802",
            "proposed_relationship_type": "RELATED_TO",
        },
    )
    assert cand_res.status_code == 201
    cand_id = cand_res.json()["candidate_relationship_id"]

    # In the meantime, someone directly creates a canonical relationship for that exact pair
    rel_res = await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-801",
            "target_skill_id": "SK-802",
            "relationship_type": "RELATED_TO",
        },
    )
    assert rel_res.status_code == 201

    # Now reviewer attempts to approve candidate -> must fail with 409 conflict
    approve_res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        headers={"X-Reviewer-Id": "reviewer-charlie"},
        json={"action": "APPROVED"},
    )
    assert approve_res.status_code == 409
    assert "already exists" in approve_res.json()["detail"].lower()

    # Verify candidate status remained PENDING and was not corrupted
    get_cand = await client.get(f"/ssks/candidates/relationships/{cand_id}")
    assert get_cand.status_code == 200
    assert get_cand.json()["review_status"] == "PENDING"

