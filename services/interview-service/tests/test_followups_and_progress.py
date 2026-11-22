"""Overall score without camera cues, follow-up questions, the avatar's short first clip and progress
across interviews (evaluation_rag.py, interview_flow.py, avatar_service.py, progress.py)."""
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.avatar_service import split_for_streaming
from app.services.evaluation_rag import overall_score
from app.services.interview_flow import MAX_FOLLOW_UPS, follow_up_concept
from app.services.progress import summarise_progress


def test_overall_score_uses_answer_quality_only():
    assert overall_score(4.0, 3.0, 5.0) == round(4.0 * 0.7 + 3.0 * 0.15 + 5.0 * 0.15, 2)
    assert overall_score(5, 5, 5) == 5.0 and overall_score(1, 1, 1) == 1.0


def test_follow_up_only_after_a_weak_answer_with_a_missed_concept():
    assert follow_up_concept(2.5, ["connection timeouts", "pool size"], False, 0) == "connection timeouts"
    assert follow_up_concept(4.0, ["pool size"], False, 0) is None          # good answer: move on
    assert follow_up_concept(2.0, [], False, 0) is None                      # nothing specific to probe
    assert follow_up_concept(2.0, ["x"], True, 0) is None                    # never two in a row
    assert follow_up_concept(2.0, ["x"], False, MAX_FOLLOW_UPS) is None      # limit per interview
    assert follow_up_concept(None, ["x"], False, 0) is None                  # not evaluated


def test_first_avatar_clip_is_short():
    text = ("Thanks for that answer, it covered indexing well, but you missed how composite indexes are "
            "ordered and when they help. Let's move on.")
    clips = split_for_streaming(text)
    assert len(clips[0].split()) <= 12
    assert " ".join(clips) == " ".join(text.split())
    assert split_for_streaming("Tell me about yourself.") == ["Tell me about yourself."]


def _session(minutes_ago, role="Backend Developer"):
    return SimpleNamespace(id=uuid.uuid4(), target_role=role, experience_level="Entry Level",
                           created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago))


def _turn(session, tech, missing, topic="Databases"):
    return SimpleNamespace(session_id=session.id, technical_accuracy_score=tech, clarity_score=3,
                           explanation_quality_score=3, missing_concepts=missing, topic=topic)


def test_progress_trend_and_recurring_gaps():
    s1, s2, s3 = _session(300), _session(200), _session(100)
    turns = [_turn(s1, 2, ["Connection pooling", "indexes"]), _turn(s1, 2, ["connection pooling."]),
             _turn(s2, 4, ["Connection Pooling"]), _turn(s2, 4, [], topic="APIs")]
    res = summarise_progress("student", [s1, s2, s3], turns)
    assert [h["session_id"] for h in res["interviews"]] == [str(s1.id), str(s2.id)]   # s3: nothing answered
    assert res["trend"] == round(overall_score(4, 3, 3) - overall_score(2, 3, 3), 2)
    # Counted once per interview, whatever the spelling
    assert res["recurring_gaps"] == [{"concept": "Connection pooling", "interviews": 2}]
    assert res["weakest_topics"][0]["topic"] == "Databases"
