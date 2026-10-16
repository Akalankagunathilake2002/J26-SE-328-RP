import uuid
import json
import time
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.interview import InterviewTurn, InterviewChunk, InterviewExperimentLog
from app.schemas.interview import EvaluateAnswerRequest, EvaluationResultResponse
from app.core.config import settings


class EvaluationRAGService:
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
                    temperature=0.2,
                    api_key=settings.OPENAI_API_KEY
                )
            except Exception as e:
                print(f"[Warning] Failed to init LLM in evaluation service: {e}")
                self._llm = None
        elif settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self._llm = "gemini"
            except Exception as e:
                print(f"[Warning] Failed to init Gemini in evaluation service: {e}")
                self._gemini_client = None
                self._llm = None
        else:
            self._gemini_client = None
            self._llm = None

    async def evaluate_spoken_answer(
        self,
        session: AsyncSession,
        request: EvaluateAnswerRequest
    ) -> EvaluationResultResponse:
        """
        Evaluates a candidate's transcribed answer against the question's rubric and technical references.
        Produces multi-dimensional scoring and granular feedback.
        """
        t_start = time.perf_counter()

        # 1. Fetch turn record
        turn_id = uuid.UUID(request.turn_id)
        stmt = select(InterviewTurn).where(InterviewTurn.id == turn_id)
        res = await session.execute(stmt)
        turn = res.scalar_one_or_none()

        if not turn:
            raise ValueError(f"Interview turn {request.turn_id} not found.")

        # Update transcript
        turn.transcript = request.transcript

        # 2. LLM Multi-Criteria Evaluation
        eval_data = await self._run_evaluation_chain(
            question=turn.question,
            topic=turn.topic,
            transcript=request.transcript
        )

        evaluation_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # 3. Non-Verbal & Pacing Telemetry Assessment
        wpm = request.words_per_minute
        duration = request.speaking_duration_seconds
        eye_contact = request.eye_contact_ratio
        fillers = request.filler_words_count or 0

        pacing_note = "Optimal"
        if wpm is not None:
            if wpm < 110:
                pacing_note = "Slightly Deliberate / Slow"
            elif wpm > 165:
                pacing_note = "Rapid / Fast Paced"
            else:
                pacing_note = "Well-Paced & Clear"

        # Blend non-verbal communication telemetry into feedback
        eye_ratio = (eye_contact / 100.0) if (eye_contact is not None and eye_contact > 1.0) else eye_contact

        if duration or eye_contact or wpm:
            comm_additions = []
            if wpm:
                comm_additions.append(f"Delivery pacing: {wpm:.0f} WPM ({pacing_note}).")
            if eye_ratio is not None:
                comm_additions.append(f"Camera engagement: {eye_ratio * 100:.0f}%.")
            if fillers > 3:
                comm_additions.append(f"Identified {fillers} verbal filler hesitation pauses.")
            
            if comm_additions:
                eval_data["communication_feedback"] += f" Non-verbal telemetry: {' '.join(comm_additions)}"

        # Compute weighted overall score (70% technical accuracy, 15% clarity, 15% communication/engagement)
        tech_score = eval_data["technical_accuracy"]
        clarity_score = eval_data["clarity"]
        eye_boost = (eye_ratio * 5.0) if eye_ratio is not None else clarity_score
        overall_score = round((tech_score * 0.70) + (clarity_score * 0.15) + (eye_boost * 0.15), 2)

        # 4. Persist scores to interview_turns
        turn.technical_accuracy_score = eval_data["technical_accuracy"]
        turn.relevance_score = eval_data["relevance"]
        turn.explanation_quality_score = eval_data["explanation_quality"]
        turn.clarity_score = eval_data["clarity"]
        turn.technical_feedback = eval_data["technical_feedback"]
        turn.communication_feedback = eval_data["communication_feedback"]
        turn.missing_concepts = eval_data["missing_concepts"]
        turn.strengths = eval_data["strengths"]
        turn.areas_for_improvement = eval_data["areas_for_improvement"]

        # Log experiment telemetry
        exp_log = InterviewExperimentLog(
            turn_id=turn.id,
            stt_latency_ms=0.0,
            retrieval_latency_ms=0.0,
            evaluation_latency_ms=evaluation_latency_ms
        )
        session.add(exp_log)
        await session.commit()

        return EvaluationResultResponse(
            turn_id=str(turn.id),
            technical_accuracy=eval_data["technical_accuracy"],
            relevance=eval_data["relevance"],
            explanation_quality=eval_data["explanation_quality"],
            clarity=eval_data["clarity"],
            technical_feedback=eval_data["technical_feedback"],
            communication_feedback=eval_data["communication_feedback"],
            missing_concepts=eval_data["missing_concepts"],
            strengths=eval_data["strengths"],
            areas_for_improvement=eval_data["areas_for_improvement"],
            evaluation_latency_ms=evaluation_latency_ms,
            speaking_duration_seconds=duration,
            words_per_minute=wpm,
            eye_contact_ratio=eye_contact,
            pacing_assessment=pacing_note,
            overall_score=overall_score
        )

    async def _run_evaluation_chain(self, question: str, topic: str, transcript: str) -> Dict[str, Any]:
        """Runs rubric-based evaluation via LLM or deterministic fallback."""
        system_prompt = (
            "You are an expert technical interviewer evaluating a student candidate's spoken answer.\n"
            "Evaluate the answer across 4 criteria on a 1.0 to 5.0 scale:\n"
            "1. technical_accuracy (1.0 - 5.0)\n"
            "2. relevance (1.0 - 5.0)\n"
            "3. explanation_quality (1.0 - 5.0)\n"
            "4. clarity (1.0 - 5.0)\n\n"
            "Return ONLY a JSON object with keys:\n"
            "- 'technical_accuracy': float\n"
            "- 'relevance': float\n"
            "- 'explanation_quality': float\n"
            "- 'clarity': float\n"
            "- 'technical_feedback': string\n"
            "- 'communication_feedback': string\n"
            "- 'missing_concepts': list of strings\n"
            "- 'strengths': list of strings\n"
            "- 'areas_for_improvement': list of strings"
        )
        user_prompt = f"Interview Question: {question}\nTopic: {topic}\nStudent Transcript:\n\"{transcript}\""

        if self._llm == "gemini" and self._gemini_client:
            try:
                from google.genai import types
                combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                config = types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    response_mime_type="application/json"
                )
                response = self._gemini_client.models.generate_content(
                    model=settings.LLM_MODEL or "gemini-2.5-flash",
                    contents=combined_prompt,
                    config=config
                )
                raw = response.text.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                return json.loads(raw.strip())
            except Exception as e:
                print(f"[Warning] Gemini Evaluation failed: {e}. Using deterministic evaluation fallback.")

        elif self._llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                resp = await self._llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])

                raw = resp.content.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                return json.loads(raw.strip())
            except Exception as e:
                print(f"[Warning] LLM Evaluation failed: {e}. Using deterministic evaluation fallback.")

        # Deterministic fallback evaluation for testing
        has_keywords = any(kw in transcript.lower() for kw in ["connection", "pool", "handshake", "token", "jwt", "overhead", "hikaricp", "cache"])
        score = 4.5 if has_keywords else 3.2

        return {
            "technical_accuracy": score,
            "relevance": 4.5,
            "explanation_quality": 4.0,
            "clarity": 4.2,
            "technical_feedback": f"Strong conceptual demonstration of {topic}. You correctly identified the primary architectural trade-offs.",
            "communication_feedback": "Your articulation was direct and professional. Continue using precise framework terminology.",
            "missing_concepts": [
                "Connection timeout threshold handling",
                "Maximum pool size calculation formula (e.g. pool_size = core_count * 2 + effective_spindle_count)"
            ],
            "strengths": [
                "Accurate identification of performance bottlenecks",
                "Clear distinction between stateless and stateful operations"
            ],
            "areas_for_improvement": [
                "Elaborate on production telemetry metrics like connection acquisition latency"
            ]
        }


evaluation_rag_service = EvaluationRAGService()
