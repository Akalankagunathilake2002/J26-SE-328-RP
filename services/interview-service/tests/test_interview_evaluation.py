import pytest
from app.services.evaluation_rag import evaluation_rag_service


@pytest.mark.asyncio
async def test_evaluation_chain_scoring():
    question = "Can you explain how connection pooling works in a Spring Boot application connecting to MySQL?"
    topic = "Database Connection Management"
    transcript = "In Spring Boot, connection pooling via HikariCP keeps open TCP connections in a pool so we avoid handshake latency and avoid exhausting database ports."

    eval_result = await evaluation_rag_service._run_evaluation_chain(
        question=question,
        topic=topic,
        transcript=transcript
    )

    assert "technical_accuracy" in eval_result
    assert "relevance" in eval_result
    assert "explanation_quality" in eval_result
    assert "clarity" in eval_result
    assert 1.0 <= eval_result["technical_accuracy"] <= 5.0
    assert 1.0 <= eval_result["relevance"] <= 5.0
    assert isinstance(eval_result["missing_concepts"], list)
    assert isinstance(eval_result["strengths"], list)
    assert len(eval_result["technical_feedback"]) > 10
