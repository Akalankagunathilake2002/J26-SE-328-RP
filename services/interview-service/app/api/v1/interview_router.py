import os
import uuid
import tempfile
import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.models.interview import InterviewSession, InterviewTurn
from app.schemas.interview import (
    StartInterviewRequest,
    InterviewSessionResponse,
    QuestionGenerationRequest,
    InterviewQuestionResponse,
    TranscribeResponse,
    AvatarSessionTokenResponse,
    AvatarConfigResponse,
    AvatarRenderRequest,
    AvatarJobResponse,
    EvaluateAnswerRequest,
    EvaluationResultResponse
)
from app.services.interview_rag import interview_rag_service
from app.services.stt_service import stt_service, SpeechToTextError
from app.services.evaluation_rag import evaluation_rag_service
from app.services.avatar_service import (
    avatar_service,
    local_avatar_service,
    is_safe_video_name,
    AvatarServiceError,
)

router = APIRouter(prefix="/interview", tags=["AI Mock Interview Assistant"])


def parse_uuid(value: str, what: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail=f"Unknown {what}: {value}")


@router.post("/start", response_model=InterviewSessionResponse)
async def start_session(
    request: StartInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """Initializes a new mock interview session for a student and target role."""
    session = InterviewSession(
        student_id=request.student_id,
        target_role=request.target_role,
        experience_level=request.experience_level
    )
    db.add(session)
    await db.commit()

    return InterviewSessionResponse(
        session_id=str(session.id),
        student_id=request.student_id,
        target_role=request.target_role,
        experience_level=request.experience_level,
        message=f"Mock interview session initialized for {request.target_role} ({request.experience_level})."
    )


@router.post("/question", response_model=InterviewQuestionResponse)
async def get_question(
    request: QuestionGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generates a personalized role-specific interview question using RAG.

    With the local avatar, rendering the spoken video starts here, so it overlaps with the
    candidate reading the question card instead of starting when the frontend asks.
    """
    parse_uuid(request.session_id, "interview session")
    question = await interview_rag_service.generate_interview_question(session=db, request=request)
    if local_avatar_service.enabled:
        try:
            question.avatar_job_id = await local_avatar_service.render(question.question)
        except AvatarServiceError as e:
            print(f"[Warning] Local avatar render not started: {e}")   # frontend falls back to voice
    return question


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...)
):
    """Converts student spoken answer audio (WebM/WAV) to text via Whisper."""
    # Save temporary file for Whisper
    suffix = os.path.splitext(file.filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        res = await stt_service.transcribe_audio_file(tmp_path)
        return TranscribeResponse(
            transcript=res["transcript"],
            latency_ms=res["latency_ms"],
            domain_terms_detected=res.get("domain_terms_detected", [])
        )
    except SpeechToTextError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/avatar/token", response_model=AvatarSessionTokenResponse)
async def create_avatar_session_token():
    """Mints a LiveAvatar session token for the realistic human interviewer video stream."""
    try:
        return AvatarSessionTokenResponse(**await avatar_service.create_session_token())
    except AvatarServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/avatar/config", response_model=AvatarConfigResponse)
async def get_avatar_config():
    """Which interviewer the frontend should use, and whether it is reachable right now."""
    if settings.AVATAR_PROVIDER == "local":
        return AvatarConfigResponse(**await local_avatar_service.config())
    if settings.AVATAR_PROVIDER == "liveavatar":
        return AvatarConfigResponse(provider="liveavatar", available=avatar_service.enabled,
                                    detail=None if avatar_service.enabled else "LIVEAVATAR_API_KEY is not configured")
    return AvatarConfigResponse(provider="none", available=False)


@router.post("/avatar/render", response_model=AvatarJobResponse)
async def render_avatar_clip(request: AvatarRenderRequest):
    """Queues a local-avatar clip for arbitrary text (replays, fallback questions)."""
    if not local_avatar_service.enabled:
        raise HTTPException(status_code=409, detail="The local avatar is not the active provider")
    try:
        job_id = await local_avatar_service.render(request.text)
    except AvatarServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return AvatarJobResponse(job_id=job_id, status="queued")


@router.get("/avatar/jobs/{job_id}", response_model=AvatarJobResponse)
async def get_avatar_job(job_id: str):
    """Progress of a local-avatar clip; `video_url` is set once it is ready to play."""
    if not job_id.isalnum() or len(job_id) > 64:
        raise HTTPException(status_code=404, detail="Unknown avatar job")
    try:
        return AvatarJobResponse(**await local_avatar_service.job(job_id))
    except AvatarServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


async def _proxy_video(url: str, request: Request) -> StreamingResponse:
    # Forward Range so browsers can seek; Safari will not play MP4 without 206 responses.
    headers = {"Range": request.headers["range"]} if "range" in request.headers else {}
    client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=60.0))
    try:
        upstream = await client.send(client.build_request("GET", url, headers=headers), stream=True)
    except httpx.HTTPError as e:
        await client.aclose()
        raise HTTPException(status_code=503, detail=f"Local avatar engine unreachable: {e}")
    if upstream.status_code not in (200, 206):
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=404 if upstream.status_code == 404 else 502, detail="Avatar video not available")

    async def body():
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    passthrough = {k.lower(): v for k, v in upstream.headers.items()
                   if k.lower() in ("content-length", "content-range", "accept-ranges", "last-modified", "etag")}
    passthrough.setdefault("accept-ranges", "bytes")
    passthrough["cache-control"] = "no-cache"
    return StreamingResponse(body(), status_code=upstream.status_code,
                             media_type="video/mp4", headers=passthrough)


@router.get("/avatar/media/idle")
async def get_avatar_idle_video(request: Request):
    """The interviewer's idle loop (head motion + blinks), played between questions."""
    return await _proxy_video(local_avatar_service.media_url("idle"), request)


@router.get("/avatar/media/outputs/{file_name}")
async def get_avatar_clip(file_name: str, request: Request):
    """A rendered spoken clip from the local avatar engine."""
    if not is_safe_video_name(file_name):
        raise HTTPException(status_code=404, detail="Avatar video not available")
    return await _proxy_video(local_avatar_service.media_url("output", file_name), request)


@router.post("/evaluate", response_model=EvaluationResultResponse)
async def evaluate_answer(
    request: EvaluateAnswerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Evaluates transcribed answer against the question's rubric and technical references."""
    return await evaluation_rag_service.evaluate_spoken_answer(session=db, request=request)


@router.get("/report/{session_id}")
async def get_session_report(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generates a diagnostic report summarizing all question-turns in the interview session."""
    s_uuid = parse_uuid(session_id, "interview session")
    stmt = select(InterviewTurn).where(InterviewTurn.session_id == s_uuid).order_by(InterviewTurn.created_at.asc())
    res = await db.execute(stmt)
    turns = res.scalars().all()

    turn_summaries = []
    avg_scores = {"tech": 0.0, "rel": 0.0, "exp": 0.0, "clar": 0.0}

    for t in turns:
        t_tech = float(t.technical_accuracy_score or 0)
        t_rel = float(t.relevance_score or 0)
        t_exp = float(t.explanation_quality_score or 0)
        t_clar = float(t.clarity_score or 0)

        avg_scores["tech"] += t_tech
        avg_scores["rel"] += t_rel
        avg_scores["exp"] += t_exp
        avg_scores["clar"] += t_clar

        turn_summaries.append({
            "turn_id": str(t.id),
            "question": t.question,
            "topic": t.topic,
            "transcript": t.transcript,
            "technical_accuracy": t_tech,
            "relevance": t_rel,
            "explanation_quality": t_exp,
            "clarity": t_clar,
            "strengths": t.strengths or [],
            "missing_concepts": t.missing_concepts or [],
            "areas_for_improvement": t.areas_for_improvement or []
        })

    count = max(1, len(turns))
    return {
        "session_id": session_id,
        "turns_completed": len(turns),
        "overall_scores": {
            "technical_accuracy": round(avg_scores["tech"] / count, 2),
            "relevance": round(avg_scores["rel"] / count, 2),
            "explanation_quality": round(avg_scores["exp"] / count, 2),
            "clarity": round(avg_scores["clar"] / count, 2)
        },
        "turns": turn_summaries
    }
