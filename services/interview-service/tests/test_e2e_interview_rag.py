import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.interview import InterviewSession
from app.schemas.interview import QuestionGenerationRequest, EvaluateAnswerRequest
from app.services.interview_rag import interview_rag_service
from app.services.evaluation_rag import evaluation_rag_service


@pytest.mark.asyncio
async def test_interview_rag_pipeline_execution():
    db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_db"
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Start Session
        sess = InterviewSession(
            student_id="test_interview_stu",
            target_role="Backend Developer",
            experience_level="Entry Level"
        )
        session.add(sess)
        await session.commit()

        # 2. Generate Question via RAG
        q_req = QuestionGenerationRequest(
            session_id=str(sess.id),
            student_id="test_interview_stu",
            target_role="Backend Developer",
            experience_level="Entry Level",
            current_skills=["Java", "Spring Boot", "MySQL"]
        )
        q_resp = await interview_rag_service.generate_interview_question(
            session=session,
            request=q_req
        )

        assert q_resp.question is not None
        assert len(q_resp.question) > 20
        assert q_resp.topic is not None
        assert len(q_resp.rubric_criteria) > 0

        # 3. Evaluate Spoken Answer against Rubric
        eval_req = EvaluateAnswerRequest(
            turn_id=q_resp.turn_id,
            transcript="HikariCP connection pooling caches TCP database connections to prevent expensive TLS handshakes and port exhaustion.",
            student_id="test_interview_stu"
        )

        eval_resp = await evaluation_rag_service.evaluate_spoken_answer(
            session=session,
            request=eval_req
        )

        assert eval_resp.turn_id == q_resp.turn_id
        assert 1.0 <= eval_resp.technical_accuracy <= 5.0
        assert 1.0 <= eval_resp.relevance <= 5.0
        assert 1.0 <= eval_resp.explanation_quality <= 5.0
        assert 1.0 <= eval_resp.clarity <= 5.0
        assert len(eval_resp.technical_feedback) > 10
        assert len(eval_resp.communication_feedback) > 10
        assert isinstance(eval_resp.strengths, list)
        assert isinstance(eval_resp.missing_concepts, list)

    await engine.dispose()
