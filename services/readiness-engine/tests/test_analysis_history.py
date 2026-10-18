import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import dispose_engine, get_sessionmaker
from app.models.analysis import Analysis, AnalysisStatus
from app.models.cache import KnowledgeSnapshot
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)


# Dispose engine after each test to ensure clean database connections
@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    yield
    await dispose_engine()


# Helper to generate unique canonical role IDs for isolated testing
def _generate_role_id() -> str:
    return f"RL-{random.randint(100000, 999999)}"


# Helper to persist a custom industry profile
async def _create_industry_profile(
    session,
    role_id: str,
    role_title: str,
    requirements: list[dict[str, Any]],
) -> IndustryProfile:
    profile = IndustryProfile(
        id=uuid.uuid4(),
        role_id=role_id,
        primary_observed_title=role_title,
        mapping_status="verified",
        career_level="ENTRY_LEVEL",
        profile_version=f"v-{uuid.uuid4().hex[:8]}",
        raw_payload={"source": "test_history"},
    )
    for r in requirements:
        req = IndustryProfileRequirement(
            id=uuid.uuid4(),
            industry_profile_id=profile.id,
            skill_id=r.get("skill_id", "SK-000001"),
            standard_name=r["standard_name"],
            primary_observed_term=r["standard_name"],
            observed_terms=[],
            mapping_status=r.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            required_proficiency_level=r.get(
                "required_proficiency_level", "INTERMEDIATE"
            ),
            required_proficiency_score=r.get("required_proficiency_score", 0.7),
            demand_weight=r.get("demand_weight", 1.0),
        )
        profile.requirements.append(req)

    session.add(profile)
    await session.commit()
    return profile


# Helper to persist a custom student skill profile
async def _create_user_profile(
    session,
    user_id: uuid.UUID,
    skills: list[dict[str, Any]],
) -> UserSkillProfile:
    profile = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=user_id,
        profile_version=f"v-{uuid.uuid4().hex[:8]}",
        raw_payload={"source": "test_history"},
    )
    for s in skills:
        skill_entry = UserSkillProfileSkill(
            id=uuid.uuid4(),
            user_skill_profile_id=profile.id,
            skill_id=s.get("skill_id", "SK-000001"),
            standard_name=s["standard_name"],
            primary_observed_term=s["standard_name"],
            observed_terms=[],
            mapping_status=s.get("mapping_status", "verified"),
            skill_type="TECHNICAL",
            proficiency_level=s.get("proficiency_level", "INTERMEDIATE"),
            proficiency_score=s.get("proficiency_score", 0.7),
            evidence_confidence=s.get("evidence_confidence", 1.0),
        )
        profile.skills.append(skill_entry)

    session.add(profile)
    await session.commit()
    return profile


