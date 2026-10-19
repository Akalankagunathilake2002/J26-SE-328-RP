import os
import uuid
import tempfile
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.config import settings
from app.core.database import get_db
from app.models.interview import InterviewSession, InterviewTurn, InterviewDocument
from app.schemas.interview import (
    RoleInfo,
    CVProfileResponse,
    StartInterviewRequest,
    InterviewSessionResponse,
    QuestionGenerationRequest,
    InterviewQuestionResponse,
    TranscribeResponse,
    AvatarSessionTokenResponse,
    AvatarConfigResponse,
    AvatarRenderRequest,
    AvatarRenderResponse,
    AvatarCancelRequest,
    AvatarJobResponse,
    EvaluateAnswerRequest,
    EvaluationResultResponse,
    RespondRequest,
    ConversationReplyResponse,
)
from app.services import interview_flow
from app.services.interview_rag import interview_rag_service
from app.services.stt_service import stt_service, SpeechToTextError
from app.services.evaluation_rag import evaluation_rag_service, EvaluationError
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


@router.get("/roles", response_model=list[RoleInfo])
async def list_roles(db: AsyncSession = Depends(get_db)):
    """Job roles the question bank covers, with question counts per experience level."""
    res = await db.execute(
        select(InterviewDocument.role, InterviewDocument.difficulty, func.count())
        .group_by(InterviewDocument.role, InterviewDocument.difficulty)
    )
    roles: dict[str, RoleInfo] = {}
    for role, level, count in res.all():
        info = roles.setdefault(role, RoleInfo(role=role, questions=0, levels={}))
        info.questions += count
        info.levels[level] = count
    return sorted(roles.values(), key=lambda r: -r.questions)


