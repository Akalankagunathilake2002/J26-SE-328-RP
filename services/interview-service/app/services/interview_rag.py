import uuid
import json
import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.interview import InterviewDocument, InterviewChunk, InterviewSession, InterviewTurn
from app.services.embedding_service import embedding_service
from app.core.config import settings
from app.schemas.interview import QuestionGenerationRequest, InterviewQuestionResponse


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
            .limit(settings.TOP_K)
        )
        result = await session.execute(stmt)
        candidates = result.all()

        if candidates:
            selected = candidates[0]
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
                reference_concept=selected.content
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
            difficulty=difficulty
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
        reference_concept: str
    ) -> str:
        prompt = (
            f"You are a Senior Technical Interviewer assessing a candidate for a {level} {role} position.\n"
            f"Candidate Skills: {', '.join(skills)}\n"
            f"Topic: {topic}\n"
            f"Reference Concept:\n{reference_concept}\n\n"
            f"Task: Formulate ONE clear, scenario-oriented technical interview question testing this concept. "
            f"Do not ask multiple questions. Be direct and realistic."
        )

        if self._llm == "gemini" and self._gemini_client:
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
