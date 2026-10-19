"""Skillaro Edu Assistant: Bloom stages, MCQ validation, marking bands (app/services/edu_assistant.py)."""
import random

from app.services.edu_assistant import STAGES, _match_topics, valid_mcq, verdict

MCQ = {"question": "What does a B-Tree index speed up?",
       "options": ["Range queries", "Image storage", "Network latency", "CPU caching"],
       "answer_index": 0, "explanation": "B-Trees keep keys sorted.", "bloom_level": "Remember"}


def test_stages_climb_blooms_taxonomy_in_order():
    order = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    levels = [b for stage in ("beginner", "intermediate", "advanced") for b in STAGES[stage]["bloom"]]
    assert levels == order
    for stage in STAGES.values():
        assert set(stage["mcqs"]) | set(stage["open"]) <= set(stage["bloom"])


def test_mcq_keeps_the_correct_answer_after_shuffling():
    for seed in range(20):
        q = valid_mcq(MCQ, "Remember", random.Random(seed))
        assert q.options[q.answer_index] == "Range queries"
        assert sorted(q.options) == sorted(MCQ["options"])


def test_invalid_mcqs_are_dropped():
    rng = random.Random(0)
    assert valid_mcq({**MCQ, "options": MCQ["options"][:3]}, "Remember", rng) is None
    assert valid_mcq({**MCQ, "answer_index": 4}, "Remember", rng) is None
    assert valid_mcq({**MCQ, "answer_index": "B"}, "Remember", rng) is None
    assert valid_mcq({**MCQ, "options": ["A", "a", "B", "C"]}, "Remember", rng) is None
    assert valid_mcq({**MCQ, "question": " "}, "Remember", rng) is None


def test_marking_bands():
    assert [verdict(s) for s in (95, 85, 70, 50, 10)] == ["excellent", "excellent", "good", "partial", "needs_work"]


def test_suggested_topics_must_exist_in_the_curriculum():
    available = ["Kubernetes Containers", "Database Indexing", "Git Basics"]
    assert _match_topics(["database indexing", "Quantum Computing", "Git Basics", "Git Basics"], available) == \
        ["Database Indexing", "Git Basics"]