@router.post("/cv/analyze", response_model=CVProfileResponse)
async def analyze_cv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Reads a CV (PDF, DOCX or TXT) in memory and returns skills, a suggested role and level.
    The file and its text are not stored."""
    from app.services.cv_service import CVError, analyse_cv, extract_text, MAX_CV_BYTES
    data = await file.read(MAX_CV_BYTES + 1)
    try:
        text = extract_text(file.filename or "", data)
    except CVError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    roles = [r for (r,) in (await db.execute(select(InterviewDocument.role).distinct())).all()]
    profile = await analyse_cv(text, roles)
    return CVProfileResponse(**profile, characters_read=len(text))


@router.post("/{session_id}/end")
async def end_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Marks the interview as completed and returns its report."""
    s_uuid = parse_uuid(session_id, "interview session")
    session = await db.get(InterviewSession, s_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown interview session")
    session.status = "completed"
    await db.commit()
    return await get_session_report(session_id, db)


@router.post("/start", response_model=InterviewSessionResponse)
async def start_session(
    request: StartInterviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """Initializes a new mock interview session for a student and target role."""
    session = InterviewSession(
        student_id=request.student_id,
        target_role=request.target_role,
        experience_level=request.experience_level,
        candidate_name=request.candidate_name,
        duration_minutes=request.duration_minutes,
    )
    db.add(session)
    await db.commit()

    return InterviewSessionResponse(
        session_id=str(session.id),
        student_id=request.student_id,
        target_role=request.target_role,
        experience_level=request.experience_level,
        duration_minutes=request.duration_minutes,
        message=f"Mock interview session initialized for {request.target_role} ({request.experience_level})."
    )


@router.post("/question", response_model=InterviewQuestionResponse)
async def get_question(
    request: QuestionGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """The interviewer's next turn: the welcome and introductions, a role question generated with RAG,
    or the closing question, depending on the turns so far and the time left (interview_flow.py).

    With the local avatar, rendering the spoken video starts here, so it overlaps with the
    candidate reading the question card instead of starting when the frontend asks.
    """
    interview = await db.get(InterviewSession, parse_uuid(request.session_id, "interview session"))
    if not interview:
        raise HTTPException(status_code=404, detail="Unknown interview session")
    phase = await interview_flow.plan(db, interview)
    if phase == "done":
        raise HTTPException(status_code=409, detail="The interview has ended.")
    if phase == "core":
        question = await interview_rag_service.generate_interview_question(session=db, request=request)
    else:
        question = await interview_flow.create_turn(db, interview, phase)
    if local_avatar_service.enabled:
        try:
            question.avatar_job_ids = await local_avatar_service.render(question.question)
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


@router.post("/avatar/render", response_model=AvatarRenderResponse)
async def render_avatar_clip(request: AvatarRenderRequest):
    """Queues local-avatar sentence clips for arbitrary text (replays, fallback questions)."""
    if not local_avatar_service.enabled:
        raise HTTPException(status_code=409, detail="The local avatar is not the active provider")
    try:
        job_ids = await local_avatar_service.render(request.text)
    except AvatarServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    return AvatarRenderResponse(job_ids=job_ids)


@router.post("/avatar/cancel")
async def cancel_avatar_clips(request: AvatarCancelRequest):
    """Drops clips that haven't started rendering, so the clip the candidate is waiting for goes next."""
    if not local_avatar_service.enabled:
        return {"cancelled": 0}
    ids = [j for j in request.job_ids if j.isalnum() and len(j) <= 64]
    await local_avatar_service.cancel(ids)
    return {"requested": len(ids)}


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
    """Evaluates the transcribed answer against the question's rubric and technical references.

    The interviewer's short spoken reaction starts rendering on the local avatar straight away,
    so it is ready (or nearly) by the time the candidate has read the scorecard.
    """
    parse_uuid(request.turn_id, "interview turn")
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="There is no answer to evaluate yet.")
    try:
        result = await evaluation_rag_service.evaluate_spoken_answer(session=db, request=request)
    except EvaluationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    if local_avatar_service.enabled and result.spoken_feedback:
        try:
            result.avatar_job_ids = await local_avatar_service.render(result.spoken_feedback)
        except AvatarServiceError as e:
            print(f"[Warning] Local avatar feedback render not started: {e}")
    return result


@router.post("/respond", response_model=ConversationReplyResponse)
async def respond_to_answer(request: RespondRequest, db: AsyncSession = Depends(get_db)):
    """The interviewer's reply to an introduction or closing answer. These answers aren't scored; the
    reply to the closing answer is the goodbye (interview_complete)."""
    turn = await db.get(InterviewTurn, parse_uuid(request.turn_id, "interview turn"))
    if not turn:
        raise HTTPException(status_code=404, detail="Unknown interview turn")
    if turn.phase == "core":
        raise HTTPException(status_code=409, detail="Role questions are evaluated with /evaluate.")
    reply, done = await interview_flow.reply_to(db, turn, request.transcript.strip())
    result = ConversationReplyResponse(turn_id=request.turn_id, phase=turn.phase, reply=reply,
                                       interview_complete=done)
    if local_avatar_service.enabled:
        try:
            result.avatar_job_ids = await local_avatar_service.render(reply)
        except AvatarServiceError as e:
            print(f"[Warning] Local avatar reply render not started: {e}")
    return result


@router.get("/report/{session_id}")
async def get_session_report(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generates a diagnostic report summarizing the scored role questions of the interview session,
    with the (unscored) introduction and closing exchanges alongside."""
    s_uuid = parse_uuid(session_id, "interview session")
    interview = await db.get(InterviewSession, s_uuid)
    stmt = (select(InterviewTurn).where(InterviewTurn.session_id == s_uuid, InterviewTurn.phase == "core")
            .order_by(InterviewTurn.created_at.asc()))
    res = await db.execute(stmt)
    turns = res.scalars().all()

    turn_summaries = []
    avg_scores = {"tech": 0.0, "rel": 0.0, "exp": 0.0, "clar": 0.0}
    answered = 0

    for t in turns:
        evaluated = t.technical_accuracy_score is not None
        t_tech = float(t.technical_accuracy_score) if evaluated else None
        t_rel = float(t.relevance_score) if evaluated else None
        t_exp = float(t.explanation_quality_score) if evaluated else None
        t_clar = float(t.clarity_score) if evaluated else None

        # Questions asked but never answered (e.g. the interview ended) don't count as zeros
        if evaluated:
            answered += 1
            avg_scores["tech"] += t_tech
            avg_scores["rel"] += t_rel
            avg_scores["exp"] += t_exp
            avg_scores["clar"] += t_clar

        turn_summaries.append({
            "turn_id": str(t.id),
            "question": t.question,
            "topic": t.topic,
            "transcript": t.transcript,
            "evaluated": evaluated,
            "technical_accuracy": t_tech,
            "relevance": t_rel,
            "explanation_quality": t_exp,
            "clarity": t_clar,
            "strengths": t.strengths or [],
            "missing_concepts": t.missing_concepts or [],
            "areas_for_improvement": t.areas_for_improvement or []
        })

    count = max(1, answered)
    elapsed = None
    if interview and interview.created_at:
        elapsed = round((datetime.now(timezone.utc) - interview.created_at).total_seconds() / 60, 1)
    return {
        "session_id": session_id,
        "planned_minutes": interview.duration_minutes if interview else None,
        "elapsed_minutes": elapsed,
        "conversation": await interview_flow.conversation(db, s_uuid),
        "questions_asked": len(turns),
        "turns_completed": answered,
        "overall_scores": {
            "technical_accuracy": round(avg_scores["tech"] / count, 2),
            "relevance": round(avg_scores["rel"] / count, 2),
            "explanation_quality": round(avg_scores["exp"] / count, 2),
            "clarity": round(avg_scores["clar"] / count, 2)
        },
        "turns": turn_summaries
    }
