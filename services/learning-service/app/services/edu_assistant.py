"""Skillaro Edu Assistant: a friendly tutor that chats, suggests topics and teaches them in three stages.

Each stage covers two levels of Bloom's taxonomy (revised, Anderson & Krathwohl 2001), from recalling
facts up to creating something new, and ends with a check at those levels:

  beginner      Remember, Understand   lesson in plain language + MCQs + "explain in your own words"
  intermediate  Apply, Analyze         worked examples + scenario MCQs + an analysis question
  advanced      Evaluate, Create       trade-offs + a judgement MCQ + justify and design questions

Everything is grounded in the curriculum through the same retrieval as the learning query
(learning_rag.retrieve_context). MCQs are graded in the browser; open answers by grade_answer.
"""
import random
import re
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import LearningDocument
from app.schemas.learning import (
    EduChatRequest, EduChatResponse, GradeAnswerRequest, GradeAnswerResponse, LessonRequest, LessonResponse,
    LessonSection, MultipleChoiceQuestion, OpenQuestion, QuizRequest, QuizResponse,
)
from app.services.learning_rag import LLMUnavailable, learning_rag_service

ASSISTANT = "Skillaro"

# What each Bloom level asks the student to do (the verbs the questions are written around)
BLOOM_VERBS = {
    "Remember": "recall facts and terms (define, list, identify)",
    "Understand": "explain ideas in their own words (explain, summarise, compare)",
    "Apply": "use the idea in a new situation (apply, implement, solve)",
    "Analyze": "break a situation down and find causes or relationships (differentiate, diagnose)",
    "Evaluate": "judge and justify a choice between options (critique, choose, defend)",
    "Create": "design or propose something new (design, plan, build)",
}

STAGES: Dict[str, Dict[str, Any]] = {
    "beginner": {
        "bloom": ["Remember", "Understand"],
        "mcqs": ["Remember", "Remember", "Understand"],
        "open": ["Understand"],
        "teaching": "Start from zero: plain language, define every term, use an everyday analogy. No jargon "
                    "without explaining it.",
    },
    "intermediate": {
        "bloom": ["Apply", "Analyze"],
        "mcqs": ["Apply", "Apply", "Analyze"],
        "open": ["Analyze"],
        "teaching": "Assume the basics. Show how it is used in real work: a worked example step by step, "
                    "common mistakes and how to spot them.",
    },
    "advanced": {
        "bloom": ["Evaluate", "Create"],
        "mcqs": ["Evaluate"],
        "open": ["Evaluate", "Create"],
        "teaching": "Go deep: trade-offs between approaches, when each one is the right choice, how experts "
                    "design with it at scale, and pitfalls in production.",
    },
}

HISTORY_TURNS = 6           # earlier chat messages sent to the model


def _clean(text: Any) -> str:
    return re.sub(r"\s+\n", "\n", str(text or "")).strip()


async def role_topics(db: AsyncSession, target_role: str) -> List[str]:
    """Curriculum topics for a role (the same role filter as retrieval), most documents first."""
    stmt = select(LearningDocument.topic)
    if target_role:
        stmt = stmt.where(or_(LearningDocument.target_role.ilike(f"%{target_role}%"),
                              LearningDocument.target_role.ilike("%all%")))
    counts: Dict[str, int] = {}
    for (topic,) in (await db.execute(stmt)).all():
        counts[topic] = counts.get(topic, 0) + 1
    return sorted(counts, key=lambda t: -counts[t])


def _match_topics(names: List[Any], available: List[str], limit: int = 3) -> List[str]:
    """Keeps suggested topics that exist in the curriculum (case-insensitive), so each one can be taught."""
    by_lower = {t.lower(): t for t in available}
    out: List[str] = []
    for n in names:
        t = by_lower.get(str(n).strip().lower())
        if t and t not in out:
            out.append(t)
    return out[:limit]