# Test 1: Verify empty history returns zero items and empty list
@pytest.mark.anyio
async def test_01_empty_history(client: AsyncClient):
    unregistered_user_id = uuid.uuid4()
    response = await client.get(f"/analyses?user_id={unregistered_user_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


# Test 2: Verify listing multiple analyses returns expected metadata without child collections
@pytest.mark.anyio
async def test_02_listing_multiple_analyses_and_metadata(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind_prof = await _create_industry_profile(
            session=session,
            role_id=role_id,
            role_title="Senior Python Architect",
            requirements=[
                {
                    "skill_id": "SK-000001",
                    "standard_name": "Python",
                    "required_proficiency_level": "ADVANCED",
                    "required_proficiency_score": 0.8,
                    "demand_weight": 1.0,
                }
            ],
        )
        user_prof = await _create_user_profile(
            session=session,
            user_id=user_id,
            skills=[
                {
                    "skill_id": "SK-000001",
                    "standard_name": "Python",
                    "proficiency_level": "ADVANCED",
                    "proficiency_score": 0.8,
                    "evidence_confidence": 1.0,
                }
            ],
        )
        ind_id = ind_prof.id
        usr_id = user_prof.id

    # Create two analyses for this user
    for _ in range(2):
        create_resp = await client.post(
            "/analyses",
            json={
                "industry_profile_id": str(ind_id),
                "user_skill_profile_id": str(usr_id),
                "role_id": role_id,
            },
        )
        assert create_resp.status_code == 201

    # Fetch analysis history
    resp = await client.get(f"/analyses?user_id={user_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2

    for item in data["items"]:
        # Verify required metadata fields
        assert uuid.UUID(item["analysisId"])
        assert item["user_id"] == str(user_id)
        assert item["roleId"] == role_id
        assert item["roleName"] == "Senior Python Architect"
        assert item["status"] == "COMPLETED"
        assert isinstance(item["readinessScore"], float)
        assert item["readinessScore"] == 100.0
        assert item["createdAt"] is not None
        assert item["completedAt"] is not None

        # Verify heavy collections are excluded from history items
        assert "skill_results" not in item
        assert "priority_skills" not in item
        assert "prioritySkills" not in item
        assert "c04_payload" not in item
        assert "reports" not in item


# Test 3: Verify isolation between distinct users via query parameter and X-User-Id header
@pytest.mark.anyio
async def test_03_isolation_between_users(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    role_id_a = _generate_role_id()
    role_id_b = _generate_role_id()

    async with session_maker() as session:
        ind_a = await _create_industry_profile(
            session, role_id_a, "Role A", [{"standard_name": "Python"}]
        )
        ind_b = await _create_industry_profile(
            session, role_id_b, "Role B", [{"standard_name": "Java"}]
        )
        usr_a = await _create_user_profile(
            session, user_a, [{"standard_name": "Python"}]
        )
        usr_b = await _create_user_profile(session, user_b, [{"standard_name": "Java"}])
        ind_a_id, usr_a_id = ind_a.id, usr_a.id
        ind_b_id, usr_b_id = ind_b.id, usr_b.id

    # Create analysis for User A
    resp_a = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_a_id),
            "user_skill_profile_id": str(usr_a_id),
            "role_id": role_id_a,
        },
    )
    assert resp_a.status_code == 201
    analysis_a_id = resp_a.json()["analysisId"]

    # Create analysis for User B
    resp_b = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_b_id),
            "user_skill_profile_id": str(usr_b_id),
            "role_id": role_id_b,
        },
    )
    assert resp_b.status_code == 201
    analysis_b_id = resp_b.json()["analysisId"]

    # Query with user_id query parameter for User A
    get_a = await client.get(f"/analyses?user_id={user_a}")
    assert get_a.status_code == 200
    items_a = get_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["analysisId"] == analysis_a_id
    assert items_a[0]["user_id"] == str(user_a)

    # Query with user_id query parameter for User B
    get_b = await client.get(f"/analyses?user_id={user_b}")
    assert get_b.status_code == 200
    items_b = get_b.json()["items"]
    assert len(items_b) == 1
    assert items_b[0]["analysisId"] == analysis_b_id
    assert items_b[0]["user_id"] == str(user_b)

    # Verify authorization header X-User-Id yields identical isolation
    header_a = await client.get("/analyses", headers={"X-User-Id": str(user_a)})
    assert header_a.status_code == 200
    assert len(header_a.json()["items"]) == 1
    assert header_a.json()["items"][0]["analysisId"] == analysis_a_id

    header_b = await client.get("/analyses", headers={"X-User-Id": str(user_b)})
    assert header_b.status_code == 200
    assert len(header_b.json()["items"]) == 1
    assert header_b.json()["items"][0]["analysisId"] == analysis_b_id


