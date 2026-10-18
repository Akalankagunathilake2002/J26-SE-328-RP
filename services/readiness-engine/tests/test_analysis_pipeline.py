import uuid

import pytest
from httpx import AsyncClient

from app.schemas.analysis import AnalysisCreateRequest
from app.services.analysis_service import AnalysisService


@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    yield
    from app.db.session import dispose_engine

    await dispose_engine()


@pytest.mark.anyio
async def test_01_successful_post_analysis(client: AsyncClient):
    # Initiate analysis via HTTP POST /analyses with role identifier RL-000003
    payload = {
        "role_id": "RL-000003",
        "matching_method": "RELATIONSHIP_AWARE",
        "scoring_config_version": "1.0",
    }
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Validate C04 contract top-level fields
    assert "analysisId" in data
    assert "user_id" in data
    assert "roleId" in data
    assert "roleName" in data
    assert "readinessScore" in data
    assert "prioritySkills" in data

    assert data["roleId"] == "RL-000003"
    assert data["roleName"] == "Software Testing Intern"
    assert isinstance(data["prioritySkills"], list)
    assert len(data["prioritySkills"]) > 0


@pytest.mark.anyio
async def test_02_prefixed_post_analysis_route(client: AsyncClient):
    # Verify endpoint works under service prefix /readiness/analyses
    payload = {
        "role_id": "RL-000003",
        "matching_method": "EXACT_BASELINE",
    }
    response = await client.post("/readiness/analyses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["roleId"] == "RL-000003"


@pytest.mark.anyio
async def test_03_c04_response_exact_field_names_and_casing(client: AsyncClient):
    # External JSON contract to-C04 structure and casing validation
    response = await client.post("/analyses", json={"role_id": "RL-000003"})
    assert response.status_code == 201
    c04 = response.json()

    expected_top_keys = {
        "analysisId",
        "user_id",
        "roleId",
        "roleName",
        "readinessScore",
        "prioritySkills",
    }
    assert set(c04.keys()) == expected_top_keys

    expected_item_keys = {
        "skillId",
        "skillName",
        "priorityRank",
        "learningPriority",
        "gap",
    }
    for item in c04["prioritySkills"]:
        assert set(item.keys()) == expected_item_keys
        assert isinstance(item["skillId"], str)
        assert isinstance(item["skillName"], str)
        assert isinstance(item["priorityRank"], int)
        assert isinstance(item["learningPriority"], (int, float))
        assert isinstance(item["gap"], (int, float))


@pytest.mark.anyio
async def test_04_execution_order_and_intermediate_handoff(client: AsyncClient):
    # Verify proper handoff: matching -> readiness -> gaps -> priorities
    res = await client.post("/analyses", json={"role_id": "RL-000003"})
    assert res.status_code == 201
    analysis_id = res.json()["analysisId"]

    # Retrieve full diagnostic record
    detail_res = await client.get(f"/analyses/{analysis_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert detail["status"] == "COMPLETED"
    assert detail["completed_at"] is not None
    assert detail["error_message"] is None
    assert len(detail["skill_results"]) == 5
    assert len(detail["priority_skills"]) == 5

    # Check intermediate handoff values on per-skill result
    first_skill = detail["skill_results"][0]
    assert first_skill["coverage_credit"] is not None
    assert first_skill["satisfaction"] is not None
    assert first_skill["gap"] is not None
    assert first_skill["result_status"] in ("MISSING", "PARTIALLY_COVERED", "COVERED")


@pytest.mark.anyio
async def test_05_priority_ordering_and_sequential_ranks(client: AsyncClient):
    # Priorities must be strictly descending with 1-based ranks
    res = await client.post("/analyses", json={"role_id": "RL-000003"})
    assert res.status_code == 201
    priority_skills = res.json()["prioritySkills"]

    priorities = [p["learningPriority"] for p in priority_skills]
    ranks = [p["priorityRank"] for p in priority_skills]

    assert priorities == sorted(priorities, reverse=True)
    assert ranks == list(range(1, len(priority_skills) + 1))


@pytest.mark.anyio
async def test_06_database_persistence_and_retrieval(client: AsyncClient):
    # Verify analysis is persisted and retrievable via GET /analyses/{id} and /c04
    post_res = await client.post("/analyses", json={"role_id": "RL-000003"})
    assert post_res.status_code == 201
    analysis_id = post_res.json()["analysisId"]

    # 1. Detail endpoint
    detail_res = await client.get(f"/analyses/{analysis_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["analysis_id"] == analysis_id
    assert detail_res.json()["c04_payload"] is not None

    # 2. C04 endpoint
    c04_res = await client.get(f"/analyses/{analysis_id}/c04")
    assert c04_res.status_code == 200
    assert c04_res.json()["analysisId"] == analysis_id


@pytest.mark.anyio
async def test_07_invalid_role_reference_returns_400(client: AsyncClient):
    # Non-existent role ID raises validation error with 400 Bad Request
    payload = {"role_id": "NON-EXISTENT-ROLE-9999"}
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 400
    assert "could not be resolved" in response.json()["detail"]


@pytest.mark.anyio
async def test_08_invalid_matching_method_returns_400(client: AsyncClient):
    # Unsupported matching method is rejected
    payload = {
        "role_id": "RL-000003",
        "matching_method": "INVALID_METHOD",
    }
    response = await client.post("/analyses", json=payload)
    assert response.status_code == 400
    assert "Unsupported matching method" in response.json()["detail"]


@pytest.mark.anyio
async def test_09_nonexistent_analysis_returns_404(client: AsyncClient):
    # Fetching a non-existent analysis returns 404
    random_id = uuid.uuid4()
    response = await client.get(f"/analyses/{random_id}")
    assert response.status_code == 404
    assert f"Analysis with ID '{random_id}' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_10_reproducibility_across_multiple_runs(client: AsyncClient):
    # Repeated runs with identical inputs produce identical numerical scores and ranks
    payload = {
        "role_id": "RL-000003",
        "matching_method": "RELATIONSHIP_AWARE",
        "scoring_config_version": "1.0",
    }
    run1 = await client.post("/analyses", json=payload)
    run2 = await client.post("/analyses", json=payload)

    assert run1.status_code == 201
    assert run2.status_code == 201

    data1 = run1.json()
    data2 = run2.json()

    assert data1["readinessScore"] == data2["readinessScore"]
    assert len(data1["prioritySkills"]) == len(data2["prioritySkills"])
    for s1, s2 in zip(data1["prioritySkills"], data2["prioritySkills"], strict=True):
        assert s1["skillId"] == s2["skillId"]
        assert s1["priorityRank"] == s2["priorityRank"]
        assert s1["learningPriority"] == s2["learningPriority"]
        assert s1["gap"] == s2["gap"]


@pytest.mark.anyio
async def test_11_failure_marks_analysis_failed_in_database(monkeypatch):
    # If algorithm execution fails, transaction rolls back and records status FAILED
    from app.db.session import get_sessionmaker

    service = AnalysisService()

    # Intentionally trigger an error in match_skills
    def broken_match(*args, **kwargs):
        raise RuntimeError("Simulated algorithm computation error")

    monkeypatch.setattr("app.services.analysis_service.match_skills", broken_match)

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        req = AnalysisCreateRequest(
            role_id="RL-000003",
            matching_method="RELATIONSHIP_AWARE",
        )
        with pytest.raises(RuntimeError, match="Simulated algorithm computation error"):
            await service.run_analysis(session, req)

        # Confirm the failed analysis is recorded in the DB with status FAILED
        from sqlalchemy import select

        from app.models.analysis import Analysis

        stmt = select(Analysis).order_by(Analysis.started_at.desc())
        res = await session.execute(stmt)
        latest_analysis = res.scalars().first()

        assert latest_analysis is not None
        assert latest_analysis.status == "FAILED"
        assert "Simulated algorithm computation error" in (
            latest_analysis.error_message or ""
        )
