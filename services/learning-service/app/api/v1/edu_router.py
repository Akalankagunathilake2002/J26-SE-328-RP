import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.schemas.learning import (
    EduChatRequest, EduChatResponse, GradeAnswerRequest, GradeAnswerResponse, LessonRequest, LessonResponse,
    MasteryRecordRequest, MasteryResponse, QuizRequest, QuizResponse, ReviewAnswerRequest, ReviewAnswerResponse,
    ReviewItem,
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


@router.post("/chat/stream")
async def edu_chat_stream(request: EduChatRequest):
    """The chat reply streamed as it's written (server-sent events): "delta" events with text, then a
    "done" event with the full reply, sources and suggested topics."""
    async def events():
        # Its own session: the request's one can close before a streamed response finishes
        async with AsyncSessionLocal() as db:
            done = None
            try:
                async for event in edu_assistant.chat_stream(db, request):
                    if event["type"] == "done":
                        done = event
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
                return
            if done:
                topic = request.current_topic or (done["sources"][0].get("topic") if done["sources"] else None)
                await _record(db, request.student_id, request.target_role, request.message, done["reply"],
                              topic or "General")

    # X-Accel-Buffering: nginx (the local gateway) passes each event on instead of buffering the response
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/lesson", response_model=LessonResponse)
async def edu_lesson(request: LessonRequest, db: AsyncSession = Depends(get_db)):
    """A lesson on a topic at one stage (beginner / intermediate / advanced), each mapped to two levels of
    Bloom's taxonomy."""
    try:
        response = await edu_assistant.lesson(db, request)
    except LLMUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not response.cached:
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



@router.post("/mastery", response_model=MasteryResponse)
async def record_mastery(request: MasteryRecordRequest, db: AsyncSession = Depends(get_db)):
    """Saves a finished check (MCQ score, written-answer mark) and schedules missed questions for review."""
    return await edu_assistant.record_mastery(db, request)


@router.get("/mastery/{student_id}", response_model=MasteryResponse)
async def get_mastery(student_id: str, db: AsyncSession = Depends(get_db)):
    """Best result per topic and stage (the skill tree), and the number of review questions due."""
    return await edu_assistant.mastery(db, student_id)


@router.get("/reviews/{student_id}", response_model=List[ReviewItem])
async def get_due_reviews(student_id: str, db: AsyncSession = Depends(get_db)):
    """Missed questions that are due for spaced-repetition review now."""
    return await edu_assistant.due_reviews(db, student_id)


@router.post("/reviews/{review_id}/answer", response_model=ReviewAnswerResponse)
async def answer_review(review_id: str, request: ReviewAnswerRequest, db: AsyncSession = Depends(get_db)):
    """Moves a review question to its next interval (right) or back to the first (wrong)."""
    result = await edu_assistant.answer_review(db, review_id, request.correct)
    if not result:
        raise HTTPException(status_code=404, detail="Unknown review question")
    return result
