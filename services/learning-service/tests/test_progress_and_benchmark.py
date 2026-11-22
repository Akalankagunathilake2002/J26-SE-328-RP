"""Spaced repetition, the lesson cache key, and the measured RAG benchmark's metrics
(app/services/edu_assistant.py, app/services/rag_evaluator.py)."""
from app.schemas.learning import LessonRequest
from app.services.edu_assistant import REVIEW_DAYS, _cache_key, next_box
from app.services.rag_evaluator import RAGEvaluatorService, context_precision, context_recall, permutation_p_value


def test_review_moves_up_when_right_and_restarts_when_wrong():
    assert REVIEW_DAYS == [1, 3, 7]
    assert next_box(0, True) == (1, 3, False)
    assert next_box(1, True) == (2, 7, False)
    assert next_box(2, True) == (3, None, True)       # answered right after 1, 3 and 7 days: done
    assert next_box(2, False) == (0, 1, False)


def test_lesson_cache_key_ignores_case_and_student():
    a = LessonRequest(student_id="s1", target_role="Backend Developer", topic=" JWT Auth ", level="beginner")
    b = LessonRequest(student_id="s2", target_role="Backend Developer", topic="jwt auth", level="beginner")
    c = LessonRequest(student_id="s1", target_role="Backend Developer", topic="jwt auth", level="advanced")
    assert _cache_key(a) == _cache_key(b) != _cache_key(c)
    assert _cache_key(LessonRequest(student_id="s", target_role="", topic="SQL"))[0] == "all"


def test_context_precision_is_reciprocal_rank_of_ground_truth():
    assert context_precision(["JWT Guide", "Other"], "JWT Guide") == 1.0
    assert context_precision(["Other", "Another", "JWT Guide"], "jwt guide") == round(1 / 3, 4)
    assert context_precision(["Other"], "JWT Guide") == 0.0          # no made-up partial credit


def test_context_recall_counts_keywords_in_context():
    assert context_recall("Tokens are signed with HMAC and expire.", ["signed", "expire", "refresh"]) == round(2 / 3, 4)
    assert context_recall("anything", []) is None


def test_permutation_p_value():
    assert permutation_p_value([0.5] * 20) < 0.001                     # consistent improvement
    assert permutation_p_value([0.3, -0.3] * 10) > 0.5                 # no effect
    assert permutation_p_value([0.1, 0.2]) is None                     # too few pairs


def test_summary_averages_only_measured_values():
    rows = [
        {"baseline": {"faithfulness": None, "answer_relevance": 0.5, "latency_ms": 100, "tokens": 50},
         "naive_rag": {"faithfulness": 0.5, "answer_relevance": 0.5, "context_precision": 0.0, "context_recall": 0.5,
                       "latency_ms": 200, "tokens": 300},
         "advanced_rag": {"faithfulness": 1.0, "answer_relevance": 1.0, "context_precision": 1.0, "context_recall": 1.0,
                          "latency_ms": 300, "tokens": 250, "compression_saved_percent": 20.0}},
        {"baseline": {"faithfulness": None, "answer_relevance": 1.0, "latency_ms": 300, "tokens": 50},
         "naive_rag": {"faithfulness": None, "answer_relevance": 1.0, "context_precision": 0.5, "context_recall": 1.0,
                       "latency_ms": 200, "tokens": 300},
         "advanced_rag": {"faithfulness": 0.5, "answer_relevance": 1.0, "context_precision": 1.0, "context_recall": 1.0,
                          "latency_ms": 300, "tokens": 250, "compression_saved_percent": 40.0}},
    ]
    res = RAGEvaluatorService.summarise(rows)
    assert res["summary"]["baseline"]["faithfulness"] is None
    assert res["summary"]["baseline"]["latency_ms"] == 200
    assert res["summary"]["naive_rag"]["faithfulness"] == 0.5          # the unjudged answer is left out
    assert res["faithfulness_pairs"] == 1 and res["p_value"] is None
    assert res["compression_saved_percent"] == 30.0


def test_local_llm_stream_yields_pieces(monkeypatch):
    """chat_stream parses OpenAI-style server-sent events from mlx_lm.server."""
    import asyncio
    import json
    import httpx
    from app.services import local_llm as module

    events = "".join(f"data: {json.dumps({'choices': [{'delta': {'content': t}}]})}\n\n" for t in ["Hel", "lo", "!"])
    events += "data: [DONE]\n\n"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "gemma"}]})
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(200, content=events.encode(), headers={"content-type": "text/event-stream"})

    real = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, "AsyncClient",
                        lambda *a, **k: real(*a, **{**k, "transport": httpx.MockTransport(handler)}))
    llm = module.LocalLLM()

    async def collect():
        return [p async for p in llm.chat_stream([{"role": "user", "content": "hi"}])]

    assert asyncio.run(collect()) == ["Hel", "lo", "!"]
