import pytest
from httpx import AsyncClient


async def create_test_skill(client: AsyncClient, skill_id: str, name: str):
    res = await client.post(
        "/ssks/skills/",
        json={
            "skill_id": skill_id,
            "preferred_name": name,
            "skill_type": "PROGRAMMING_SKILL",
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()


async def submit_candidate(
    client: AsyncClient,
    source_id: str,
    target_id: str,
    rel_type: str = "RELATED_TO",
    confidence: float = 0.85,
    note: str = "Candidate proposed by ingestion pipeline",
):
    res = await client.post(
        "/ssks/candidates/relationships",
        json={
            "source_skill_id": source_id,
            "target_skill_id": target_id,
            "proposed_relationship_type": rel_type,
            "confidence_score": confidence,
            "review_note": note,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


# 1. Approve a candidate without overrides, preserving the original proposal
@pytest.mark.anyio
async def test_approve_candidate_without_overrides(client: AsyncClient):
    await create_test_skill(client, "SK-A1", "React")
    await create_test_skill(client, "SK-A2", "MERN Stack")

    cand = await submit_candidate(client, "SK-A1", "SK-A2", "PART_OF")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "admin-auditor-1"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["review_status"] == "APPROVED"
    assert data["source_skill_id"] == "SK-A1"
    assert data["target_skill_id"] == "SK-A2"
    assert data["proposed_relationship_type"] == "PART_OF"
    assert data["canonical_relationship_id"] is not None
    assert data["canonical_relationship"] is not None
    assert data["canonical_relationship"]["source_skill_id"] == "SK-A1"
    assert data["canonical_relationship"]["target_skill_id"] == "SK-A2"
    assert data["canonical_relationship"]["relationship_type"] == "PART_OF"
    assert data["reviewed_by"] == "admin-auditor-1"
    assert data["reviewed_at"] is not None


# 2. Approve a candidate after changing the relationship type
@pytest.mark.anyio
async def test_approve_candidate_changing_relationship_type(client: AsyncClient):
    await create_test_skill(client, "SK-B1", "Docker")
    await create_test_skill(client, "SK-B2", "Kubernetes")

    # Originally proposed as RELATED_TO
    cand = await submit_candidate(client, "SK-B1", "SK-B2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    # Refined to PREREQUISITE_OF during admin review
    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "relationship_type": "PREREQUISITE_OF",
            "review_note": "Corrected relationship type to prerequisite based on curriculum requirements",
        },
        headers={"X-Reviewer-Id": "admin-curriculum"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["review_status"] == "APPROVED"
    assert data["canonical_relationship"]["relationship_type"] == "PREREQUISITE_OF"
    assert data["review_note"] == "Corrected relationship type to prerequisite based on curriculum requirements"


# 3. Approve a candidate after swapping source and target
@pytest.mark.anyio
async def test_approve_candidate_swapping_source_and_target(client: AsyncClient):
    await create_test_skill(client, "SK-C1", "TypeScript")
    await create_test_skill(client, "SK-C2", "JavaScript")

    # Inverted proposal: TypeScript -> BROADER_THAN -> JavaScript (incorrect direction)
    cand = await submit_candidate(client, "SK-C1", "SK-C2", "BROADER_THAN")
    cand_id = cand["candidate_relationship_id"]

    # Swapped: JavaScript (SK-C2) -> BROADER_THAN -> TypeScript (SK-C1)
    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "source_skill_id": "SK-C2",
            "target_skill_id": "SK-C1",
            "relationship_type": "BROADER_THAN",
            "review_note": "Swapped direction: JavaScript is broader superset of TypeScript",
        },
        headers={"X-Reviewer-Id": "lead-reviewer"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["canonical_relationship"]["source_skill_id"] == "SK-C2"
    assert data["canonical_relationship"]["target_skill_id"] == "SK-C1"
    assert data["canonical_relationship"]["relationship_type"] == "BROADER_THAN"


# 4. Persist evidence description and URL
@pytest.mark.anyio
async def test_persist_evidence_description_and_url(client: AsyncClient):
    await create_test_skill(client, "SK-D1", "Express.js")
    await create_test_skill(client, "SK-D2", "Node.js")

    cand = await submit_candidate(client, "SK-D1", "SK-D2", "PART_OF")
    cand_id = cand["candidate_relationship_id"]

    evidence_desc = "Express is standard minimal web application framework running inside Node.js runtime"
    evidence_url = "https://expressjs.com/en/starter/installing.html"

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "evidence_description": evidence_desc,
            "evidence_url": evidence_url,
            "review_note": "Verified with official Express documentation",
        },
        headers={"X-Reviewer-Id": "admin-verified"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["evidence_description"] == evidence_desc
    assert data["evidence_url"] == evidence_url
    assert data["canonical_relationship"]["evidence_description"] == evidence_desc
    assert data["canonical_relationship"]["evidence_url"] == evidence_url


# 5. Persist reviewer and review timestamp
@pytest.mark.anyio
async def test_persist_reviewer_and_review_timestamp(client: AsyncClient):
    await create_test_skill(client, "SK-E1", "SQL")
    await create_test_skill(client, "SK-E2", "PostgreSQL")

    cand = await submit_candidate(client, "SK-E1", "SK-E2", "BROADER_THAN")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "expert-auditor-99"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["reviewed_by"] == "expert-auditor-99"
    assert data["reviewed_at"] is not None
    assert data["canonical_relationship"]["reviewed_by"] == "expert-auditor-99"


# 6. Reject invalid relationship types
@pytest.mark.anyio
async def test_reject_invalid_relationship_types(client: AsyncClient):
    await create_test_skill(client, "SK-F1", "HTML")
    await create_test_skill(client, "SK-F2", "CSS")

    cand = await submit_candidate(client, "SK-F1", "SK-F2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "relationship_type": "NON_EXISTENT_REL_TYPE",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res.status_code == 422
    assert "relationship_type" in str(res.json()["detail"])


# 7. Reject nonexistent skill IDs
@pytest.mark.anyio
async def test_reject_nonexistent_skill_ids(client: AsyncClient):
    await create_test_skill(client, "SK-G1", "FastAPI")
    await create_test_skill(client, "SK-G2", "Pydantic")

    cand = await submit_candidate(client, "SK-G1", "SK-G2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    # Nonexistent source override
    res_src = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "source_skill_id": "SK-NONEXISTENT-999",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res_src.status_code == 404
    assert "Source skill 'SK-NONEXISTENT-999' not found" in res_src.json()["detail"]

    # Nonexistent target override
    res_tgt = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "target_skill_id": "SK-NONEXISTENT-888",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res_tgt.status_code == 404
    assert "Target skill 'SK-NONEXISTENT-888' not found" in res_tgt.json()["detail"]


# 8. Reject identical source and target skills
@pytest.mark.anyio
async def test_reject_identical_source_and_target_skills(client: AsyncClient):
    await create_test_skill(client, "SK-H1", "Java")
    await create_test_skill(client, "SK-H2", "Spring Boot")

    cand = await submit_candidate(client, "SK-H1", "SK-H2", "PREREQUISITE_OF")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "source_skill_id": "SK-H1",
            "target_skill_id": "SK-H1",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res.status_code == 422
    assert "must be different" in res.json()["detail"]


# 9. Handle duplicate canonical relationships
@pytest.mark.anyio
async def test_handle_duplicate_canonical_relationships(client: AsyncClient):
    await create_test_skill(client, "SK-I1", "C++")
    await create_test_skill(client, "SK-I2", "Rust")

    # Manually create existing canonical relationship
    await client.post(
        "/ssks/relationships",
        json={
            "source_skill_id": "SK-I1",
            "target_skill_id": "SK-I2",
            "relationship_type": "RELATED_TO",
        },
    )

    # Candidate proposing a duplicate
    cand = await submit_candidate(client, "SK-I1", "SK-I2", "EQUIVALENT_TO")
    cand_id = cand["candidate_relationship_id"]

    # Try to approve with relationship_type="RELATED_TO" which already exists as canonical
    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "relationship_type": "RELATED_TO",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res.status_code == 409
    assert "canonical relationship of this type between these skills already exists" in res.json()["detail"]


# 10. Verify that rejection creates no canonical relationship
@pytest.mark.anyio
async def test_rejection_creates_no_canonical_relationship(client: AsyncClient):
    await create_test_skill(client, "SK-J1", "Ruby")
    await create_test_skill(client, "SK-J2", "Rails")

    cand = await submit_candidate(client, "SK-J1", "SK-J2", "EQUIVALENT_TO")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "REJECT",
            "review_note": "Ruby and Rails are not equivalent: one is language, one is framework",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["review_status"] == "REJECTED"
    assert data["canonical_relationship_id"] is None
    assert data["canonical_relationship"] is None
    assert data["reviewed_by"] == "admin-1"

    # Verify no canonical relationship was created between Ruby and Rails
    canonical_check = await client.get(
        "/ssks/relationships",
        params={"source_skill_id": "SK-J1", "target_skill_id": "SK-J2"},
    )
    assert canonical_check.status_code == 200
    assert len(canonical_check.json()) == 0


# 11. Verify that failed approval does not leave the candidate approved
@pytest.mark.anyio
async def test_failed_approval_leaves_candidate_pending(client: AsyncClient):
    await create_test_skill(client, "SK-K1", "Go")
    await create_test_skill(client, "SK-K2", "Gin")

    cand = await submit_candidate(client, "SK-K1", "SK-K2", "PREREQUISITE_OF")
    cand_id = cand["candidate_relationship_id"]

    # Attempt approval with nonexistent skill ID
    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "target_skill_id": "SK-GHOST-404",
        },
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res.status_code == 404

    # Fetch candidate and verify it remains PENDING
    cand_check = await client.get(f"/ssks/candidates/relationships/{cand_id}")
    assert cand_check.status_code == 200
    assert cand_check.json()["review_status"] == "PENDING"
    assert cand_check.json()["canonical_relationship_id"] is None


# 12. Verify retry/idempotency behavior (already reviewed candidate returns 409)
@pytest.mark.anyio
async def test_retry_already_reviewed_candidate_returns_conflict(client: AsyncClient):
    await create_test_skill(client, "SK-L1", "Kafka")
    await create_test_skill(client, "SK-L2", "RabbitMQ")

    cand = await submit_candidate(client, "SK-L1", "SK-L2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    # First review: approve
    res1 = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res1.status_code == 200

    # Second review: retry must return 409 Conflict
    res2 = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res2.status_code == 409
    assert "already been reviewed" in res2.json()["detail"]


# 13. Verify knowledge-version publication: snapshot version updates and contains the new verified relationship
@pytest.mark.anyio
async def test_knowledge_version_publication_on_approval(client: AsyncClient):
    await create_test_skill(client, "SK-M1", "Kubernetes")
    await create_test_skill(client, "SK-M2", "Helm")

    # Initial snapshot metadata
    snap_before = await client.get("/ssks/snapshots/metadata")
    assert snap_before.status_code == 200
    version_before = snap_before.json()["version"]
    rel_count_before = snap_before.json()["counts"]["relationships"]

    # Submit and approve candidate
    cand = await submit_candidate(client, "SK-M2", "SK-M1", "PART_OF")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "publisher-admin"},
    )
    assert res.status_code == 200
    approved_cand = res.json()
    assert approved_cand["published_snapshot_version"] is not None

    # Snapshot metadata should now reflect the updated relationship count and new version hash
    snap_after = await client.get("/ssks/snapshots/metadata")
    assert snap_after.status_code == 200
    version_after = snap_after.json()["version"]
    rel_count_after = snap_after.json()["counts"]["relationships"]

    assert rel_count_after == rel_count_before + 1
    assert version_after != version_before
    assert approved_cand["published_snapshot_version"] == version_after

    # Export snapshot and verify the verified relationship is contained in the exported payload
    export_res = await client.get("/ssks/snapshots/export")
    assert export_res.status_code == 200
    export_data = export_res.json()
    rel_found = any(
        r["source_skill_id"] == "SK-M2"
        and r["target_skill_id"] == "SK-M1"
        and r["relationship_type"] == "PART_OF"
        for r in export_data["relationships"]
    )
    assert rel_found, "Approved relationship was not found in exported published snapshot"


# 14. Verify unauthorised users cannot perform administrative review operations
@pytest.mark.anyio
async def test_unauthorised_user_cannot_review(client: AsyncClient):
    await create_test_skill(client, "SK-N1", "Git")
    await create_test_skill(client, "SK-N2", "GitHub")

    cand = await submit_candidate(client, "SK-N1", "SK-N2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    # Missing X-Reviewer-Id header
    res_no_header = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
    )
    assert res_no_header.status_code == 403
    assert "Reviewer authorization required" in res_no_header.json()["detail"]

    # Empty X-Reviewer-Id header
    res_empty_header = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "   "},
    )
    assert res_empty_header.status_code == 403