async def chat(db: AsyncSession, req: EduChatRequest) -> EduChatResponse:
    t0 = time.perf_counter()
    history = req.history[-HISTORY_TURNS:]
    # Short follow-ups ("why?", "give an example") are retrieved with the previous question for context
    last_user = next((m.content for m in reversed(history) if m.role == "user"), "")
    query = req.message if len(req.message.split()) > 5 else f"{last_user} {req.message}"
    if req.current_topic:
        query = f"{req.current_topic}: {query}"
    ctx = await learning_rag_service.retrieve_context(db, query, req.target_role)
    topics = await role_topics(db, req.target_role)

    # The account name falls back to an e-mail address, which isn't a name to greet
    name = req.student_name.split()[0] if req.student_name and "@" not in req.student_name else ""
    system = (
        f"You are {ASSISTANT}, a warm, encouraging Edu Assistant and tutor for a student preparing for a "
        f"{req.target_role or 'software'} career. Talk like a friendly teacher in a chat: short paragraphs, "
        "simple words, an example when it helps, and a question back to the student when it moves the "
        "conversation forward. Greet them only if they greet you."
        + (f" The student's name is {name}." if name else "")
        + f"\nTheir skills: {', '.join(req.current_skills) or 'not given'}. "
        f"Learning priority: {req.learning_priority or 'none set'}."
        + (f"\nThey are currently learning: {req.current_topic}." if req.current_topic else "")
        + "\n\nGround facts in the curriculum context below and mention the source title when you use it. "
        "If the context doesn't cover the question, say so briefly and answer from general knowledge, "
        "labelled as such.\n"
        f"Curriculum topics you can teach as full lessons: {', '.join(topics[:40])}.\n"
        "Return JSON: {\"reply\": string (markdown allowed: **bold**, lists, `code`), "
        "\"suggested_topics\": up to 3 topic names copied exactly from that list that would help next "
        "(empty if none fit)}.\n\n"
        f"CURRICULUM CONTEXT:\n{ctx['context']}"
    )
    convo = "\n".join(f"{'Student' if m.role == 'user' else ASSISTANT}: {m.content[:1500]}" for m in history)
    user = (f"Conversation so far:\n{convo}\n\n" if convo else "") + f"Student: {req.message}"
    try:
        data = await learning_rag_service.generate_json(system, user, max_tokens=800, temperature=0.4)
        reply = _clean(data.get("reply"))
        suggested = _match_topics(data.get("suggested_topics") or [], topics)
    except LLMUnavailable as e:
        print(f"[Warning] Edu chat without LLM: {e}")
        reply, suggested = "", []
    if not reply:
        top = ctx["items"][0] if ctx["items"] else None
        reply = (f"I can't reach my language model right now, but here is what the curriculum says in "
                 f"**{top['title']}**:\n\n{top['content'][:700]}" if top else
                 "I can't reach my language model right now and found nothing on that in the curriculum. "
                 "Try again in a moment.")
    return EduChatResponse(reply=reply, suggested_topics=suggested, sources=ctx["sources"],
                           latency_ms=round((time.perf_counter() - t0) * 1000, 1))


