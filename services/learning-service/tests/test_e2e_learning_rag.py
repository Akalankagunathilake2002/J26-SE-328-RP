import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.schemas.learning import LearningQueryRequest, BenchmarkRequest
from app.services.learning_rag import learning_rag_service
from app.services.progress_service import progress_service


@pytest.mark.asyncio
async def test_learning_rag_pipeline_execution():
    # Use localhost for host connection to docker postgres port 5432
    db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/learning_db"
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        req = LearningQueryRequest(
            student_id="test_student_01",
            target_role="Backend Developer",
            current_skills=["Python", "SQL", "Git"],
            learning_priority="REST API Development",
            question="How does JWT authentication work?"
        )

        response = await learning_rag_service.execute_rag(session=session, request=req)

        # 1. Assert response structure
        assert response.answer is not None
        assert len(response.answer) > 50
        assert response.recommended_next_topic is not None
        assert response.retrieval_latency_ms >= 0.0
        assert response.generation_latency_ms >= 0.0

        # 2. Assert retrieved chunks from pgvector
        assert len(response.retrieved_chunks) > 0
        top_chunk = response.retrieved_chunks[0]
        assert top_chunk.similarity_score >= 0.0
        assert "JWT" in top_chunk.content_preview or "JSON" in top_chunk.content_preview
        assert top_chunk.topic == "Jwt Authentication"

        # 3. Assert cited sources
        assert len(response.sources) > 0
        assert any("JWT" in s.title for s in response.sources)

    await engine.dispose()


@pytest.mark.asyncio
async def test_progress_tracking_no_skill_tree():
    db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/learning_db"
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # Record queries
        await progress_service.record_query_progress(
            session=session,
            student_id="test_student_progress",
            target_role="Backend Developer",
            question="What is JWT?",
            answer="JWT is JSON Web Token",
            topic="JWT Authentication"
        )

        progress = await progress_service.get_student_progress(
            session=session,
            student_id="test_student_progress"
        )

        assert progress.student_id == "test_student_progress"
        assert progress.total_topics_explored >= 1
        assert any(t.topic == "JWT Authentication" for t in progress.topics)

    await engine.dispose()