# Test 4: Verify pagination with limit/offset and deterministic newest-first ordering
@pytest.mark.anyio
async def test_04_pagination_and_deterministic_ordering(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    base_time = datetime.now(UTC) - timedelta(hours=5)

    async with session_maker() as session:
        ind_prof = await _create_industry_profile(
            session, role_id, "Ordering Test Role", [{"standard_name": "SQL"}]
        )
        usr_prof = await _create_user_profile(
            session, user_id, [{"standard_name": "SQL"}]
        )
        snapshot_res = await session.execute(select(KnowledgeSnapshot))
        snapshot = snapshot_res.scalars().first()

        # Insert 4 analyses with distinct sequential timestamps
        analysis_ids = []
        for i in range(4):
            an = Analysis(
                analysis_id=uuid.uuid4(),
                user_id=user_id,
                user_skill_profile_id=usr_prof.id,
                industry_profile_id=ind_prof.id,
                snapshot_id=snapshot.snapshot_id,
                matching_method="RELATIONSHIP_AWARE",
                scoring_config_version="1.0",
                readiness_score=float(70 + i),
                status="COMPLETED",
                started_at=base_time + timedelta(minutes=i * 10),
                completed_at=base_time + timedelta(minutes=i * 10 + 2),
            )
            session.add(an)
            analysis_ids.append(an.analysis_id)
        await session.commit()

    # The newest analysis is the last one created (index 3)
    expected_order = [str(aid) for aid in reversed(analysis_ids)]

    # Page 1: limit 2, offset 0
    page1 = await client.get(f"/analyses?user_id={user_id}&limit=2&offset=0")
    assert page1.status_code == 200
    data1 = page1.json()
    assert data1["total"] == 4
    assert data1["limit"] == 2
    assert data1["offset"] == 0
    assert len(data1["items"]) == 2
    assert [item["analysisId"] for item in data1["items"]] == expected_order[:2]

    # Page 2: limit 2, offset 2
    page2 = await client.get(f"/analyses?user_id={user_id}&limit=2&offset=2")
    assert page2.status_code == 200
    data2 = page2.json()
    assert data2["total"] == 4
    assert data2["limit"] == 2
    assert data2["offset"] == 2
    assert len(data2["items"]) == 2
    assert [item["analysisId"] for item in data2["items"]] == expected_order[2:]


# Test 5: Verify status filtering isolates analyses by status
@pytest.mark.anyio
async def test_05_status_filtering(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind_prof = await _create_industry_profile(
            session, role_id, "Status Filter Role", [{"standard_name": "Docker"}]
        )
        usr_prof = await _create_user_profile(
            session, user_id, [{"standard_name": "Docker"}]
        )
        snapshot_res = await session.execute(select(KnowledgeSnapshot))
        snapshot = snapshot_res.scalars().first()

        # Insert 1 COMPLETED, 1 FAILED, 1 PENDING
        completed = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr_prof.id,
            industry_profile_id=ind_prof.id,
            snapshot_id=snapshot.snapshot_id,
            status=AnalysisStatus.COMPLETED.value,
            readiness_score=85.0,
            started_at=datetime.now(UTC) - timedelta(minutes=30),
            completed_at=datetime.now(UTC) - timedelta(minutes=28),
        )
        failed = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr_prof.id,
            industry_profile_id=ind_prof.id,
            snapshot_id=snapshot.snapshot_id,
            status=AnalysisStatus.FAILED.value,
            error_message="Profile validation failed",
            started_at=datetime.now(UTC) - timedelta(minutes=20),
            completed_at=datetime.now(UTC) - timedelta(minutes=19),
        )
        pending = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr_prof.id,
            industry_profile_id=ind_prof.id,
            snapshot_id=snapshot.snapshot_id,
            status=AnalysisStatus.PENDING.value,
            started_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        session.add_all([completed, failed, pending])
        await session.commit()

        completed_id = str(completed.analysis_id)
        failed_id = str(failed.analysis_id)
        pending_id = str(pending.analysis_id)

    # Filter COMPLETED
    res_completed = await client.get(f"/analyses?user_id={user_id}&status=COMPLETED")
    assert res_completed.status_code == 200
    data_completed = res_completed.json()
    assert data_completed["total"] == 1
    assert data_completed["items"][0]["analysisId"] == completed_id

    # Filter completed (lowercase test)
    res_completed_lower = await client.get(
        f"/analyses?user_id={user_id}&status=completed"
    )
    assert res_completed_lower.status_code == 200
    assert res_completed_lower.json()["total"] == 1

    # Filter FAILED
    res_failed = await client.get(f"/analyses?user_id={user_id}&status=FAILED")
    assert res_failed.status_code == 200
    data_failed = res_failed.json()
    assert data_failed["total"] == 1
    assert data_failed["items"][0]["analysisId"] == failed_id
    assert data_failed["items"][0]["readinessScore"] is None

    # Filter PENDING
    res_pending = await client.get(f"/analyses?user_id={user_id}&status=PENDING")
    assert res_pending.status_code == 200
    data_pending = res_pending.json()
    assert data_pending["total"] == 1
    assert data_pending["items"][0]["analysisId"] == pending_id
    assert data_pending["items"][0]["readinessScore"] is None
    assert data_pending["items"][0]["completedAt"] is None

    # Filter unknown status returns empty result
    res_unknown = await client.get(f"/analyses?user_id={user_id}&status=UNKNOWN_STATUS")
    assert res_unknown.status_code == 200
    assert res_unknown.json()["total"] == 0
    assert res_unknown.json()["items"] == []


