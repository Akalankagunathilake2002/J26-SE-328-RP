"""Local avatar provider, video proxy, STT error handling and ID validation.

Runs without PostgreSQL, Docker or the avatar engine: the engine is faked with an
httpx MockTransport and the database dependency is overridden.
"""
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
    audio = tmp_path / "answer.webm"
    audio.write_bytes(b"fake")
    with pytest.raises(SpeechToTextError) as exc:
        await stt.transcribe_audio_file(str(audio))
    assert exc.value.status_code == 503


def test_transcribe_endpoint_returns_error_not_canned_text(client, monkeypatch):
    from app.api.v1 import interview_router
    monkeypatch.setattr(interview_router.stt_service, "_client", None)
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
    assert job["job_id"] == "abc123def456"
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
