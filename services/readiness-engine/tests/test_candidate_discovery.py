import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.models.analysis import AnalysisStatus, CandidateDiscoveryRun
from app.models.cache import CachedSkillEmbedding
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    UserSkillProfile,
    UserSkillProfileSkill,
)
from app.schemas.analysis import AnalysisCreateRequest
from app.services.analysis_service import AnalysisService
from app.services.candidate_discovery_service import (
    CandidateDiscoveryService,
    CandidatePair,
    compute_cosine_similarity,
    filter_and_rank_candidates,
    generate_candidate_skill_pairs,
    submit_candidate_to_ssks,
)


# 1. Cosine similarity calculation: normal cases
def test_01_cosine_similarity_normal_cases():
    # Identical vectors
    assert compute_cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    # Orthogonal vectors
    assert compute_cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    # Opposite vectors
    assert compute_cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)
    # Scaled vectors
    sim = compute_cosine_similarity([3.0, 4.0], [4.0, 3.0])
    assert sim == pytest.approx(24.0 / 25.0)


# 1. Cosine similarity calculation: zero vectors
def test_02_cosine_similarity_zero_vectors():
    # One zero vector
    assert compute_cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    # Both zero vectors
    assert compute_cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


# 1. Cosine similarity calculation: incompatible and invalid vectors
def test_03_cosine_similarity_incompatible_and_invalid():
    # Dimension mismatch
    assert compute_cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) is None
    # Expected dim mismatch
    assert compute_cosine_similarity([1.0, 2.0], [1.0, 2.0], expected_dim=384) is None
    # Non-finite values
    assert compute_cosine_similarity([float("nan"), 1.0], [1.0, 2.0]) is None
    assert compute_cosine_similarity([float("inf"), 1.0], [1.0, 2.0]) is None
    # None or empty inputs
    assert compute_cosine_similarity(None, [1.0, 2.0]) is None
    assert compute_cosine_similarity([], []) is None


# 2. Configurable threshold behaviour
def test_04_configurable_threshold_behaviour():
    pairs = [
        CandidatePair("SK-01", "SK-11", 0.7499),
        CandidatePair("SK-02", "SK-12", 0.7500),
        CandidatePair("SK-03", "SK-13", 0.8500),
    ]

    # Default threshold 0.75
    res_default = filter_and_rank_candidates(pairs, threshold=0.75, max_candidates=10)
    assert len(res_default) == 2
    assert {c.source_skill_id for c in res_default} == {"SK-02", "SK-03"}

    # Higher threshold 0.80
    res_higher = filter_and_rank_candidates(pairs, threshold=0.80, max_candidates=10)
    assert len(res_higher) == 1
    assert res_higher[0].source_skill_id == "SK-03"


# 3. Exclusion of identical and verified-resolvable pairs
def test_05_exclusion_of_identical_and_verified_relationships():
    unmatched_stu = ["SK-01", "SK-02", "SK-03"]
    unmatched_req = ["SK-01", "SK-04", "SK-05"]

    # SK-02 and SK-04 have a verified relationship in the knowledge snapshot
    verified_pairs = {("SK-02", "SK-04"), ("SK-04", "SK-02")}

    pairs = generate_candidate_skill_pairs(
        unmatched_student_skill_ids=unmatched_stu,
        unmatched_requirement_skill_ids=unmatched_req,
        verified_relationship_pairs=verified_pairs,
    )

    # Identical pair (SK-01, SK-01) excluded
    assert ("SK-01", "SK-01") not in pairs
    # Verified pair (SK-02, SK-04) excluded
    assert ("SK-02", "SK-04") not in pairs
    assert ("SK-04", "SK-02") not in pairs

    # Remaining valid pairs included
    assert ("SK-02", "SK-05") in pairs
    assert ("SK-03", "SK-04") in pairs
    assert ("SK-03", "SK-05") in pairs


# 4. Candidate ranking and maximum-candidate limits
def test_06_candidate_ranking_and_max_limits():
    pairs = [
        CandidatePair("SK-02", "SK-10", 0.85),
        CandidatePair("SK-01", "SK-10", 0.85),  # Tie with SK-02, SK-01 comes first alphabetically
        CandidatePair("SK-03", "SK-10", 0.95),  # Highest
        CandidatePair("SK-04", "SK-10", 0.78),  # Lowest
    ]

    # Rank with max limit 2
    ranked = filter_and_rank_candidates(pairs, threshold=0.75, max_candidates=2)
    assert len(ranked) == 2
    assert ranked[0].source_skill_id == "SK-03"
    assert ranked[0].similarity_score == 0.95
    # Tie-break alphabetically between SK-01 and SK-02
    assert ranked[1].source_skill_id == "SK-01"
    assert ranked[1].similarity_score == 0.85