# Test 6: Verify role filtering filters correctly by role identifier
@pytest.mark.anyio
async def test_06_role_filtering(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_1 = _generate_role_id()
    role_2 = _generate_role_id()

    async with session_maker() as session:
        ind_1 = await _create_industry_profile(
            session,
            role_1,
            "Frontend Dev",
            [{"skill_id": "SK-000001", "standard_name": "CSS"}],
        )
        ind_2 = await _create_industry_profile(
            session,
            role_2,
            "Backend Dev",
            [{"skill_id": "SK-000002", "standard_name": "Rust"}],
        )
        usr = await _create_user_profile(
            session,
            user_id,
            [
                {"skill_id": "SK-000001", "standard_name": "CSS"},
                {"skill_id": "SK-000002", "standard_name": "Rust"},
            ],
        )
        ind_1_id, ind_2_id, usr_id = ind_1.id, ind_2.id, usr.id

    # Create analysis for Role 1
    resp1 = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_1_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_1,
        },
    )
    assert resp1.status_code == 201, resp1.text

    # Create analysis for Role 2
    resp2 = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_2_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_2,
        },
    )
    assert resp2.status_code == 201

    # Filter by Role 1
    res_role1 = await client.get(f"/analyses?user_id={user_id}&role_id={role_1}")
    assert res_role1.status_code == 200
    data_role1 = res_role1.json()
    assert data_role1["total"] == 1
    assert data_role1["items"][0]["roleId"] == role_1
    assert data_role1["items"][0]["roleName"] == "Frontend Dev"

    # Filter by nonexistent role
    res_none = await client.get(f"/analyses?user_id={user_id}&role_id=RL-999999")
    assert res_none.status_code == 200
    assert res_none.json()["total"] == 0


# Test 7: Verify invalid pagination and query values return 422 Unprocessable Entity
@pytest.mark.anyio
async def test_07_invalid_pagination_values(client: AsyncClient):
    # Limit less than 1
    resp = await client.get("/analyses?limit=0")
    assert resp.status_code == 422

    # Negative limit
    resp = await client.get("/analyses?limit=-5")
    assert resp.status_code == 422

    # Limit greater than 100
    resp = await client.get("/analyses?limit=101")
    assert resp.status_code == 422

    # Negative offset
    resp = await client.get("/analyses?offset=-1")
    assert resp.status_code == 422

    # Non-integer limit
    resp = await client.get("/analyses?limit=notanumber")
    assert resp.status_code == 422

    # Invalid user_id UUID
    resp = await client.get("/analyses?user_id=invalid-uuid-string")
    assert resp.status_code == 422