async def lesson(db: AsyncSession, req: LessonRequest) -> LessonResponse:
    t0 = time.perf_counter()
    stage = STAGES[req.level]
    ctx = await learning_rag_service.retrieve_context(
        db, f"{req.topic} {' '.join(stage['bloom'])} explained with examples", req.target_role)
    goals = "; ".join(f"{b}: {BLOOM_VERBS[b]}" for b in stage["bloom"])
    system = (
        f"You are {ASSISTANT}, a friendly, patient teacher. Write the {req.level} lesson on \"{req.topic}\" "
        f"for a student aiming to become a {req.target_role}. Their skills: "
        f"{', '.join(req.current_skills) or 'not given'}.\n"
        f"Bloom's taxonomy goals for this lesson: {goals}. By the end the student should be able to do "
        "exactly these.\n"
        f"Teaching approach: {stage['teaching']}\n"
        "Speak to the student directly and warmly, like a good teacher in class. Ground the facts in the "
        "curriculum context below.\n"
        "Return JSON: {\"title\": string, \"introduction\": 2-3 sentences on what they'll learn and why it "
        "matters for the role, \"sections\": 2-4 objects {\"heading\": string, \"body\": string, markdown "
        "allowed}, \"key_points\": 3-5 short strings, \"example\": one concrete example or analogy}.\n\n"
        f"CURRICULUM CONTEXT:\n{ctx['context']}"
    )
    try:
        data = await learning_rag_service.generate_json(system, f"Teach me {req.topic} ({req.level}).",
                                                        max_tokens=1400, temperature=0.3)
    except LLMUnavailable as e:
        raise LLMUnavailable(f"{ASSISTANT} can't prepare the lesson right now. {e}") from e
    sections = [LessonSection(heading=_clean(s.get("heading")) or "Lesson", body=_clean(s.get("body")))
                for s in data.get("sections") or [] if isinstance(s, dict) and s.get("body")]
    if not sections:
        raise LLMUnavailable(f"{ASSISTANT}'s lesson came back empty. Try again.")
    return LessonResponse(
        topic=req.topic, level=req.level, bloom_levels=stage["bloom"],
        title=_clean(data.get("title")) or f"{req.topic}: {req.level.title()}",
        introduction=_clean(data.get("introduction")),
        sections=sections,
        key_points=[_clean(k) for k in data.get("key_points") or [] if _clean(k)][:6],
        example=_clean(data.get("example")) or None,
        sources=ctx["sources"],
        latency_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


def valid_mcq(item: Any, bloom: str, rng: random.Random) -> Optional[MultipleChoiceQuestion]:
    """Four distinct options with one correct answer, shuffled (models tend to put the answer first)."""
    if not isinstance(item, dict):
        return None
    options = [_clean(o) for o in item.get("options") or []]
    try:
        answer = int(item.get("answer_index"))
    except (TypeError, ValueError):
        return None
    if len(options) != 4 or len({o.lower() for o in options}) != 4 or not all(options) or not 0 <= answer < 4:
        return None
    question = _clean(item.get("question"))
    if not question:
        return None
    correct = options[answer]
    rng.shuffle(options)
    return MultipleChoiceQuestion(question=question, options=options, answer_index=options.index(correct),
                                  explanation=_clean(item.get("explanation")), bloom_level=bloom)


async def quiz(db: AsyncSession, req: QuizRequest) -> QuizResponse:
    t0 = time.perf_counter()
    stage = STAGES[req.level]
    ctx = await learning_rag_service.retrieve_context(db, f"{req.topic} {' '.join(req.key_points[:4])}",
                                                      req.target_role)
    mcq_spec = ", ".join(f"{n} {b}" for b, n in _count(stage["mcqs"]).items())
    open_spec = ", ".join(stage["open"])
    system = (
        f"You are {ASSISTANT}, a teacher writing a short check after the {req.level} lesson on \"{req.topic}\" "
        f"for a future {req.target_role}.\n"
        + (f"The lesson's key points: {'; '.join(req.key_points)}.\n" if req.key_points else "")
        + "Write questions at these Bloom's taxonomy levels: "
        + "; ".join(f"{b} = {BLOOM_VERBS[b]}" for b in stage["bloom"]) + ".\n"
        f"Multiple-choice questions: {mcq_spec}. Each has exactly 4 options, one correct, and plausible "
        "wrong options based on common misconceptions; Apply/Analyze/Evaluate questions use a short realistic "
        "scenario.\n"
        f"Open (written) questions: {open_spec}. Each needs guidance: the points a good answer covers.\n"
        "Ground everything in the curriculum context below.\n"
        "Return JSON: {\"mcqs\": [{\"question\", \"options\": [4 strings], \"answer_index\": 0-3, "
        "\"explanation\": why the answer is right, \"bloom_level\"}], \"open_questions\": [{\"question\", "
        "\"bloom_level\", \"guidance\"}]}.\n\n"
        f"CURRICULUM CONTEXT:\n{ctx['context']}"
    )
    try:
        data = await learning_rag_service.generate_json(system, f"Quiz on {req.topic} ({req.level}).",
                                                        max_tokens=1400, temperature=0.3)
    except LLMUnavailable as e:
        raise LLMUnavailable(f"{ASSISTANT} can't write the quiz right now. {e}") from e

    rng = random.Random()
    mcqs = []
    for i, item in enumerate(data.get("mcqs") or []):
        bloom = item.get("bloom_level") if isinstance(item, dict) and item.get("bloom_level") in stage["bloom"] \
            else stage["mcqs"][min(i, len(stage["mcqs"]) - 1)]
        q = valid_mcq(item, bloom, rng)
        if q:
            mcqs.append(q)
    opens = []
    for i, item in enumerate(data.get("open_questions") or []):
        if isinstance(item, dict) and _clean(item.get("question")):
            bloom = item.get("bloom_level") if item.get("bloom_level") in stage["bloom"] \
                else stage["open"][min(i, len(stage["open"]) - 1)]
            opens.append(OpenQuestion(question=_clean(item["question"]), bloom_level=bloom,
                                      guidance=_clean(item.get("guidance"))))
    if not mcqs and not opens:
        raise LLMUnavailable(f"{ASSISTANT}'s quiz came back unusable. Try again.")
    return QuizResponse(topic=req.topic, level=req.level, mcqs=mcqs[:len(stage["mcqs"])],
                        open_questions=opens[:len(stage["open"])],
                        latency_ms=round((time.perf_counter() - t0) * 1000, 1))


def verdict(score: int) -> str:
    return "excellent" if score >= 85 else "good" if score >= 65 else "partial" if score >= 40 else "needs_work"


async def grade_answer(req: GradeAnswerRequest) -> GradeAnswerResponse:
    system = (
        f"You are {ASSISTANT}, a supportive teacher marking a student's written answer on \"{req.topic}\" "
        f"({req.level} level, Bloom's taxonomy level {req.bloom_level}: {BLOOM_VERBS.get(req.bloom_level, '')}).\n"
        f"Question: {req.question}\n"
        + (f"A good answer covers: {req.guidance}\n" if req.guidance else "")
        + "Score 0-100 for how well the answer meets the question at that Bloom level (for Create and "
        "Evaluate, reward sound reasoning and justified choices, not one fixed answer). Be fair and specific.\n"
        "Return JSON: {\"score\": integer, \"feedback\": 2-3 encouraging sentences on what was good and what "
        "to add, \"model_answer\": a short model answer}."
    )
    try:
        data = await learning_rag_service.generate_json(system, f"Student's answer: {req.answer}",
                                                        max_tokens=600, temperature=0.2)
        score = max(0, min(100, int(float(data.get("score")))))
    except LLMUnavailable as e:
        raise LLMUnavailable(f"{ASSISTANT} can't mark this right now. {e}") from e
    except (TypeError, ValueError) as e:
        raise LLMUnavailable(f"{ASSISTANT}'s marking came back without a score. Try again.") from e
    return GradeAnswerResponse(score=score, verdict=verdict(score), feedback=_clean(data.get("feedback")),
                               model_answer=_clean(data.get("model_answer")))


def _count(items: List[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return out
