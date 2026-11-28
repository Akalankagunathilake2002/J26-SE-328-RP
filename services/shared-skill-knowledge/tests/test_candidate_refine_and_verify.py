import pytest
from httpx import AsyncClient

from tests.conftest import HR_UUID


async def create_test_skill(client: AsyncClient, admin_headers: dict, skill_id: str, name: str):
    res = await client.post(
        "/ssks/skills/",
        headers=admin_headers,
        json={
            "skill_id": skill_id,
            "preferred_name": name,
            "skill_type": "PROGRAMMING_SKILL",
            "status": "ACTIVE",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


async def submit_candidate(
    client: AsyncClient,
    hr_headers: dict,
    source_id: str,
    target_id: str,
    rel_type: str = "RELATED_TO",
    confidence: float = 0.85,
    note: str = "Candidate proposed by ingestion pipeline",
):
    res = await client.post(
        "/ssks/candidates/relationships",
        headers=hr_headers,
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


@pytest.mark.anyio
async def test_approve_candidate_without_overrides(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-A1", "React")
    await create_test_skill(client, admin_headers, "SK-A2", "MERN Stack")

    cand = await submit_candidate(client, hr_headers, "SK-A1", "SK-A2", "PART_OF")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers=hr_headers,
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
    assert data["reviewed_by"] == str(HR_UUID)
    assert data["reviewed_at"] is not None


@pytest.mark.anyio
async def test_approve_candidate_changing_relationship_type(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-B1", "Docker")
    await create_test_skill(client, admin_headers, "SK-B2", "Kubernetes")

    cand = await submit_candidate(client, hr_headers, "SK-B1", "SK-B2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "relationship_type": "PREREQUISITE_OF",
            "review_note": "Corrected relationship type to prerequisite based on curriculum requirements",
        },
        headers=hr_headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["review_status"] == "APPROVED"
    assert data["canonical_relationship"]["relationship_type"] == "PREREQUISITE_OF"
    assert data["review_note"] == "Corrected relationship type to prerequisite based on curriculum requirements"


@pytest.mark.anyio
async def test_approve_candidate_swapping_source_and_target(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-C1", "TypeScript")
    await create_test_skill(client, admin_headers, "SK-C2", "JavaScript")

    cand = await submit_candidate(client, hr_headers, "SK-C1", "SK-C2", "BROADER_THAN")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "APPROVE",
            "source_skill_id": "SK-C2",
            "target_skill_id": "SK-C1",
            "relationship_type": "BROADER_THAN",
            "review_note": "Swapped direction: JavaScript is broader superset of TypeScript",
        },
        headers=hr_headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["canonical_relationship"]["source_skill_id"] == "SK-C2"
    assert data["canonical_relationship"]["target_skill_id"] == "SK-C1"
    assert data["canonical_relationship"]["relationship_type"] == "BROADER_THAN"


@pytest.mark.anyio
async def test_persist_evidence_description_and_url(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-D1", "Express.js")
    await create_test_skill(client, admin_headers, "SK-D2", "Node.js")

    cand = await submit_candidate(client, hr_headers, "SK-D1", "SK-D2", "PART_OF")
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
        headers=hr_headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["evidence_description"] == evidence_desc
    assert data["evidence_url"] == evidence_url
    assert data["canonical_relationship"]["evidence_description"] == evidence_desc
    assert data["canonical_relationship"]["evidence_url"] == evidence_url


@pytest.mark.anyio
async def test_persist_reviewer_and_review_timestamp_ignores_spoofed_headers(
    client: AsyncClient, admin_headers, hr_headers
):
    await create_test_skill(client, admin_headers, "SK-E1", "SQL")
    await create_test_skill(client, admin_headers, "SK-E2", "PostgreSQL")

    cand = await submit_candidate(client, hr_headers, "SK-E1", "SK-E2", "BROADER_THAN")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={
            **hr_headers,
            "X-Reviewer-Id": "spoofed-reviewer-id",
            "X-User-Id": "spoofed-user-id",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["reviewed_by"] == str(HR_UUID)
    assert data["reviewed_at"] is not None
    assert data["canonical_relationship"]["reviewed_by"] == str(HR_UUID)


@pytest.mark.anyio
async def test_reject_invalid_relationship_types(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-F1", "HTML")
    await create_test_skill(client, admin_headers, "SK-F2", "CSS")

    cand = await submit_candidate(client, hr_headers, "SK-F1", "SK-F2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE", "relationship_type": "NON_EXISTENT_REL_TYPE"},
        headers=hr_headers,
    )
    assert res.status_code == 422
    assert "relationship_type" in str(res.json()["detail"])


@pytest.mark.anyio
async def test_reject_nonexistent_skill_ids(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-G1", "FastAPI")
    await create_test_skill(client, admin_headers, "SK-G2", "Pydantic")

    cand = await submit_candidate(client, hr_headers, "SK-G1", "SK-G2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    res_src = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE", "source_skill_id": "SK-NONEXISTENT-999"},
        headers=hr_headers,
    )
    assert res_src.status_code == 404
    assert "Source skill 'SK-NONEXISTENT-999' not found" in res_src.json()["detail"]

    res_tgt = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE", "target_skill_id": "SK-NONEXISTENT-888"},
        headers=hr_headers,
    )
    assert res_tgt.status_code == 404
    assert "Target skill 'SK-NONEXISTENT-888' not found" in res_tgt.json()["detail"]


@pytest.mark.anyio
async def test_reject_identical_source_and_target_skills(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-H1", "Java")
    await create_test_skill(client, admin_headers, "SK-H2", "Spring Boot")

    cand = await submit_candidate(client, hr_headers, "SK-H1", "SK-H2", "PREREQUISITE_OF")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE", "source_skill_id": "SK-H1", "target_skill_id": "SK-H1"},
        headers=hr_headers,
    )
    assert res.status_code == 422
    assert "must be different" in res.json()["detail"]


@pytest.mark.anyio
async def test_handle_duplicate_canonical_relationships(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-I1", "C++")
    await create_test_skill(client, admin_headers, "SK-I2", "Rust")

    await client.post(
        "/ssks/relationships",
        headers=admin_headers,
        json={"source_skill_id": "SK-I1", "target_skill_id": "SK-I2", "relationship_type": "RELATED_TO"},
    )

    cand = await submit_candidate(client, hr_headers, "SK-I1", "SK-I2", "EQUIVALENT_TO")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE", "relationship_type": "RELATED_TO"},
        headers=hr_headers,
    )
    assert res.status_code == 409
    assert "canonical relationship of this type between these skills already exists" in res.json()["detail"]


@pytest.mark.anyio
async def test_rejection_creates_no_canonical_relationship(
    client: AsyncClient, admin_headers, hr_headers, user_headers
):
    await create_test_skill(client, admin_headers, "SK-J1", "Ruby")
    await create_test_skill(client, admin_headers, "SK-J2", "Rails")

    cand = await submit_candidate(client, hr_headers, "SK-J1", "SK-J2", "EQUIVALENT_TO")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={
            "action": "REJECT",
            "review_note": "Ruby and Rails are not equivalent: one is language, one is framework",
        },
        headers=hr_headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["review_status"] == "REJECTED"
    assert data["canonical_relationship_id"] is None
    assert data["canonical_relationship"] is None
    assert data["reviewed_by"] == str(HR_UUID)

    canonical_check = await client.get(
        "/ssks/relationships",
        params={"source_skill_id": "SK-J1", "target_skill_id": "SK-J2"},
        headers=user_headers,
    )
    assert canonical_check.status_code == 200
    assert len(canonical_check.json()) == 0


@pytest.mark.anyio
async def test_failed_approval_leaves_candidate_pending(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-K1", "Go")
    await create_test_skill(client, admin_headers, "SK-K2", "Gin")

    cand = await submit_candidate(client, hr_headers, "SK-K1", "SK-K2", "PREREQUISITE_OF")
    cand_id = cand["candidate_relationship_id"]

    res = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE", "target_skill_id": "SK-GHOST-404"},
        headers=hr_headers,
    )
    assert res.status_code == 404

    cand_check = await client.get(f"/ssks/candidates/relationships/{cand_id}", headers=hr_headers)
    assert cand_check.status_code == 200
    assert cand_check.json()["review_status"] == "PENDING"
    assert cand_check.json()["canonical_relationship_id"] is None


@pytest.mark.anyio
async def test_retry_already_reviewed_candidate_returns_conflict(client: AsyncClient, admin_headers, hr_headers):
    await create_test_skill(client, admin_headers, "SK-L1", "Kafka")
    await create_test_skill(client, admin_headers, "SK-L2", "RabbitMQ")

    cand = await submit_candidate(client, hr_headers, "SK-L1", "SK-L2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    res1 = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers=hr_headers,
    )
    assert res1.status_code == 200

    res2 = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers=hr_headers,
    )
    assert res2.status_code == 409
    assert "already been reviewed" in res2.json()["detail"]


@pytest.mark.anyio
async def test_unauthorised_user_cannot_review(
    client: AsyncClient, admin_headers, hr_headers, user_headers, service_headers
):
    await create_test_skill(client, admin_headers, "SK-N1", "Git")
    await create_test_skill(client, admin_headers, "SK-N2", "GitHub")

    cand = await submit_candidate(client, hr_headers, "SK-N1", "SK-N2", "RELATED_TO")
    cand_id = cand["candidate_relationship_id"]

    res_no_header = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
    )
    assert res_no_header.status_code == 401

    res_spoofed_only = await client.patch(
        f"/ssks/candidates/relationships/{cand_id}/review",
        json={"action": "APPROVE"},
        headers={"X-Reviewer-Id": "admin-1"},
    )
    assert res_spoofed_only.status_code == 401

    assert (
        await client.patch(
            f"/ssks/candidates/relationships/{cand_id}/review",
            json={"action": "APPROVE"},
            headers=user_headers,
        )
    ).status_code == 403

    assert (
        await client.patch(
            f"/ssks/candidates/relationships/{cand_id}/review",
            json={"action": "APPROVE"},
            headers=service_headers,
        )
    ).status_code == 403
