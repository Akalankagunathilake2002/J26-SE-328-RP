import uuid
import json
import re
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.interview import InterviewTurn, InterviewChunk, InterviewExperimentLog, InterviewSession
from app.schemas.interview import EvaluateAnswerRequest, EvaluationResultResponse
from app.core.config import settings


class EvaluationError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


SCORE_KEYS = ("technical_accuracy", "relevance", "explanation_quality", "clarity")
LIST_KEYS = ("missing_concepts", "strengths", "areas_for_improvement")


def _validated(data: dict) -> dict:
    """Checks an LLM evaluation: the four scores must be present (clamped to 1-5); text and list
    fields are normalised. Raises if the model skipped a score, rather than guessing one."""
    out = dict(data)
    for k in SCORE_KEYS:
        try:
            out[k] = round(min(5.0, max(1.0, float(data[k]))), 1)
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"evaluation is missing a valid '{k}' score")
    for k in LIST_KEYS:
        v = data.get(k) or []
        out[k] = [str(x) for x in (v if isinstance(v, list) else [v])]
    for k in ("technical_feedback", "communication_feedback", "spoken_feedback"):
        out[k] = str(data.get(k) or "")
    if not out["technical_feedback"]:
        raise ValueError("evaluation is missing technical_feedback")
    return out


def _speakable(text: str) -> str:
    """Strip markdown the voice would read out or stumble on (`code`, **bold**, # headings)."""
    return re.sub(r"\s+", " ", re.sub(r"[`*_#>]+", "", text or "")).strip()


