import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_session
from app.models.core import Skill, Role
from app.models.aliases import SkillAlias, RoleAlias
from app.models.candidates import CandidateEntity

from tests.conftest import TestingSessionLocal

async def seed_normalization_data():
    async with TestingSessionLocal() as session:
        skill1 = Skill(
            skill_id="SK-000001",
            preferred_name="Python",
            skill_type="PROGRAMMING_LANGUAGE",
            skill_nature="TECHNICAL",
            status="ACTIVE",
        )
        skill2 = Skill(
            skill_id="SK-000002",
            preferred_name="JavaScript",
            skill_type="PROGRAMMING_LANGUAGE",
            skill_nature="TECHNICAL",
            status="ACTIVE",
        )
        skill3 = Skill(
            skill_id="SK-000003",
            preferred_name="Node.js",
            skill_type="SOFTWARE_OR_TOOL",
            skill_nature="TECHNICAL",
            status="ACTIVE",
        )
        session.add_all([skill1, skill2, skill3])

        role1 = Role(
            role_id="RL-000001",
            preferred_name="Frontend Developer",
            status="ACTIVE",
        )
        role2 = Role(
            role_id="RL-000002",
            preferred_name="Data Engineer",
            status="ACTIVE",
        )
        session.add_all([role1, role2])

        alias1 = SkillAlias(
            alias_id="AL-000001",
            skill_id="SK-000002",
            alias_text="JS",
            normalized_alias="js",
            verification_status="VERIFIED",
        )
        alias2 = SkillAlias(
            alias_id="AL-000002",
            skill_id="SK-000001",
            alias_text="Py",
            normalized_alias="py",
            verification_status="UNVERIFIED",
        )
        session.add_all([alias1, alias2])

        role_alias1 = RoleAlias(
            alias_id="AL-000003",
            role_id="RL-000001",
            alias_text="UI Developer",
            normalized_alias="ui developer",
            verification_status="VERIFIED",
        )
        role_alias2 = RoleAlias(
            alias_id="AL-000004",
            role_id="RL-000002",
            alias_text="Big Data Dev",
            normalized_alias="big data dev",
            verification_status="UNVERIFIED",
        )
        session.add_all([role_alias1, role_alias2])

        await session.commit()

# ==================== Normalization Tests ====================

@pytest.mark.anyio
async def test_normalization_canonical_exact_match(client):
    await seed_normalization_data()
    res = await client.post("/ssks/normalize/skills", json={
        "items": ["python", "  JavaScript  ", "Node.js"]
    })
    assert res.status_code == 200
    data = res.json()["results"]
    assert len(data) == 3

    assert data[0]["input_name"] == "python"
    assert data[0]["status"] == "MATCHED"
    assert data[0]["canonical_id"] == "SK-000001"
    assert data[0]["preferred_name"] == "Python"
    assert data[0]["matching_method"] == "CANONICAL_NAME"

    assert data[1]["input_name"] == "  JavaScript  "
    assert data[1]["status"] == "MATCHED"
    assert data[1]["canonical_id"] == "SK-000002"
    assert data[1]["preferred_name"] == "JavaScript"
    assert data[1]["matching_method"] == "CANONICAL_NAME"

    assert data[2]["input_name"] == "Node.js"
    assert data[2]["status"] == "MATCHED"
    assert data[2]["canonical_id"] == "SK-000003"
    assert data[2]["preferred_name"] == "Node.js"

@pytest.mark.anyio
async def test_normalization_verified_alias_match(client):
    await seed_normalization_data()
    res = await client.post("/ssks/normalize/skills", json={
        "items": ["JS", "js"]
    })
    assert res.status_code == 200
    data = res.json()["results"]
    for item in data:
        assert item["status"] == "MATCHED"
        assert item["canonical_id"] == "SK-000002"
        assert item["preferred_name"] == "JavaScript"
        assert item["matching_method"] == "VERIFIED_ALIAS"

@pytest.mark.anyio
async def test_normalization_unverified_alias_not_authoritative(client):
    await seed_normalization_data()
    # 'Py' is an UNVERIFIED alias for Python
    res = await client.post("/ssks/normalize/skills", json={
        "items": ["Py"]
    })
    assert res.status_code == 200
    data = res.json()["results"]
    # Must NOT be MATCHED
    assert data[0]["status"] != "MATCHED"
    assert data[0]["canonical_id"] is None

