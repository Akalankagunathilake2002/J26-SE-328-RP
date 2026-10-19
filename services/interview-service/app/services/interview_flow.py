"""The shape of an interview: welcome and introductions, role questions while time allows, then a closing.

The server decides each turn's phase from the turns so far and the time used, so a hands-free interview
keeps to its planned length (chosen at setup, 25 minutes by default) without the frontend counting:

  intro    "Hi, welcome... tell me about yourself", then one follow-up on what they said (not scored)
  core     scored role questions (interview_rag.py); at least INTERVIEW_MIN_QUESTIONS, at most MAX
  closing  "Do you have any questions for me?"; the reply to their answer is the goodbye
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.roles import is_technical
from app.models.interview import InterviewSession, InterviewTurn
from app.schemas.interview import InterviewQuestionResponse
from app.services.interview_rag import interview_rag_service

CLOSING_RESERVE_S = 150          # time kept for the closing question, their answer and the goodbye
DEFAULT_CORE_CYCLE_S = 210       # one role question: asked, answered, evaluated, feedback spoken


def intro_turns_planned(duration_minutes: int) -> int:
    """Welcome + 'tell me about yourself', and in longer interviews one follow-up on their answer."""
    return 2 if duration_minutes >= 20 else 1


def next_phase(turns: Sequence[Tuple[str, datetime]], now: datetime, started: datetime,
               duration_minutes: int) -> str:
    """Phase of the next interviewer turn: "intro", "core", "closing" or "done".

    turns: (phase, created_at) of the turns so far, oldest first.
    """
    phases = [p for p, _ in turns]
    if "closing" in phases:
        return "done"
    core = [t for p, t in turns if p == "core"]
    if not core and phases.count("intro") < intro_turns_planned(duration_minutes):
        return "intro"
    if len(core) < settings.INTERVIEW_MIN_QUESTIONS:
        return "core"
    if len(core) >= settings.INTERVIEW_MAX_QUESTIONS:
        return "closing"
    # Average time per role question so far (each one is answered by the time the next is asked)
    cycle = (now - core[0]).total_seconds() / len(core)
    remaining = duration_minutes * 60 - (now - started).total_seconds()
    return "core" if remaining - max(cycle, 60) >= CLOSING_RESERVE_S else "closing"


def first_name(name: Optional[str]) -> str:
    """First name for a greeting; an e-mail address (the fallback account name) isn't one."""
    if not name or "@" in name:
        return ""
    return name.strip().split()[0]


def welcome_text(name: Optional[str], role: str, level: str, minutes: int) -> str:
    who = first_name(name)
    kind = "technical" if is_technical(role) else "role-related"
    return (
        f"Hi{' ' + who if who else ''}, welcome, and thank you for joining me today. "
        f"I'm {settings.INTERVIEWER_NAME}, and I'll be interviewing you for the {level} {role} position. "
        f"We have about {minutes} minutes. We'll start with a little about you, then I'll ask some {kind} "
        f"questions, and at the end you'll have time to ask me anything. "
        f"To start, could you tell me a little about yourself?"
    )


def closing_text(name: Optional[str]) -> str:
    who = first_name(name)
    return (
        f"Alright{', ' + who if who else ''}, that brings us to the end of my questions. "
        "Before we wrap up, do you have any questions for me about the role or about this interview?"
    )


async def _follow_up_text(session: InterviewSession) -> str:
    """The second introduction question, built on what they said about themselves."""
    prompt = (
        f"You are {settings.INTERVIEWER_NAME}, a friendly interviewer for a {session.experience_level} "
        f"{session.target_role} position. You asked the candidate to tell you about themselves. They said:\n"
        f"{(session.candidate_intro or '')[:1500]}\n\n"
        "Ask ONE warm follow-up question to get to know them better: what draws them to this role, or a "
        "project or experience they mentioned. Refer to something specific they said. Don't assess them and "
        "don't ask a technical question. It will be spoken aloud: plain conversational sentences, no lists "
        "or quotes, under 30 words."
    )
    return (await interview_rag_service.complete(prompt, temperature=0.5)
            or f"Thank you. What interests you most about working as a {session.target_role}?")


