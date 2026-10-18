import uuid
import json
import random
import re
import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.interview import InterviewDocument, InterviewChunk, InterviewSession, InterviewTurn
from app.services.embedding_service import embedding_service
from app.core.config import settings
from app.schemas.interview import QuestionGenerationRequest, InterviewQuestionResponse

QUESTION_POOL = 60        # closest bank items considered per question
QUESTION_SHORTLIST = 6    # the pick is random among this many of the best remaining matches


class InterviewRAGService:
    def __init__(self):
        self._gemini_client = None
        self._llm = None
        self._init_llm()

    def _init_llm(self):
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=settings.LLM_MODEL,
                    temperature=0.3,
                    api_key=settings.OPENAI_API_KEY
                )
            except Exception as e:
                print(f"[Warning] Failed to init LLM in interview service: {e}")
                self._llm = None
        elif settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self._llm = "gemini"
            except Exception as e:
                print(f"[Warning] Failed to init Gemini in interview service: {e}")
                self._gemini_client = None
                self._llm = None
        else:
            self._gemini_client = None
            self._llm = None

    async def generate_interview_question(
        self,
        session: AsyncSession,
        request: QuestionGenerationRequest
    ) -> InterviewQuestionResponse:
        """
        Retrieves interview technical concepts and rubrics from pgvector
        and generates a role-specific interview question.
        """
        # Formulate query from role, skills, and topic
        query_text = f"{request.target_role} {request.experience_level} {' '.join(request.current_skills)} {request.preferred_topic or ''}"
        query_vec = embedding_service.embed_text(query_text)

        # Retrieve matching chunks from interview_chunks
        stmt = (
            select(
                InterviewChunk.id,
                InterviewChunk.content,
                InterviewChunk.expected_answer,
                InterviewChunk.rubric,
                InterviewDocument.topic,
                InterviewDocument.difficulty,
                InterviewDocument.role,
                InterviewChunk.embedding.cosine_distance(query_vec).label("distance")
            )
            .join(InterviewDocument, InterviewChunk.document_id == InterviewDocument.id)
            .where(InterviewDocument.role.ilike(f"%{request.target_role}%"))
            .order_by("distance")
            # a wider pool so topic de-duplication and the level preference have room to work
            # a wide pool: with a large bank the same query would otherwise always pick the same few
            .limit(QUESTION_POOL)
        )
        result = await session.execute(stmt)
        candidates = result.all()

        # Skip topics already asked in this session, and questions this student got in earlier sessions
        # (turns store the bank item's reference answer, which identifies it)
        asked_res = await session.execute(
            select(InterviewTurn.topic).where(InterviewTurn.session_id == uuid.UUID(request.session_id))
        )
        asked_topics = {t for (t,) in asked_res.all() if t}
        seen_res = await session.execute(
            select(InterviewTurn.reference_answer)
            .join(InterviewSession, InterviewTurn.session_id == InterviewSession.id)
            .where(InterviewSession.student_id == select(InterviewSession.student_id)
                   .where(InterviewSession.id == uuid.UUID(request.session_id)).scalar_subquery())
            .where(InterviewTurn.reference_answer.isnot(None))
        )
        seen_refs = {r for (r,) in seen_res.all()}
        unseen = [c for c in candidates if (c.expected_answer or c.content) not in seen_refs]
        fresh = [c for c in (unseen or candidates) if c.topic not in asked_topics]
        # Prefer the candidate's chosen experience level, then any level
        at_level = [c for c in fresh if c.difficulty == request.experience_level]

        if candidates:
            # Random among the closest matches, so interviews vary while staying on the profile
            preferred = at_level or fresh or candidates
            selected = random.choice(preferred[:QUESTION_SHORTLIST])
            topic = selected.topic
            difficulty = selected.difficulty
            rubric_dict = selected.rubric if isinstance(selected.rubric, dict) else {}
            rubric_criteria = rubric_dict.get("criteria", [
                "Technical accuracy of foundational concepts",
                "Explanation of trade-offs and performance impact",
                "Clarity of terminology"
            ])
            expected_ref = selected.expected_answer or selected.content

            # Prompt LLM to phrase a natural interview question
            question_text = await self._generate_question_text(
                role=request.target_role,
                level=request.experience_level,
                topic=topic,
                skills=request.current_skills,
                reference_concept=selected.content,
                previous_question=request.previous_question,
                previous_answer=request.previous_answer,
                previous_missing=request.previous_missing_concepts,
                background=request.candidate_background,
            )
            context_or_reason = f"Evaluates your understanding of {topic} for an {request.experience_level} {request.target_role} position."
        else:
            # Fallback if knowledge base has not been seeded yet
            topic = request.preferred_topic or "API Architecture & Data Flow"
            difficulty = request.experience_level
            question_text = (
                f"In a production {request.target_role} environment, how would you design an authentication and connection pooling mechanism "
                f"to guarantee low latency and resource resilience under high concurrency?"
            )
            context_or_reason = f"Core competency question for {request.target_role} candidates."
            expected_ref = None
            rubric_criteria = [
                "Explains connection lifecycle and pooling",
                "Explains token verification without blocking",
                "Mentions resource exhaustion prevention"
            ]

        # Record interview turn in database
        turn = InterviewTurn(
            session_id=uuid.UUID(request.session_id),
            question=question_text,
            topic=topic,
            difficulty=difficulty,
            reference_answer=expected_ref,
            rubric_criteria=rubric_criteria,
        )
        session.add(turn)
        await session.commit()

        return InterviewQuestionResponse(
            turn_id=str(turn.id),
            session_id=request.session_id,
            question=question_text,
            topic=topic,
            difficulty=difficulty,
            context_or_reason=context_or_reason,
            rubric_criteria=rubric_criteria
        )

    async def _generate_question_text(
        self,
        role: str,
        level: str,
        topic: str,
        skills: List[str],
        reference_concept: str,
        previous_question: str | None = None,
        previous_answer: str | None = None,
        previous_missing: List[str] | None = None,
        background: str | None = None,
    ) -> str:
        from app.core.roles import is_technical
        technical = is_technical(role)
        interviewer = ("a Senior Technical Interviewer assessing" if technical
                       else "an experienced hiring manager interviewing")
        prompt = (
            f"You are {interviewer} a candidate for a {level} {role} position.\n"
            f"Candidate Skills: {', '.join(skills)}\n"
            + (f"Candidate background (from their CV): {background}\n"
               "Where it fits naturally, frame the scenario around their experience.\n" if background else "")
            + f"Topic: {topic}\n"
            f"Reference Concept:\n{reference_concept}\n\n"
        )
        if previous_question and previous_answer:
            prompt += (
                f"Previous question: {previous_question}\n"
                f"Candidate's answer: {previous_answer[:1500]}\n"
                + (f"Concepts the answer missed: {', '.join(previous_missing)}\n" if previous_missing else "")
                + "\nYou already gave spoken feedback on that answer, so don't assess it again. "
                "Open with a brief natural transition (e.g. 'Let's build on that.' or 'Moving on.'). "
                "If a missed concept relates to this topic, probe it.\n"
            )
        task = ("Formulate ONE clear, scenario-oriented technical interview question testing this concept." if technical
                else "Formulate ONE clear interview question for this role testing this competency or knowledge: either "
                     "behavioural (\"Tell me about a time...\") or situational (\"How would you handle...\"), "
                     "grounded in the reference concept.")
        prompt += (
            f"Task: {task} "
            "Do not ask multiple questions. Be direct and realistic. It will be spoken aloud by a video "
            "interviewer, so write plain conversational sentences: no markdown, lists, code or quotes. "
            "Keep it under 35 words in total, like a real interviewer speaking."
        )

        if settings.LLM_PROVIDER == "local":
            try:
                from app.services.local_llm import local_llm
                text = await local_llm.chat([{"role": "user", "content": prompt}], temperature=0.4, max_tokens=300)
                if text:
                    return re.sub(r"[`*_#>]+", "", text).strip().strip('"')
            except Exception as e:
                print(f"[Warning] Local LLM question generation error: {e}")
        elif self._llm == "gemini" and self._gemini_client:
            try:
                resp = self._gemini_client.models.generate_content(
                    model=settings.LLM_MODEL or "gemini-2.5-flash",
                    contents=prompt
                )
                return resp.text.strip().strip('"')
            except Exception as e:
                print(f"[Warning] Gemini Question generation error: {e}")
        elif self._llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                resp = await self._llm.ainvoke([HumanMessage(content=prompt)])
                return resp.content.strip().strip('"')
            except Exception as e:
                print(f"[Warning] Question LLM generation error: {e}")

        return f"Can you explain how {topic} operates in production, and how you would prevent common pitfalls when building services in {role}?"


interview_rag_service = InterviewRAGService()