@pytest.mark.anyio
async def test_normalization_fuzzy_suggestions_not_automatic_match(client):
    await seed_normalization_data()
    # 'Pythn' is close to 'Python'
    res = await client.post("/ssks/normalize/skills", json={
        "items": ["Pythn", "UnknownFrameworkXYZ"]
    })
    assert res.status_code == 200
    data = res.json()["results"]

    # Fuzzy suggestion
    assert data[0]["input_name"] == "Pythn"
    assert data[0]["status"] == "SUGGESTED"
    assert data[0]["canonical_id"] is None
    assert data[0]["matching_method"] == "FUZZY_SUGGESTION"
    assert len(data[0]["suggestions"]) > 0
    assert data[0]["suggestions"][0]["canonical_id"] == "SK-000001"
    assert data[0]["suggestions"][0]["preferred_name"] == "Python"
    assert data[0]["suggestions"][0]["score"] >= 0.80

    # Completely unmatched
    assert data[1]["input_name"] == "UnknownFrameworkXYZ"
    assert data[1]["status"] == "UNMATCHED"
    assert data[1]["canonical_id"] is None
    assert data[1]["matching_method"] is None
    assert len(data[1]["suggestions"]) == 0

@pytest.mark.anyio
async def test_normalization_skill_and_role_separation(client):
    await seed_normalization_data()
    # Frontend Developer is a role, not a skill
    res_skill = await client.post("/ssks/normalize/skills", json={
        "items": ["Frontend Developer"]
    })
    assert res_skill.status_code == 200
    assert res_skill.json()["results"][0]["status"] == "UNMATCHED"

    # Now normalize via roles endpoint
    res_role = await client.post("/ssks/normalize/roles", json={
        "items": ["Frontend Developer", "ui developer", "big data dev"]
    })
    assert res_role.status_code == 200
    role_results = res_role.json()["results"]
    assert role_results[0]["status"] == "MATCHED"
    assert role_results[0]["canonical_id"] == "RL-000001"
    assert role_results[0]["matching_method"] == "CANONICAL_NAME"

    # Verified role alias
    assert role_results[1]["status"] == "MATCHED"
    assert role_results[1]["canonical_id"] == "RL-000001"
    assert role_results[1]["matching_method"] == "VERIFIED_ALIAS"

    # Unverified role alias must not match
    assert role_results[2]["status"] != "MATCHED"

@pytest.mark.anyio
async def test_normalization_validation_and_deduplication(client):
    await seed_normalization_data()
    # Empty request must be rejected with 422
    empty_res = await client.post("/ssks/normalize/skills", json={"items": []})
    assert empty_res.status_code == 422

    # Multiple identical and repeated inputs
    res = await client.post("/ssks/normalize/skills", json={
        "items": ["Python", "python", "Python", "JS"]
    })
    assert res.status_code == 200
    data = res.json()["results"]
    assert len(data) == 4
    assert data[0]["status"] == "MATCHED"
    assert data[1]["status"] == "MATCHED"
    assert data[2]["status"] == "MATCHED"
    assert data[3]["status"] == "MATCHED"

# ==================== Candidate Entity Tests ====================

@pytest.mark.anyio
async def test_candidate_submission_success(client):
    res = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "FastAPI",
        "description": "Modern async Python web framework",
        "proposed_skill_type": "SOFTWARE_OR_TOOL",
        "proposed_skill_nature": "TECHNICAL",
        "source_component": "C01",
        "source_reference": "job_listing_456"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["candidate_entity_id"].startswith("CE-")
    assert data["entity_type"] == "SKILL"
    assert data["submitted_name"] == "FastAPI"
    assert data["normalized_name"] == "fastapi"
    assert data["review_status"] == "PENDING"
    assert data["matched_entity_id"] is None

@pytest.mark.anyio
async def test_candidate_submission_duplicate_detection(client):
    await seed_normalization_data()

    # 1. Existing canonical skill conflict
    res_canon = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "  Python  ",
        "proposed_skill_type": "PROGRAMMING_LANGUAGE"
    })
    assert res_canon.status_code == 409
    assert "canonical skill already exists" in res_canon.json()["detail"].lower()

    # 2. Existing verified alias conflict
    res_alias = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "JS",
        "proposed_skill_type": "PROGRAMMING_LANGUAGE"
    })
    assert res_alias.status_code == 409
    assert "verified skill alias already exists" in res_alias.json()["detail"].lower()

    # 3. First submission succeeds
    res_cand1 = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "Kubernetes",
        "proposed_skill_type": "SOFTWARE_OR_TOOL"
    })
    assert res_cand1.status_code == 201

    # 4. Duplicate pending submission conflicts
    res_cand2 = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "kubernetes",
        "proposed_skill_type": "SOFTWARE_OR_TOOL"
    })
    assert res_cand2.status_code == 409
    assert "pending candidate already exists" in res_cand2.json()["detail"].lower()