async def create_turn(db: AsyncSession, session: InterviewSession, phase: str) -> InterviewQuestionResponse:
    """Records and returns an introduction or closing turn."""
    if phase == "intro":
        intro_count = len((await db.execute(
            select(InterviewTurn.id).where(InterviewTurn.session_id == session.id, InterviewTurn.phase == "intro")
        )).all())
        minutes = session.duration_minutes or settings.INTERVIEW_DEFAULT_MINUTES
        text = (welcome_text(session.candidate_name, session.target_role, session.experience_level, minutes)
                if intro_count == 0 else await _follow_up_text(session))
        topic, reason = "Introduction", "Getting to know you. This part isn't scored."
    else:
        text = closing_text(session.candidate_name)
        topic, reason = "Closing", "Your chance to ask the interviewer a question. This part isn't scored."
    turn = InterviewTurn(session_id=session.id, phase=phase, question=text, topic=topic,
                         difficulty=session.experience_level)
    db.add(turn)
    await db.commit()
    return InterviewQuestionResponse(turn_id=str(turn.id), session_id=str(session.id), phase=phase,
                                     question=text, topic=topic, difficulty=session.experience_level,
                                     context_or_reason=reason, rubric_criteria=[])


async def plan(db: AsyncSession, session: InterviewSession) -> str:
    rows = (await db.execute(
        select(InterviewTurn.phase, InterviewTurn.created_at)
        .where(InterviewTurn.session_id == session.id).order_by(InterviewTurn.created_at.asc())
    )).all()
    now = datetime.now(timezone.utc)
    return next_phase([(p, _aware(t)) for p, t in rows], now, _aware(session.created_at),
                      session.duration_minutes or settings.INTERVIEW_DEFAULT_MINUTES)


def _aware(t: datetime) -> datetime:
    # created_at defaults to datetime.utcnow (naive) before the database round-trips it
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


async def reply_to(db: AsyncSession, turn: InterviewTurn, transcript: str) -> Tuple[str, bool]:
    """What the interviewer says after an introduction or closing answer; True when it is the goodbye."""
    session = await db.get(InterviewSession, turn.session_id)
    turn.transcript = transcript
    who = first_name(session.candidate_name)
    if turn.phase == "intro":
        session.candidate_intro = f"{session.candidate_intro or ''} {transcript}".strip()[-3000:]
        prompt = (
            f"You are {settings.INTERVIEWER_NAME}, a friendly interviewer. You asked: {turn.question}\n"
            f"The candidate answered: {transcript[:1500]}\n\n"
            "Acknowledge their answer warmly in ONE short sentence that mentions something specific they said. "
            "Don't ask a question and don't evaluate it. Plain spoken words, under 25 words."
        )
        reply = await interview_rag_service.complete(prompt, temperature=0.5) or "Thank you, that's helpful to know."
        done = False
    else:
        prompt = (
            f"You are {settings.INTERVIEWER_NAME}, ending a practice interview for a {session.experience_level} "
            f"{session.target_role} position. You asked if the candidate has any questions for you. "
            f"They said: {transcript[:1500]}\n\n"
            "If they asked something, answer it briefly and honestly. This is a practice interview with no real "
            "company, so don't invent company facts: talk about what the role usually involves or how to prepare. "
            f"Then thank {who or 'them'} for their time, say their detailed feedback report is ready next, and say "
            "goodbye warmly. Plain spoken sentences, no lists, under 80 words."
        )
        reply = await interview_rag_service.complete(prompt, temperature=0.5, max_tokens=400) or (
            f"Thank you so much for your time today{', ' + who if who else ''}. Your detailed feedback report "
            "is ready next. Best of luck with your preparation, and goodbye for now!")
        session.status = "completed"
        done = True
    await db.commit()
    return reply, done


async def conversation(db: AsyncSession, session_id: uuid.UUID) -> List[dict]:
    """Introduction and closing exchanges, for the report."""
    rows = (await db.execute(
        select(InterviewTurn).where(InterviewTurn.session_id == session_id, InterviewTurn.phase != "core")
        .order_by(InterviewTurn.created_at.asc())
    )).scalars().all()
    return [{"phase": t.phase, "question": t.question, "answer": t.transcript} for t in rows]
