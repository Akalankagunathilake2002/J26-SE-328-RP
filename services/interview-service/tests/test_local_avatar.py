"""Local avatar provider, video proxy, STT error handling and ID validation.

Runs without PostgreSQL, Docker or the avatar engine: the engine is faked with an
httpx MockTransport and the database dependency is overridden.
"""
import shutil
import subprocess

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.services.avatar_service import is_safe_video_name
from app.services.stt_service import SpeechToTextError, SpeechToTextService

VIDEO = b"\x00\x00\x00\x18ftypmp42" + b"x" * 1000
_RealAsyncClient = httpx.AsyncClient


def fake_engine(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/avatars":
        return httpx.Response(200, json=[{"name": "elena"}, {"name": "sample"}])
    if path == "/api/speak":
        return httpx.Response(200, json={"job": "abc123def456"})
    if path == "/api/jobs/abc123def456":
        return httpx.Response(200, json={"id": "abc123def456", "status": "done", "message": "Ready.",
                                         "result": {"url": "/media/outputs/elena-20261016.mp4", "audio_seconds": 6.4}})
    if path == "/api/jobs/queuedjob":
        return httpx.Response(200, json={"status": "queued", "message": "Waiting…", "queued_ahead": 2})
    if path.startswith("/media/"):
        rng = request.headers.get("range")
        if rng == "bytes=0-9":
            return httpx.Response(206, content=VIDEO[:10],
                                  headers={"Content-Range": f"bytes 0-9/{len(VIDEO)}", "Accept-Ranges": "bytes"})
        return httpx.Response(200, content=VIDEO, headers={"Accept-Ranges": "bytes"})
    return httpx.Response(404, json={"error": "Unknown"})


@pytest.fixture
def local_provider(monkeypatch):
    monkeypatch.setattr(settings, "AVATAR_PROVIDER", "local")
    monkeypatch.setattr(settings, "LOCAL_AVATAR_URL", "http://engine.test:8768")
    monkeypatch.setattr(settings, "LOCAL_AVATAR_NAME", "elena")

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(fake_engine)
        return _RealAsyncClient(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)


@pytest.fixture
def client():
    async def no_db():
        yield None

    app.dependency_overrides[get_db] = no_db
    yield TestClient(app)          # no `with`: skips the lifespan, so no database is needed
    app.dependency_overrides.clear()


def test_safe_video_names():
    assert is_safe_video_name("elena-20261016-120000.mp4")
    for bad in ("../secret.mp4", "a/b.mp4", "clip.mov", "", "..mp4x", "x.mp4/../y"):
        assert not is_safe_video_name(bad), bad


@pytest.mark.asyncio
async def test_stt_never_invents_a_transcript(tmp_path):
    stt = SpeechToTextService()
    stt._client = None                                  # no OPENAI_API_KEY
    stt._gemini = None                                  # no GEMINI_API_KEY
    audio = tmp_path / "answer.webm"
    audio.write_bytes(b"fake")
    with pytest.raises(SpeechToTextError) as exc:
        await stt.transcribe_audio_file(str(audio))
    assert exc.value.status_code == 503


class _FakeGemini:
    """Stands in for google-genai: records what it was sent and returns a canned transcript."""
    def __init__(self, text):
        self.text, self.sent = text, None
        self.models = self

    def generate_content(self, model, contents, config=None):
        self.sent = contents
        return type("Resp", (), {"text": self.text})()


def _webm_answer(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not installed")
    path = tmp_path / "answer.webm"
    subprocess.run([ffmpeg, "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                    "-c:a", "libopus", str(path)], check=True)
    return path


@pytest.mark.asyncio
async def test_stt_gemini_used_when_no_openai_key(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STT_PROVIDER", "auto")
    stt = SpeechToTextService()
    stt._client = None
    stt._gemini = _FakeGemini("I would use HikariCP with a connection timeout.")
    res = await stt.transcribe_audio_file(str(_webm_answer(tmp_path)))
    assert res["provider"] == "gemini"
    assert res["transcript"] == "I would use HikariCP with a connection timeout."
    assert "HikariCP" in res["domain_terms_detected"]
    audio_part = stt._gemini.sent[1]
    assert audio_part.inline_data.mime_type == "audio/flac"           # WebM was converted
    assert audio_part.inline_data.data[:4] == b"fLaC"


@pytest.mark.asyncio
async def test_stt_gemini_no_speech_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STT_PROVIDER", "gemini")
    stt = SpeechToTextService()
    stt._gemini = _FakeGemini("[NO_SPEECH]")
    with pytest.raises(SpeechToTextError) as exc:
        await stt.transcribe_audio_file(str(_webm_answer(tmp_path)))
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_evaluation_canned_scores_only_in_mock_mode(monkeypatch):
    from app.services.evaluation_rag import EvaluationRAGService, EvaluationError
    svc = EvaluationRAGService()
    svc._llm, svc._gemini_client = None, None
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")          # real provider, but it failed
    with pytest.raises(EvaluationError) as exc:
        await svc._run_evaluation_chain("Q?", "Topic", "my answer")
    assert exc.value.status_code == 503
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    assert "technical_accuracy" in await svc._run_evaluation_chain("Q?", "Topic", "my answer")


def test_evaluate_rejects_bad_ids_and_empty_answers(client):
    bad = client.post("/api/v1/interview/evaluate", json={"turn_id": "nope", "transcript": "x", "student_id": "s"})
    assert bad.status_code == 404
    empty = client.post("/api/v1/interview/evaluate", json={
        "turn_id": "6f1c3f8e-0000-4000-8000-000000000000", "transcript": "   ", "student_id": "s"})
    assert empty.status_code == 422


def test_transcribe_endpoint_returns_error_not_canned_text(client, monkeypatch):
    from app.api.v1 import interview_router
    monkeypatch.setattr(interview_router.stt_service, "_client", None)
    monkeypatch.setattr(interview_router.stt_service, "_gemini", None)
    res = client.post("/api/v1/interview/transcribe", files={"file": ("a.webm", b"fake", "audio/webm")})
    assert res.status_code == 503
    assert "HikariCP" not in res.text


def test_config_local_available(client, local_provider):
    res = client.get("/api/v1/interview/avatar/config")
    assert res.status_code == 200
    body = res.json()
    assert body == {"provider": "local", "available": True, "avatar_name": "elena",
                    "idle_video_url": "/api/v1/interview/avatar/media/idle", "detail": None}


def test_config_local_missing_avatar(client, local_provider, monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_AVATAR_NAME", "nobody")
    body = client.get("/api/v1/interview/avatar/config").json()
    assert body["available"] is False and "nobody" in body["detail"]


def test_config_local_engine_down(client, monkeypatch):
    monkeypatch.setattr(settings, "AVATAR_PROVIDER", "local")
    monkeypatch.setattr(settings, "LOCAL_AVATAR_URL", "http://127.0.0.1:9")     # nothing listens here
    body = client.get("/api/v1/interview/avatar/config").json()
    assert body["provider"] == "local" and body["available"] is False


def test_render_and_job_status(client, local_provider):
    job = client.post("/api/v1/interview/avatar/render", json={"text": "Tell me about yourself."}).json()
    assert job["job_ids"] == ["abc123def456"]
    done = client.get("/api/v1/interview/avatar/jobs/abc123def456").json()
    assert done["status"] == "done"
    assert done["video_url"] == "/api/v1/interview/avatar/media/outputs/elena-20261016.mp4"
    queued = client.get("/api/v1/interview/avatar/jobs/queuedjob").json()
    assert queued["status"] == "queued" and queued["queued_ahead"] == 2 and queued["video_url"] is None


def test_render_rejected_when_not_local(client, monkeypatch):
    monkeypatch.setattr(settings, "AVATAR_PROVIDER", "liveavatar")
    assert client.post("/api/v1/interview/avatar/render", json={"text": "hi"}).status_code == 409


def test_job_id_validation(client, local_provider):
    assert client.get("/api/v1/interview/avatar/jobs/..%2Fetc").status_code == 404


def test_video_proxy_full_and_range(client, local_provider):
    full = client.get("/api/v1/interview/avatar/media/outputs/elena-20261016.mp4")
    assert full.status_code == 200 and full.content == VIDEO
    assert full.headers["content-type"] == "video/mp4"
    part = client.get("/api/v1/interview/avatar/media/idle", headers={"Range": "bytes=0-9"})
    assert part.status_code == 206 and part.content == VIDEO[:10]
    assert part.headers["content-range"] == f"bytes 0-9/{len(VIDEO)}"


def test_video_proxy_rejects_unsafe_names(client, local_provider):
    assert client.get("/api/v1/interview/avatar/media/outputs/secret.txt").status_code == 404


def test_invalid_ids_are_404_not_500(client):
    assert client.get("/api/v1/interview/report/not-a-uuid").status_code == 404
    res = client.post("/api/v1/interview/question", json={
        "session_id": "not-a-uuid", "student_id": "s1", "target_role": "Backend Developer"})
    assert res.status_code == 404


# ---------------------------------------------------------------- local, key-free providers

def _fake_llm(reply_text):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "/models/phi-4-mini"}]})
        if request.url.path == "/v1/chat/completions":
            import json as _json
            body = _json.loads(request.content)
            assert body["model"] == "/models/phi-4-mini"       # never asks the server to load another model
            return httpx.Response(200, json={"choices": [{"message": {"content": reply_text}}]})
        return httpx.Response(404)
    return handler


@pytest.fixture
def local_llm_reply(monkeypatch):
    from app.services import local_llm as module

    def install(text):
        monkeypatch.setattr(settings, "LLM_PROVIDER", "local")
        monkeypatch.setattr(module.local_llm, "_model_id", None)
        monkeypatch.setattr(httpx, "AsyncClient",
                            lambda *a, **k: _RealAsyncClient(*a, **{**k, "transport": httpx.MockTransport(_fake_llm(text))}))
        return module.local_llm
    return install


@pytest.mark.asyncio
async def test_local_llm_extracts_json_from_chatty_reply(local_llm_reply):
    llm = local_llm_reply('<think>hmm</think>Sure! Here it is:\n```json\n{"a": 1, "b": "x"}\n```\nHope that helps.')
    assert await llm.chat_json("sys", "user") == {"a": 1, "b": "x"}


@pytest.mark.asyncio
async def test_local_evaluation_validates_scores(local_llm_reply):
    from app.services.evaluation_rag import EvaluationRAGService
    local_llm_reply('{"technical_accuracy": 7, "relevance": "3.5", "explanation_quality": 0, "clarity": 4,'
                    ' "technical_feedback": "Good on leaks.", "communication_feedback": "Clear.",'
                    ' "missing_concepts": "timeouts", "spoken_feedback": "Nice work on **leaks**."}')
    data = await EvaluationRAGService()._run_evaluation_chain("Q?", "Pools", "answer")
    assert (data["technical_accuracy"], data["relevance"], data["explanation_quality"]) == (5.0, 3.5, 1.0)
    assert data["missing_concepts"] == ["timeouts"] and data["strengths"] == []


@pytest.mark.asyncio
async def test_local_evaluation_missing_score_is_an_error_not_a_guess(local_llm_reply):
    from app.services.evaluation_rag import EvaluationRAGService, EvaluationError
    local_llm_reply('{"technical_accuracy": 4, "technical_feedback": "ok"}')       # relevance etc. missing
    with pytest.raises(EvaluationError):
        await EvaluationRAGService()._run_evaluation_chain("Q?", "Pools", "answer")


@pytest.mark.asyncio
async def test_local_question_generation_strips_markdown(local_llm_reply):
    from app.services.interview_rag import InterviewRAGService
    local_llm_reply('"How would you detect a **connection leak** in `HikariCP`?"')
    q = await InterviewRAGService()._generate_question_text("Backend Developer", "Entry", "Pools", ["Java"], "ref")
    assert q == "How would you detect a connection leak in HikariCP?"


def test_embeddings_never_fall_back_to_random_vectors(monkeypatch):
    from app.services.embedding_service import EmbeddingService, EmbeddingError
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(EmbeddingError):
        EmbeddingService().embed_text("connection pooling")


# ---------------------------------------------------------------- sentence streaming + cancel

def test_split_for_streaming_puts_first_sentence_alone():
    from app.services.avatar_service import split_for_streaming
    text = ("You spotted the leak well. You didn't mention timeouts, which matter under load. "
            "Also consider metrics. Let's move on.")
    chunks = split_for_streaming(text, max_words=12)
    assert chunks[0] == "You spotted the leak well."
    assert " ".join(chunks).split() == text.split()            # nothing lost or reordered
    assert all(len(c.split()) <= 12 for c in chunks[1:])


def test_split_for_streaming_merges_tiny_opener():
    from app.services.avatar_service import split_for_streaming
    assert split_for_streaming("Okay. How would you size a connection pool?")[0] == \
        "Okay. How would you size a connection pool?"


@pytest.mark.asyncio
async def test_render_chains_sentence_clips(monkeypatch):
    from app.services.avatar_service import LocalAvatarService
    sent = []

    def engine(request):
        import json as _json
        body = _json.loads(request.content)
        sent.append(body)
        return httpx.Response(200, json={"job": f"job{len(sent)}"})

    monkeypatch.setattr(settings, "LOCAL_AVATAR_URL", "http://engine.test:8768")
    monkeypatch.setattr(httpx, "AsyncClient",
                        lambda *a, **k: _RealAsyncClient(*a, **{**k, "transport": httpx.MockTransport(engine)}))
    ids = await LocalAvatarService().render("First sentence here today. Second one. Third one follows it.")
    assert ids == ["job1", "job2"]
    assert sent[0]["continue_job"] is None and sent[1]["continue_job"] == "job1"   # head motion continues


def test_cancel_endpoint(client, local_provider, monkeypatch):
    cancelled = []
    from app.services import avatar_service as module

    async def fake_cancel(self, ids):
        cancelled.extend(ids)

    monkeypatch.setattr(module.LocalAvatarService, "cancel", fake_cancel)
    res = client.post("/api/v1/interview/avatar/cancel", json={"job_ids": ["abc123", "../evil"]})
    assert res.status_code == 200 and cancelled == ["abc123"]


# ---------------------------------------------------------------- CV upload, roles, end interview

DEVOPS_CV = ("Nimal Perera - DevOps intern. 2 years building CI/CD with GitHub Actions and Jenkins, "
             "Docker images, Kubernetes deployments on AWS, Terraform modules, Prometheus and Grafana dashboards.")


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeDB:
    """Just enough of AsyncSession for the roles / CV endpoints."""
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, _stmt):
        return _FakeResult(self.rows)


@pytest.fixture
def db_rows():
    def install(rows):
        async def fake_db():
            yield _FakeDB(rows)
        app.dependency_overrides[get_db] = fake_db
    yield install
    app.dependency_overrides.clear()


def test_cv_text_extraction_and_errors():
    from app.services.cv_service import CVError, extract_text, MAX_CV_BYTES
    assert "Kubernetes" in extract_text("cv.txt", DEVOPS_CV.encode())
    with pytest.raises(CVError) as e1:
        extract_text("cv.png", b"\x89PNG....")
    assert e1.value.status_code == 415
    with pytest.raises(CVError):
        extract_text("cv.txt", b"too short")
    with pytest.raises(CVError) as e3:
        extract_text("cv.txt", b"x" * (MAX_CV_BYTES + 1))
    assert e3.value.status_code == 413


def test_cv_keyword_fallback_picks_role_and_level():
    from app.services.cv_service import _keyword_profile
    p = _keyword_profile(DEVOPS_CV, ["Backend Developer", "DevOps Engineer", "Database Engineer"])
    assert p["suggested_role"] == "DevOps Engineer" and p["experience_level"] == "Mid Level"
    assert {"docker", "kubernetes", "terraform"} <= set(p["skills"]) and p["method"] == "keyword"


@pytest.mark.asyncio
async def test_cv_llm_profile_is_validated(local_llm_reply):
    from app.services.cv_service import analyse_cv
    local_llm_reply('{"name": "Nimal", "skills": ["Docker", "Kubernetes"], "suggested_role": "Astronaut",'
                    ' "experience_level": "Guru", "summary": "DevOps intern with CI/CD and Kubernetes experience."}')
    p = await analyse_cv(DEVOPS_CV, ["Backend Developer", "DevOps Engineer"])
    assert p["method"] == "llm" and p["name"] == "Nimal" and p["skills"] == ["Docker", "Kubernetes"]
    # invented role / level are replaced by the keyword fallback instead of passed through
    assert p["suggested_role"] == "DevOps Engineer" and p["experience_level"] == "Mid Level"


def test_roles_endpoint(db_rows):
    db_rows([("Backend Developer", "Entry Level", 4), ("Backend Developer", "Mid Level", 3),
             ("DevOps Engineer", "Entry Level", 2)])
    roles = TestClient(app).get("/api/v1/interview/roles").json()
    assert roles[0] == {"role": "Backend Developer", "questions": 7, "levels": {"Entry Level": 4, "Mid Level": 3}}
    assert roles[1]["role"] == "DevOps Engineer"


def test_cv_analyze_endpoint_without_llm(db_rows, monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")          # no LLM -> keyword matching
    db_rows([("Backend Developer",), ("DevOps Engineer",)])
    res = TestClient(app).post("/api/v1/interview/cv/analyze",
                               files={"file": ("cv.txt", DEVOPS_CV.encode(), "text/plain")})
    assert res.status_code == 200
    body = res.json()
    assert body["suggested_role"] == "DevOps Engineer" and body["method"] == "keyword"
    assert body["characters_read"] == len(DEVOPS_CV)


def test_cv_analyze_rejects_images(db_rows):
    db_rows([("Backend Developer",)])
    res = TestClient(app).post("/api/v1/interview/cv/analyze", files={"file": ("cv.png", b"\x89PNG", "image/png")})
    assert res.status_code == 415


def test_end_interview_unknown_session(client):
    assert client.post("/api/v1/interview/not-a-uuid/end").status_code == 404


def test_delivery_fields_are_range_checked(client):
    res = client.post("/api/v1/interview/evaluate", json={
        "turn_id": "6f1c3f8e-0000-4000-8000-000000000000", "transcript": "x", "student_id": "s",
        "eye_contact_ratio": 0.8, "smile_ratio": 1.7})
    assert res.status_code == 422                                  # smile_ratio must be 0-1
