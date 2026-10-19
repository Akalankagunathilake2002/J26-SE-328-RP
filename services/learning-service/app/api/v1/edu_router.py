from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.learning import (
    EduChatRequest, EduChatResponse, GradeAnswerRequest, GradeAnswerResponse, LessonRequest, LessonResponse,
    QuizRequest, QuizResponse,
)
from app.services import edu_assistant
from app.services.learning_rag import LLMUnavailable
from app.services.progress_service import progress_service

router = APIRouter(prefix="/learning/edu", tags=["Skillaro Edu Assistant"])


async def _record(db: AsyncSession, student_id: str, role: str, question: str, answer: str, topic: str):
    # Progress is a side effect: a failure here must not lose the student's answer
    try:
        await progress_service.record_query_progress(session=db, student_id=student_id, target_role=role,
                                                     question=question, answer=answer, topic=topic[:100])
    except Exception as e:
        await db.rollback()
        print(f"[Warning] Learning progress not recorded: {e}")


@router.post("/chat", response_model=EduChatResponse)
async def edu_chat(request: EduChatRequest, db: AsyncSession = Depends(get_db)):
    """A friendly, multi-turn chat with Skillaro, grounded in the curriculum; suggests topics to learn."""
    response = await edu_assistant.chat(db, request)
    topic = request.current_topic or (response.sources[0].topic if response.sources else "General")
    await _record(db, request.student_id, request.target_role, request.message, response.reply, topic or "General")
    return response


@router.post("/lesson", response_model=LessonResponse)
async def edu_lesson(request: LessonRequest, db: AsyncSession = Depends(get_db)):
    """A lesson on a topic at one stage (beginner / intermediate / advanced), each mapped to two levels of
    Bloom's taxonomy."""
    try:
        response = await edu_assistant.lesson(db, request)
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    await _record(db, request.student_id, request.target_role, f"Lesson: {request.topic} ({request.level})",
                  response.introduction, request.topic)
    return response


@router.post("/quiz", response_model=QuizResponse)
async def edu_quiz(request: QuizRequest, db: AsyncSession = Depends(get_db)):
    """MCQs and open questions at the stage's Bloom levels. MCQ answers are included for instant marking."""
    try:
        return await edu_assistant.quiz(db, request)
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/grade", response_model=GradeAnswerResponse)
async def edu_grade(request: GradeAnswerRequest):
    """Marks a written (open) answer with feedback and a model answer."""
    try:
        return await edu_assistant.grade_answer(request)
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
