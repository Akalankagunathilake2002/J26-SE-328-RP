import re
from typing import Dict, Any
import httpx
from app.core.config import settings


class AvatarServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class LiveAvatarService:
    """
    Mints short-lived HeyGen LiveAvatar session tokens so the browser can stream a
    photorealistic human interviewer (lip-sync, blinking, head and hand gestures)
    without ever seeing the LiveAvatar API key.
    """

    @property
    def enabled(self) -> bool:
        return bool(settings.LIVEAVATAR_API_KEY)

    async def create_session_token(self) -> Dict[str, Any]:
        if not self.enabled:
            raise AvatarServiceError("LIVEAVATAR_API_KEY is not configured", status_code=503)

        payload: Dict[str, Any] = {
            "mode": "FULL",
            "avatar_id": settings.LIVEAVATAR_AVATAR_ID,
            "is_sandbox": settings.LIVEAVATAR_SANDBOX,
            # Push-to-talk is never triggered, so LiveAvatar's built-in LLM never answers the
            # candidate. The avatar only speaks the RAG-generated questions sent via repeat().
            "interactivity_type": "PUSH_TO_TALK",
            "video_settings": {"quality": "high", "encoding": "H264"},
            # FULL mode requires a persona (or voice agent); without voice_id the avatar's default voice is used
            "avatar_persona": {"language": "en"},
        }
        if not settings.LIVEAVATAR_SANDBOX:
            payload["max_session_duration"] = settings.LIVEAVATAR_MAX_SESSION_SECONDS
        if settings.LIVEAVATAR_VOICE_ID:
            payload["avatar_persona"]["voice_id"] = settings.LIVEAVATAR_VOICE_ID

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{settings.LIVEAVATAR_API_URL}/v1/sessions/token",
                    headers={"X-API-KEY": settings.LIVEAVATAR_API_KEY, "accept": "application/json"},
                    json=payload,
                )
        except httpx.HTTPError as e:
            raise AvatarServiceError(f"LiveAvatar unreachable: {e}")

        if res.status_code != 200:
            raise AvatarServiceError(f"LiveAvatar token request failed ({res.status_code}): {res.text[:300]}")

        data = (res.json() or {}).get("data") or {}
        if not data.get("session_token"):
            raise AvatarServiceError("LiveAvatar response did not include a session token")

        return {
            "session_token": data["session_token"],
            "session_id": data["session_id"],
            "avatar_id": settings.LIVEAVATAR_AVATAR_ID,
            "is_sandbox": settings.LIVEAVATAR_SANDBOX,
        }


avatar_service = LiveAvatarService()


MEDIA_PREFIX = "/api/v1/interview/avatar/media"
_VIDEO_NAME = re.compile(r"^[A-Za-z0-9._-]+\.mp4$")


def is_safe_video_name(name: str) -> bool:
    return bool(_VIDEO_NAME.match(name)) and ".." not in name


class LocalAvatarService:
    """
    Client for the local interview avatar engine (LivePortrait head motion + blinks and
    MuseTalk lip-sync), which runs natively on the host Mac because it needs the Apple GPU.
    Each question is rendered to an MP4 in the background; the browser plays it through
    this service, so it never talks to the engine directly.
    """

    @property
    def enabled(self) -> bool:
        return settings.AVATAR_PROVIDER == "local"

    @property
    def base(self) -> str:
        return settings.LOCAL_AVATAR_URL.rstrip("/")

    async def config(self) -> Dict[str, Any]:
        name = settings.LOCAL_AVATAR_NAME
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base}/api/avatars")
            res.raise_for_status()
            names = [a.get("name") for a in res.json()]
        except (httpx.HTTPError, ValueError) as e:
            return {"provider": "local", "available": False, "avatar_name": name,
                    "detail": f"Local avatar engine unreachable at {self.base}: {e}"}
        if name not in names:
            return {"provider": "local", "available": False, "avatar_name": name,
                    "detail": f"Avatar '{name}' not found in the local engine (has: {', '.join(names) or 'none'})"}
        return {"provider": "local", "available": True, "avatar_name": name,
                "idle_video_url": f"{MEDIA_PREFIX}/idle"}

    async def render(self, text: str) -> str:
        """Queue a spoken clip; returns the engine's job id."""
        payload = {"avatar": settings.LOCAL_AVATAR_NAME, "text": text,
                   "voice": settings.LOCAL_AVATAR_VOICE, "decoder": settings.LOCAL_AVATAR_DECODER}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.base}/api/speak", json=payload)
        except httpx.HTTPError as e:
            raise AvatarServiceError(f"Local avatar engine unreachable: {e}", status_code=503)
        if res.status_code != 200:
            raise AvatarServiceError(f"Local avatar render failed ({res.status_code}): {res.text[:300]}")
        return res.json()["job"]

    async def job(self, job_id: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base}/api/jobs/{job_id}")
        except httpx.HTTPError as e:
            raise AvatarServiceError(f"Local avatar engine unreachable: {e}", status_code=503)
        if res.status_code == 404:
            raise AvatarServiceError("Unknown avatar job (the engine may have restarted)", status_code=404)
        if res.status_code != 200:
            raise AvatarServiceError(f"Local avatar job lookup failed ({res.status_code})")
        j = res.json()
        out = {"job_id": job_id, "status": j.get("status", "error"), "message": j.get("message"),
               "queued_ahead": j.get("queued_ahead"), "error": j.get("error")}
        result = j.get("result") or {}
        if out["status"] == "done" and result.get("url"):
            out["video_url"] = f"{MEDIA_PREFIX}/outputs/{result['url'].rsplit('/', 1)[-1]}"
            out["audio_seconds"] = result.get("audio_seconds")
        return out

    def media_url(self, kind: str, name: str = "") -> str:
        if kind == "idle":
            return f"{self.base}/media/avatars/{settings.LOCAL_AVATAR_NAME}/idle.mp4"
        return f"{self.base}/media/outputs/{name}"


local_avatar_service = LocalAvatarService()
