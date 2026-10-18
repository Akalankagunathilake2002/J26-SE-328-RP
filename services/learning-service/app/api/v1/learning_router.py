from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.learning import LearningDocument
from app.schemas.learning import LearningQueryRequest, LearningQueryResponse, LearningTopic
from app.services.learning_rag import learning_rag_service
from app.services.progress_service import progress_service
from app.services.experiment_logger import experiment_logger

router = APIRouter(prefix="/learning", tags=["Personalized Learning Assistant"])


@router.post("/query", response_model=LearningQueryResponse)
async def submit_learning_query(
    request: LearningQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a student question to the Personalized Learning Assistant.
    Executes role-filtered semantic search over pgvector, constructs a grounded prompt,
    and returns a cited answer with a recommended next topic.
    """
    try:
        response = await learning_rag_service.execute_rag(session=db, request=request)

        # Record progress and history
        topic = request.learning_priority or (response.sources[0].topic if response.sources else "General")
        await progress_service.record_query_progress(
            session=db,
            student_id=request.student_id,
            target_role=request.target_role,
            question=request.question,
            answer=response.answer,
            topic=topic,
            learning_priority=request.learning_priority,
            recommended_next_topic=response.recommended_next_topic,
            retrieved_chunk_ids=[c.chunk_id for c in response.retrieved_chunks],
            sources=[s.model_dump() for s in response.sources]
        )

        # Log experiment telemetry
        await experiment_logger.log_run(
            session=db,
            query_text=request.question,
            retrieved_chunk_ids=[c.chunk_id for c in response.retrieved_chunks],
            similarity_scores=[c.similarity_score for c in response.retrieved_chunks],
            retrieval_latency_ms=response.retrieval_latency_ms,
            generation_latency_ms=response.generation_latency_ms,
            generated_output=response.answer,
            is_baseline=0
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Learning RAG execution error: {str(e)}")


@router.get("/topics", response_model=List[LearningTopic])
async def list_learning_topics(target_role: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Curriculum documents available for a role (same role filter as retrieval), so the frontend
    can suggest questions the assistant has material for."""
    stmt = select(LearningDocument.title, LearningDocument.topic, LearningDocument.target_role)
    if target_role and target_role.lower() != "all":
        stmt = stmt.where(or_(LearningDocument.target_role.ilike(f"%{target_role}%"),
                              LearningDocument.target_role.ilike("%all%")))
    rows = (await db.execute(stmt.order_by(LearningDocument.topic))).all()
    return [LearningTopic(title=r.title, topic=r.topic, target_role=r.target_role) for r in rows]