@pytest.mark.anyio
async def test_candidate_invalid_metadata_and_role_fields(client):
    # Role cannot have proposed skill fields
    res1 = await client.post("/ssks/candidates/entities", json={
        "entity_type": "ROLE",
        "submitted_name": "DevOps Engineer",
        "proposed_skill_type": "SOFTWARE_OR_TOOL"
    })
    assert res1.status_code == 422

    # Invalid skill type enum
    res2 = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "GraphQL",
        "proposed_skill_type": "INVALID_TYPE"
    })
    assert res2.status_code == 422

@pytest.mark.anyio
async def test_candidate_listing_and_retrieval(client):
    await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "Skill A",
        "proposed_skill_type": "KNOWLEDGE"
    })
    await client.post("/ssks/candidates/entities", json={
        "entity_type": "ROLE",
        "submitted_name": "Role B"
    })

    # List all
    res = await client.get("/ssks/candidates/entities")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Filter by entity_type
    res_skills = await client.get("/ssks/candidates/entities?entity_type=SKILL")
    assert len(res_skills.json()) == 1
    assert res_skills.json()[0]["submitted_name"] == "Skill A"

    # Get by ID
    cand_id = res_skills.json()[0]["candidate_entity_id"]
    get_res = await client.get(f"/ssks/candidates/entities/{cand_id}")
    assert get_res.status_code == 200
    assert get_res.json()["candidate_entity_id"] == cand_id

    # 404 for missing
    assert (await client.get("/ssks/candidates/entities/CE-999999")).status_code == 404

@pytest.mark.anyio
async def test_candidate_review_authorization_check(client):
    res_cand = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "Rust",
        "proposed_skill_type": "PROGRAMMING_LANGUAGE"
    })
    cand_id = res_cand.json()["candidate_entity_id"]

    # Missing reviewer header must return 403
    res_no_auth = await client.patch(f"/ssks/candidates/entities/{cand_id}/review", json={
        "action": "APPROVE"
    })
    assert res_no_auth.status_code == 403
    assert "reviewer authorization required" in res_no_auth.json()["detail"].lower()

@pytest.mark.anyio
async def test_candidate_approval_workflow(client):
    await seed_normalization_data()

    res_cand = await client.post("/ssks/candidates/entities", json={
        "entity_type": "SKILL",
        "submitted_name": "Rust",
        "description": "Systems programming language",
        "proposed_skill_type": "PROGRAMMING_LANGUAGE",
        "proposed_skill_nature": "TECHNICAL"
    })
    cand_id = res_cand.json()["candidate_entity_id"]

    # Approve with reviewer header
    approve_res = await client.patch(
        f"/ssks/candidates/entities/{cand_id}/review",
        headers={"X-Reviewer-Id": "reviewer_alice"},
        json={
            "action": "APPROVE",
            "review_note": "Approved by senior reviewer"
        }
    )
    assert approve_res.status_code == 200
    cand_data = approve_res.json()
    assert cand_data["review_status"] == "APPROVED"
    assert cand_data["matched_entity_id"] is not None
    assert cand_data["matched_entity_id"].startswith("SK-")
    assert cand_data["review_note"] == "Approved by senior reviewer"
    assert cand_data["reviewed_at"] is not None

    canonical_id = cand_data["matched_entity_id"]

    # Verify canonical skill was created in database
    get_skill_res = await client.get(f"/ssks/skills/{canonical_id}")
    assert get_skill_res.status_code == 200
    assert get_skill_res.json()["skill_id"] == canonical_id
    assert get_skill_res.json()["preferred_name"] == "Rust"
    assert get_skill_res.json()["skill_type"] == "PROGRAMMING_LANGUAGE"
    assert get_skill_res.json()["skill_nature"] == "TECHNICAL"

    # Repeat approval must return 409 Conflict
    repeat_res = await client.patch(
        f"/ssks/candidates/entities/{cand_id}/review",
        headers={"X-Reviewer-Id": "reviewer_alice"},
        json={"action": "APPROVE"}
    )
    assert repeat_res.status_code == 409
    assert "already been reviewed" in repeat_res.json()["detail"]

@pytest.mark.anyio
async def test_candidate_rejection_workflow(client):
    res_cand = await client.post("/ssks/candidates/entities", json={
        "entity_type": "ROLE",
        "submitted_name": "Temporary Typo Role"
    })
    cand_id = res_cand.json()["candidate_entity_id"]

    reject_res = await client.patch(
        f"/ssks/candidates/entities/{cand_id}/review",
        headers={"X-Reviewer-Id": "reviewer_bob"},
        json={
            "action": "REJECT",
            "review_note": "Spam entry"
        }
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["review_status"] == "REJECTED"
    assert data["matched_entity_id"] is None
    assert data["review_note"] == "Spam entry"
    assert data["reviewed_at"] is not None

    # Ensure no canonical role was created
    roles_list = (await client.get("/ssks/roles/")).json()
    assert not any(r["preferred_name"] == "Temporary Typo Role" for r in roles_list)
