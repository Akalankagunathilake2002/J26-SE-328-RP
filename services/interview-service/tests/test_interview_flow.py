"""Interview structure: welcome and introductions, role questions within the time budget, closing
(app/services/interview_flow.py)."""
from datetime import datetime, timedelta, timezone

from app.services.interview_flow import first_name, next_phase, welcome_text

START = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)


def at(minutes: float) -> datetime:
    return START + timedelta(minutes=minutes)


def test_opens_with_welcome_then_a_follow_up_in_longer_interviews():
    assert next_phase([], at(0), START, 25) == "intro"
    assert next_phase([("intro", at(0))], at(2), START, 25) == "intro"
    assert next_phase([("intro", at(0)), ("intro", at(2))], at(4), START, 25) == "core"


def test_short_interview_has_one_introduction_turn():
    assert next_phase([("intro", at(0))], at(2), START, 15) == "core"


def test_role_questions_continue_while_time_allows():
    turns = [("intro", at(0)), ("intro", at(2)), ("core", at(4)), ("core", at(7.5))]
    assert next_phase(turns, at(11), START, 25) == "core"


def test_closes_when_another_question_would_overrun():
    # 3.5 minutes per question so far; at 20 minutes another one leaves too little time for the closing
    turns = [("intro", at(0)), ("intro", at(2))] + [("core", at(4 + 3.5 * i)) for i in range(4)]
    assert next_phase(turns, at(20), START, 25) == "closing"


def test_minimum_role_questions_even_when_slow():
    turns = [("intro", at(0)), ("intro", at(5)), ("core", at(14))]
    assert next_phase(turns, at(24), START, 25) == "core"


def test_closing_ends_the_interview():
    turns = [("intro", at(0)), ("core", at(3)), ("core", at(6)), ("closing", at(9))]
    assert next_phase(turns, at(10), START, 15) == "done"


def test_greeting_uses_first_name_but_not_an_email():
    assert first_name("Nimal Perera") == "Nimal"
    assert first_name("nimal@example.com") == ""
    text = welcome_text("Nimal Perera", "Backend Developer", "Entry Level", 25)
    assert text.startswith("Hi Nimal, welcome") and "25 minutes" in text and "technical" in text
    assert "role-related" in welcome_text(None, "HR Manager", "Mid Level", 20)
