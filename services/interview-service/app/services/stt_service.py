import time
import os
import re
from typing import Dict, Any, List
from app.core.config import settings

TECHNICAL_DOMAIN_VOCABULARY = (
    "HikariCP, PostgreSQL, ACID, MVCC, xmin, xmax, B-Tree, GIN, BRIN, Kafka, "
    "RabbitMQ, Docker, Kubernetes, Next.js, SSR, SSG, ISR, Redis, Zustand, TanStack Query, "
    "gRPC, Protobuf, OpenTelemetry, Circuit Breaker, Resilience4j, JWT, OWASP, "
    "OAuth2, REST, HPA, microservices, decoupling, idempotency"
)


class SpeechToTextError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class SpeechToTextService:
    def __init__(self):
        self._client = None
        self._init_client()

    def _init_client(self):
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"[Warning] Failed to init OpenAI Whisper client: {e}")
                self._client = None
        else:
            self._client = None

    async def transcribe_audio_file(self, file_path: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Transcribes audio via Whisper API with domain vocabulary prompting
        to guarantee high accuracy on software engineering terminology, acronyms, and frameworks.
        """
        t_start = time.perf_counter()
        prompt_vocab = custom_prompt or TECHNICAL_DOMAIN_VOCABULARY

        # Never substitute a canned answer: the transcript is scored as the candidate's own words.
        if not self._client:
            raise SpeechToTextError(
                "Speech-to-text is not configured (OPENAI_API_KEY missing). Type your answer instead.",
                status_code=503,
            )
        if not os.path.exists(file_path):
            raise SpeechToTextError("The recorded audio was not received.", status_code=400)
        try:
            with open(file_path, "rb") as audio_file:
                transcript_resp = self._client.audio.transcriptions.create(
                    model=settings.WHISPER_MODEL,
                    file=audio_file,
                    prompt=prompt_vocab,
                    temperature=0.0
                )
                transcript_text = (transcript_resp.text or "").strip()
        except Exception as e:
            print(f"[Error] Whisper API error: {e}")
            raise SpeechToTextError("Transcription failed. Please try again or type your answer.") from e
        if not transcript_text:
            raise SpeechToTextError("No speech was detected in the recording. Please try again.", status_code=422)

        latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # Detect technical domain vocabulary tokens in transcript
        detected_terms: List[str] = []
        for term in TECHNICAL_DOMAIN_VOCABULARY.split(", "):
            clean_term = term.strip()
            if re.search(r'\b' + re.escape(clean_term) + r'\b', transcript_text, re.IGNORECASE):
                detected_terms.append(clean_term)

        return {
            "transcript": transcript_text,
            "latency_ms": latency_ms,
            "domain_terms_detected": detected_terms
        }


stt_service = SpeechToTextService()