# 5. Missing embeddings and incompatible models handled safely
@pytest.mark.anyio
async def test_07_missing_embeddings_and_incompatible_models():
    service = CandidateDiscoveryService()

    analysis_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session_factory = MagicMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    # Mock DB query to return embedding only for SK-01, not SK-02
    mock_emb = CachedSkillEmbedding(
        snapshot_id=snapshot_id,
        skill_id="SK-01",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimension=384,
        embedding_text_hash="hash1",
        embedding_text="text1",
        embedding=[0.1] * 384,
    )
    mock_execute_res = MagicMock()
    mock_execute_res.scalars.return_value.all.return_value = [mock_emb]
    mock_session.execute.return_value = mock_execute_res

    run = await service.run_candidate_discovery(
        analysis_id=analysis_id,
        snapshot_id=snapshot_id,
        unmatched_requirement_skill_ids=["SK-02"],
        unmatched_student_skill_ids=["SK-01"],
        verified_relationship_pairs=set(),
        session_factory=mock_session_factory,
    )

    # Missing embedding for SK-02 skipped without error
    assert run is not None
    assert run.status == "COMPLETED"
    assert run.candidates_submitted_count == 0


# 6 & 7. Correct SSKS REST API contract and successful submission
@pytest.mark.anyio
async def test_08_ssks_api_contract_and_successful_submission():
    captured_requests = []

    def mock_handler(request: httpx.Request):
        captured_requests.append(request)
        return httpx.Response(
            status_code=201,
            json={
                "candidate_relationship_id": "CR-000001",
                "source_skill_id": "SK-01",
                "target_skill_id": "SK-02",
                "proposed_relationship_type": "RELATED_TO",
                "confidence_score": 0.88,
                "review_status": "PENDING",
            },
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        analysis_id = uuid.uuid4()
        success, outcome = await submit_candidate_to_ssks(
            client=client,
            ssks_base_url="http://ssks:8005",
            source_skill_id="SK-01",
            target_skill_id="SK-02",
            similarity_score=0.88123,
            analysis_id=analysis_id,
        )

    assert success is True
    assert outcome == "CREATED"
    assert len(captured_requests) == 1

    req = captured_requests[0]
    assert req.method == "POST"
    assert req.url.path == "/ssks/candidates/relationships"

    import json
    body = json.loads(req.content.decode())
    assert body["source_skill_id"] == "SK-01"
    assert body["target_skill_id"] == "SK-02"
    assert body["proposed_relationship_type"] == "RELATED_TO"
    assert body["confidence_score"] == 0.8812
    assert body["source_id"] is None
    assert "C03" in body["review_note"]
    assert str(analysis_id) in body["review_note"]


# 7. Unsuccessful API responses handled safely
@pytest.mark.anyio
async def test_09_ssks_api_unsuccessful_responses():
    # 400 Bad Request
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(status_code=400, json={"detail": "Bad request"}))
    ) as client:
        success, outcome = await submit_candidate_to_ssks(
            client=client,
            ssks_base_url="http://ssks:8005",
            source_skill_id="SK-01",
            target_skill_id="SK-02",
            similarity_score=0.80,
            analysis_id=uuid.uuid4(),
            max_retries=1,
        )
        assert success is False
        assert outcome == "HTTP_400"

    # 409 Conflict (already exists in SSKS)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(status_code=409, json={"detail": "A pending candidate relationship already exists"}))
    ) as client:
        success, outcome = await submit_candidate_to_ssks(
            client=client,
            ssks_base_url="http://ssks:8005",
            source_skill_id="SK-01",
            target_skill_id="SK-02",
            similarity_score=0.80,
            analysis_id=uuid.uuid4(),
            max_retries=1,
        )
        # Treated as gracefully handled duplicate
        assert success is True
        assert outcome == "ALREADY_EXISTS"


