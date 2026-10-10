import os
import uuid
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.interview import InterviewSession, InterviewTurn
from app.schemas.interview import (
    StartInterviewRequest,
    InterviewSessionResponse,
    QuestionGenerationRequest,
    InterviewQuestionResponse,
    TranscribeResponse,
    EvaluateAnswerRequest,
    EvaluationResultResponse
)
from app.services.interview_rag import interview_rag_service
from app.services.stt_service import stt_service
from app.services.evaluation_rag import evaluation_rag_service

router = APIRouter(prefix="/interview", tags=["AI Mock Interview Assistant"])


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
    """Generates a personalized role-specific interview question using RAG."""
    return await interview_rag_service.generate_interview_question(session=db, request=request)


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
            latency_ms=res["latency_ms"]
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


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
    s_uuid = uuid.UUID(session_id)
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