# Test 8: Verify correct metadata representation for completed, pending, and failed states
@pytest.mark.anyio
async def test_08_correct_metadata_for_different_statuses(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session, role_id, "Platform Engineer", [{"standard_name": "Kubernetes"}]
        )
        usr = await _create_user_profile(
            session, user_id, [{"standard_name": "Kubernetes"}]
        )
        snapshot_res = await session.execute(select(KnowledgeSnapshot))
        snapshot = snapshot_res.scalars().first()

        now = datetime.now(UTC)
        comp = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr.id,
            industry_profile_id=ind.id,
            snapshot_id=snapshot.snapshot_id,
            status="COMPLETED",
            readiness_score=92.5,
            started_at=now - timedelta(minutes=5),
            completed_at=now - timedelta(minutes=4),
        )
        pend = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr.id,
            industry_profile_id=ind.id,
            snapshot_id=snapshot.snapshot_id,
            status="PENDING",
            readiness_score=None,
            started_at=now - timedelta(minutes=3),
            completed_at=None,
        )
        fail = Analysis(
            analysis_id=uuid.uuid4(),
            user_id=user_id,
            user_skill_profile_id=usr.id,
            industry_profile_id=ind.id,
            snapshot_id=snapshot.snapshot_id,
            status="FAILED",
            error_message="Snapshot lookup timeout",
            readiness_score=None,
            started_at=now - timedelta(minutes=2),
            completed_at=now - timedelta(minutes=1),
        )
        session.add_all([comp, pend, fail])
        await session.commit()

    res = await client.get(f"/analyses?user_id={user_id}")
    assert res.status_code == 200
    items = {item["status"]: item for item in res.json()["items"]}

    # Completed metadata assertions
    assert items["COMPLETED"]["readinessScore"] == 92.5
    assert items["COMPLETED"]["completedAt"] is not None
    assert items["COMPLETED"]["roleId"] == role_id
    assert items["COMPLETED"]["roleName"] == "Platform Engineer"

    # Pending metadata assertions
    assert items["PENDING"]["readinessScore"] is None
    assert items["PENDING"]["completedAt"] is None
    assert items["PENDING"]["roleId"] == role_id
    assert items["PENDING"]["roleName"] == "Platform Engineer"

    # Failed metadata assertions
    assert items["FAILED"]["readinessScore"] is None
    assert items["FAILED"]["completedAt"] is not None
    assert items["FAILED"]["roleId"] == role_id
    assert items["FAILED"]["roleName"] == "Platform Engineer"


# Test 9: Verify existing single analysis detail and C04 retrieval endpoints remain unaffected
@pytest.mark.anyio
async def test_09_no_changes_to_detail_and_c04_endpoints(client: AsyncClient):
    session_maker = get_sessionmaker()
    user_id = uuid.uuid4()
    role_id = _generate_role_id()

    async with session_maker() as session:
        ind = await _create_industry_profile(
            session, role_id, "Cloud Architect", [{"standard_name": "Terraform"}]
        )
        usr = await _create_user_profile(
            session, user_id, [{"standard_name": "Terraform"}]
        )
        ind_id, usr_id = ind.id, usr.id

    create_resp = await client.post(
        "/analyses",
        json={
            "industry_profile_id": str(ind_id),
            "user_skill_profile_id": str(usr_id),
            "role_id": role_id,
        },
    )
    assert create_resp.status_code == 201
    analysis_id = create_resp.json()["analysisId"]

    # Retrieve detail endpoint
    detail_resp = await client.get(f"/analyses/{analysis_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["analysis_id"] == analysis_id
    assert "skill_results" in detail_data
    assert "priority_skills" in detail_data
    assert "c04_payload" in detail_data

    # Retrieve downstream C04 payload endpoint
    c04_resp = await client.get(f"/analyses/{analysis_id}/c04")
    assert c04_resp.status_code == 200
    c04_data = c04_resp.json()
    assert c04_data["analysisId"] == analysis_id
    assert "prioritySkills" in c04_data
    assert "readinessScore" in c04_data


# Test 10: Verify both /analyses and /readiness/analyses mount paths work identically
@pytest.mark.anyio
async def test_10_readiness_prefix_routing(client: AsyncClient):
    user_id = uuid.uuid4()
    resp_standard = await client.get(f"/analyses?user_id={user_id}")
    resp_prefixed = await client.get(f"/readiness/analyses?user_id={user_id}")

    assert resp_standard.status_code == 200
    assert resp_prefixed.status_code == 200
    assert resp_standard.json() == resp_prefixed.json()