# 8. Timeout and retry behaviour without duplicate submissions
@pytest.mark.anyio
async def test_10_retry_behaviour():
    call_count = 0

    def mock_flaky_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectTimeout("Connection timed out")
        elif call_count == 2:
            # On retry, SSKS already received previous attempt and returns 409 Conflict
            return httpx.Response(
                status_code=409,
                json={"detail": "A pending candidate relationship already exists"},
            )
        return httpx.Response(status_code=201, json={"status": "ok"})

    transport = httpx.MockTransport(mock_flaky_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        success, outcome = await submit_candidate_to_ssks(
            client=client,
            ssks_base_url="http://ssks:8005",
            source_skill_id="SK-01",
            target_skill_id="SK-02",
            similarity_score=0.85,
            analysis_id=uuid.uuid4(),
            max_retries=3,
        )

    # Retry recognized 409 conflict and succeeded gracefully
    assert success is True
    assert outcome == "ALREADY_EXISTS"
    assert call_count == 2


# 9. Run status and submitted count persistence
@pytest.mark.anyio
async def test_11_run_status_and_count_persistence():
    service = CandidateDiscoveryService()
    analysis_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session_factory = MagicMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    vec_stu = [0.5] * 384
    vec_req = [0.5] * 384
    mock_embs = [
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-01",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h1",
            embedding_text="t1",
            embedding=vec_stu,
        ),
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-02",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h2",
            embedding_text="t2",
            embedding=vec_req,
        ),
    ]
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = mock_embs
    mock_session.execute.return_value = mock_res

    mock_client = AsyncMock()
    mock_response = MagicMock(status_code=201)
    mock_client.post.return_value = mock_response

    run = await service.run_candidate_discovery(
        analysis_id=analysis_id,
        snapshot_id=snapshot_id,
        unmatched_requirement_skill_ids=["SK-02"],
        unmatched_student_skill_ids=["SK-01"],
        verified_relationship_pairs=set(),
        http_client=mock_client,
        session_factory=mock_session_factory,
    )

    assert run is not None
    assert run.status == "COMPLETED"
    assert run.candidates_submitted_count == 1
    assert run.completed_at is not None


# 10. Partial success when some submissions fail
@pytest.mark.anyio
async def test_12_partial_success_when_some_submissions_fail():
    service = CandidateDiscoveryService()
    analysis_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session_factory = MagicMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    # Mock 3 skills: SK-STU with SK-REQ1 and SK-REQ2
    mock_embs = [
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-STU",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h",
            embedding_text="t",
            embedding=[0.5] * 384,
        ),
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-REQ1",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h1",
            embedding_text="t1",
            embedding=[0.5] * 384,
        ),
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-REQ2",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h2",
            embedding_text="t2",
            embedding=[0.5] * 384,
        ),
    ]
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = mock_embs
    mock_session.execute.return_value = mock_res

    # First submission succeeds (201), second submission fails (500)
    async def mock_post(url, json):
        if json["target_skill_id"] == "SK-REQ1":
            return MagicMock(status_code=201)
        return MagicMock(status_code=500, text="Internal Server Error")

    mock_client = AsyncMock()
    mock_client.post.side_effect = mock_post

    run = await service.run_candidate_discovery(
        analysis_id=analysis_id,
        snapshot_id=snapshot_id,
        unmatched_requirement_skill_ids=["SK-REQ1", "SK-REQ2"],
        unmatched_student_skill_ids=["SK-STU"],
        verified_relationship_pairs=set(),
        http_client=mock_client,
        session_factory=mock_session_factory,
    )

    assert run is not None
    assert run.status == "PARTIALLY_COMPLETED"
    assert run.candidates_submitted_count == 1


# 11 & 12. Discovery failure does not invalidate analysis and scoring is unaffected
@pytest.mark.anyio
async def test_13_discovery_failure_does_not_affect_analysis():
    # Verify that even if CandidateDiscoveryService fails with an exception,
    # run_analysis returns normal results without raising
    mock_discovery = AsyncMock()
    mock_discovery.run_candidate_discovery.side_effect = RuntimeError("SSKS service unavailable")

    analysis_service = AnalysisService(candidate_discovery_service=mock_discovery)

    # Mock user profile and industry profile
    user_uuid = uuid.uuid4()
    mock_user_prof = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=user_uuid,
        skills=[
            UserSkillProfileSkill(
                id=uuid.uuid4(),
                skill_id="SK-000878",
                standard_name="MySQL",
                proficiency_score=0.8,
                evidence_confidence=0.9,
                proficiency_level="ADVANCED",
                mapping_status="RESOLVED",
            )
        ],
    )
    req = AnalysisCreateRequest(
        user_id=user_uuid,
        role_id="RL-000003",
        matching_method="RELATIONSHIP_AWARE",
    )
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_ind_prof = IndustryProfile(
        id=uuid.uuid4(),
        role_id="RL-000003",
        role_name="Software Testing Intern",
        requirements=[
            IndustryProfileRequirement(
                id=uuid.uuid4(),
                skill_id="SK-000499",
                standard_name="SQL",
                demand_weight=1.0,
                required_proficiency_score=0.6,
                required_proficiency_level="INTERMEDIATE",
                mapping_status="RESOLVED",
            )
        ],
    )

    mock_snapshot = MagicMock(snapshot_id=uuid.uuid4())

    with (
        patch("app.services.analysis_service.resolve_user_profile", return_value=mock_user_prof),
        patch("app.services.analysis_service.resolve_industry_profile", return_value=mock_ind_prof),
        patch("app.services.analysis_service.resolve_snapshot", return_value=mock_snapshot),
        patch("app.services.analysis_service.load_snapshot_knowledge", return_value=([], [])),
        patch("app.services.analysis_service.validate_industry_profile"),
        patch("app.services.analysis_service.validate_user_skill_profile"),
    ):
        analysis, c04_payload = await analysis_service.run_analysis(
            session=mock_session,
            request=req,
            enable_candidate_discovery=True,
        )

    # Analysis completed normally despite discovery service exception
    assert analysis.status == AnalysisStatus.COMPLETED.value
    assert "readinessScore" in c04_payload
    assert "prioritySkills" in c04_payload