def _first_sentences(text: str, max_words: int = 40) -> str:
    """Short spoken version of written feedback, used if the LLM gives no spoken_feedback."""
    words, out = 0, []
    for sentence in text.replace("\n", " ").split(". "):
        n = len(sentence.split())
        if out and words + n > max_words:
            break
        out.append(sentence.strip().rstrip("."))
        words += n
    return (". ".join(out) + ".") if out else ""


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
            raise EvaluationError(f"Interview turn {request.turn_id} not found.", status_code=404)

        # Update transcript
        turn.transcript = request.transcript

        # 2. LLM Multi-Criteria Evaluation (criteria depend on whether the role is technical)
        interview = await session.get(InterviewSession, turn.session_id)
        role = interview.target_role if interview else None
        eval_data = await self._run_evaluation_chain(
            question=turn.question,
            topic=turn.topic,
            transcript=request.transcript,
            reference_answer=turn.reference_answer,
            rubric_criteria=turn.rubric_criteria,
            role=role,
        )
        # Technical accuracy from the trained scorer / calibration when the mode says so (scripts/training)
        from app.services.answer_scorer import answer_scorer
        llm_technical = eval_data["technical_accuracy"]
        eval_data["technical_accuracy"], scoring_method = answer_scorer.technical_accuracy(
            llm_technical, turn.question, turn.reference_answer, request.transcript, role=role)

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

        # Observable delivery cues only; no emotion or mood is inferred from the face
        comm_additions = []
        if wpm:
            comm_additions.append(f"Pace {wpm:.0f} words per minute ({pacing_note}).")
        if fillers > 3:
            comm_additions.append(f"{fillers} filler words.")
        if request.pause_ratio is not None and request.pause_ratio > 0.35:
            comm_additions.append(f"Silent for {request.pause_ratio * 100:.0f}% of the answer; aim for fewer long pauses.")
        if eye_ratio is not None:
            comm_additions.append(f"Looked at the camera {eye_ratio * 100:.0f}% of the time"
                                  + ("." if eye_ratio >= 0.6 else "; try to look at the camera more, as you would at an interviewer."))
        if request.face_visible_ratio is not None and request.face_visible_ratio < 0.8:
            comm_additions.append(f"Your face was out of view {100 - request.face_visible_ratio * 100:.0f}% of the time.")
        if request.smile_ratio is not None:
            comm_additions.append(f"Smiled during {request.smile_ratio * 100:.0f}% of the answer.")
        if request.head_steadiness is not None and request.head_steadiness < 0.5:
            comm_additions.append("Frequent head movement; a steadier posture reads as more composed on video.")
        if comm_additions:
            eval_data["communication_feedback"] += " Delivery: " + " ".join(comm_additions)

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
            overall_score=overall_score,
            spoken_feedback=_speakable(eval_data.get("spoken_feedback") or "")
            or _speakable(_first_sentences(eval_data["technical_feedback"])),
            scoring_method=scoring_method,
            llm_technical_accuracy=llm_technical,
        )

    async def _run_evaluation_chain(self, question: str, topic: str, transcript: str,
                                    reference_answer: Optional[str] = None,
                                    rubric_criteria: Optional[List[str]] = None,
                                    role: Optional[str] = None) -> Dict[str, Any]:
        """Runs rubric-based evaluation via LLM or deterministic fallback. With a reference answer
        and rubric (from the question bank) the model grades against them instead of its own idea
        of a good answer; evaluation/eval_mohler.py measures the difference against human graders."""
        from app.core.roles import is_technical
        if is_technical(role):
            criteria = ("You are an expert technical interviewer evaluating a student candidate's spoken answer.\n"
                        "Evaluate the answer across 4 criteria on a 1.0 to 5.0 scale:\n"
                        "1. technical_accuracy (1.0 - 5.0)\n"
                        "2. relevance (1.0 - 5.0)\n"
                        "3. explanation_quality (1.0 - 5.0)\n"
                        "4. clarity (1.0 - 5.0)\n\n")
        else:
            # Same JSON keys, competency-based meaning for HR, marketing, finance, design and writing roles
            criteria = (f"You are an experienced hiring manager for a {role} position evaluating a candidate's spoken "
                        "interview answer.\nEvaluate the answer across 4 criteria on a 1.0 to 5.0 scale:\n"
                        "1. technical_accuracy: accuracy and depth of role knowledge and professional judgement\n"
                        "2. relevance: how directly the answer addresses the question\n"
                        "3. explanation_quality: structure and evidence; for behavioural questions situation, task, "
                        "action and result, with concrete examples and measurable impact\n"
                        "4. clarity: clear, concise, professional communication\n\n")
        system_prompt = (
            criteria +
            "Return ONLY a JSON object with keys:\n"
            "- 'technical_accuracy': float\n"
            "- 'relevance': float\n"
            "- 'explanation_quality': float\n"
            "- 'clarity': float\n"
            "- 'technical_feedback': string\n"
            "- 'communication_feedback': string\n"
            "- 'missing_concepts': list of strings\n"
            "- 'strengths': list of strings\n"
            "- 'areas_for_improvement': list of strings\n"
            "- 'spoken_feedback': string. What you, the interviewer, say out loud right after the answer: "
            "1-2 natural sentences (max 40 words) naming one thing they did well and the most important gap. "
            "No scores, no markdown, no lists. Do not ask a new question."
        )
        user_prompt = f"Interview Question: {question}\nTopic: {topic}\n"
        if reference_answer:
            user_prompt += (
                f"Reference Answer (what a correct answer covers; the question may be phrased differently, "
                f"and correct points beyond it still count):\n{reference_answer}\n"
            )
        if rubric_criteria:
            user_prompt += "Rubric Criteria:\n" + "\n".join(f"- {c}" for c in rubric_criteria) + "\n"
        user_prompt += f"Student Transcript:\n\"{transcript}\""

        if settings.LLM_PROVIDER == "local":
            try:
                from app.services.local_llm import local_llm
                data = await local_llm.chat_json(system_prompt, user_prompt, temperature=settings.LLM_TEMPERATURE)
                return _validated(data)
            except Exception as e:
                print(f"[Warning] Local LLM evaluation failed: {e}.")
        elif self._llm == "gemini" and self._gemini_client:
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
                print(f"[Warning] Gemini Evaluation failed: {e}.")

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
                print(f"[Warning] LLM Evaluation failed: {e}.")

        # Canned scores are only for the explicit "mock" provider (tests). For a real provider,
        # inventing a 4.5/5 would mislead the candidate about their readiness.
        if settings.LLM_PROVIDER != "mock":
            raise EvaluationError(
                "The interviewer couldn't evaluate this answer right now (the AI service didn't respond). "
                "Please try again.", status_code=503,
            )

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