# 12. Readiness scores, matching outputs, gap results, and reports remain strictly unchanged
@pytest.mark.anyio
async def test_14_readiness_scoring_and_report_outputs_unchanged():
    mock_discovery = AsyncMock()
    analysis_service = AnalysisService(candidate_discovery_service=mock_discovery)

    user_uuid = uuid.uuid4()
    mock_user_prof = UserSkillProfile(
        id=uuid.uuid4(),
        user_id=user_uuid,
        skills=[
            UserSkillProfileSkill(
                id=uuid.uuid4(),
                skill_id="SK-000878",
                standard_name="MySQL",
                proficiency_score=0.8,
                evidence_confidence=0.9,
                proficiency_level="ADVANCED",
                mapping_status="RESOLVED",
            )
        ],
    )
    req = AnalysisCreateRequest(
        user_id=user_uuid,
        role_id="RL-000003",
        matching_method="RELATIONSHIP_AWARE",
    )
    mock_ind_prof = IndustryProfile(
        id=uuid.uuid4(),
        role_id="RL-000003",
        role_name="Software Testing Intern",
        requirements=[
            IndustryProfileRequirement(
                id=uuid.uuid4(),
                skill_id="SK-000499",
                standard_name="SQL",
                demand_weight=1.0,
                required_proficiency_score=0.6,
                required_proficiency_level="INTERMEDIATE",
                mapping_status="RESOLVED",
            )
        ],
    )
    mock_snapshot = MagicMock(snapshot_id=uuid.uuid4())

    with (
        patch("app.services.analysis_service.resolve_user_profile", return_value=mock_user_prof),
        patch("app.services.analysis_service.resolve_industry_profile", return_value=mock_ind_prof),
        patch("app.services.analysis_service.resolve_snapshot", return_value=mock_snapshot),
        patch("app.services.analysis_service.load_snapshot_knowledge", return_value=([], [])),
        patch("app.services.analysis_service.validate_industry_profile"),
        patch("app.services.analysis_service.validate_user_skill_profile"),
    ):
        analysis_off, payload_off = await analysis_service.run_analysis(
            session=AsyncMock(add=MagicMock()),
            request=req,
            enable_candidate_discovery=False,
        )
        analysis_on, payload_on = await analysis_service.run_analysis(
            session=AsyncMock(add=MagicMock()),
            request=req,
            enable_candidate_discovery=True,
        )

    # Readiness scores and payload outputs are strictly identical
    assert analysis_off.readiness_score == analysis_on.readiness_score
    assert payload_off["readinessScore"] == payload_on["readinessScore"]
    assert payload_off["prioritySkills"] == payload_on["prioritySkills"]
    assert payload_off["roleId"] == payload_on["roleId"]


# 13. Verify no individual candidate records are written to C03 database
@pytest.mark.anyio
async def test_15_no_individual_candidate_records_written():
    service = CandidateDiscoveryService()
    analysis_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()

    added_objects = []
    mock_session = AsyncMock()
    mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

    mock_session_factory = MagicMock(return_value=AsyncMock())
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_embs = [
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-01",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h1",
            embedding_text="t1",
            embedding=[0.5] * 384,
        ),
        CachedSkillEmbedding(
            snapshot_id=snapshot_id,
            skill_id="SK-02",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            embedding_text_hash="h2",
            embedding_text="t2",
            embedding=[0.5] * 384,
        ),
    ]
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = mock_embs
    mock_session.execute.return_value = mock_res

    mock_client = AsyncMock()
    mock_client.post.return_value = MagicMock(status_code=201)

    await service.run_candidate_discovery(
        analysis_id=analysis_id,
        snapshot_id=snapshot_id,
        unmatched_requirement_skill_ids=["SK-02"],
        unmatched_student_skill_ids=["SK-01"],
        verified_relationship_pairs=set(),
        http_client=mock_client,
        session_factory=mock_session_factory,
    )

    # Only CandidateDiscoveryRun was added to session, no individual candidate rows
    assert len(added_objects) == 1
    assert isinstance(added_objects[0], CandidateDiscoveryRun)
