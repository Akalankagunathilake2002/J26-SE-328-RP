import asyncio
import os
import re
import subprocess
import tempfile
import time
from typing import Dict, Any, List
from app.core.config import settings

TECHNICAL_DOMAIN_VOCABULARY = (
    "HikariCP, PostgreSQL, ACID, MVCC, xmin, xmax, B-Tree, GIN, BRIN, Kafka, "
    "RabbitMQ, Docker, Kubernetes, Next.js, SSR, SSG, ISR, Redis, Zustand, TanStack Query, "
    "gRPC, Protobuf, OpenTelemetry, Circuit Breaker, Resilience4j, JWT, OWASP, "
    "OAuth2, REST, HPA, microservices, decoupling, idempotency"
)

GEMINI_TRANSCRIBE_PROMPT = (
    "Transcribe this recording of a job candidate answering a technical interview question. "
    "Return ONLY the candidate's words, verbatim, as plain text: no timestamps, speaker labels, "
    "quotes or commentary. Keep filler words such as 'um' and 'uh'. If there is no intelligible "
    "speech, return exactly: [NO_SPEECH]\n"
    "Technical terms that may appear: {vocab}"
)


def _usable(key: str) -> bool:
    return bool(key) and not key.startswith("your_")


class SpeechToTextError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class SpeechToTextService:
    """Transcribes the candidate's spoken answer with OpenAI Whisper, local faster-whisper or Gemini.

    STT_PROVIDER="auto" picks the OpenAI Whisper API if OPENAI_API_KEY is set, then local
    faster-whisper if installed (no key), then Gemini.
    """

    def __init__(self):
        self._client = None          # OpenAI client (Whisper)
        self._gemini = None          # google-genai client
        self._local = None           # faster-whisper model, loaded on first use
        self._init_client()

    def _init_client(self):
        if _usable(settings.OPENAI_API_KEY):
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"[Warning] Failed to init OpenAI Whisper client: {e}")
        if _usable(settings.GEMINI_API_KEY):
            try:
                from google import genai
                self._gemini = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                print(f"[Warning] Failed to init Gemini speech-to-text client: {e}")

    @staticmethod
    def _local_available() -> bool:
        try:
            import faster_whisper  # noqa: F401
            return True
        except ImportError:
            return False

    @property
    def provider(self) -> str | None:
        choice = settings.STT_PROVIDER
        if choice == "whisper_api":
            return "whisper_api" if self._client else None
        if choice == "gemini":
            return "gemini" if self._gemini else None
        if choice == "local":
            return "local" if self._local_available() else None
        if choice == "auto":
            if self._client:
                return "whisper_api"
            if self._local_available():
                return "local"
            return "gemini" if self._gemini else None
        return None

    async def transcribe_audio_file(self, file_path: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Transcribes the recorded answer with domain vocabulary hints so software engineering
        terms, acronyms and frameworks are spelled correctly.
        """
        t_start = time.perf_counter()
        prompt_vocab = custom_prompt or TECHNICAL_DOMAIN_VOCABULARY

        # Never substitute a canned answer: the transcript is scored as the candidate's own words.
        provider = self.provider
        if provider is None:
            raise SpeechToTextError(
                "Speech-to-text is not configured (install faster-whisper for local, or set OPENAI_API_KEY "
                "or GEMINI_API_KEY). Type your answer instead.",
                status_code=503,
            )
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise SpeechToTextError("The recorded audio was not received.", status_code=400)

        try:
            if provider == "whisper_api":
                transcript_text = await asyncio.to_thread(self._whisper, file_path, prompt_vocab)
            elif provider == "local":
                transcript_text = await asyncio.to_thread(self._local_transcribe, file_path, prompt_vocab)
            else:
                transcript_text = await asyncio.to_thread(self._gemini_transcribe, file_path, prompt_vocab)
        except SpeechToTextError:
            raise
        except Exception as e:
            print(f"[Error] {provider} transcription error: {e}")
            raise SpeechToTextError("Transcription failed. Please try again or type your answer.") from e

        if not transcript_text or transcript_text.strip() == "[NO_SPEECH]":
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
            "domain_terms_detected": detected_terms,
            "provider": provider,
        }

    def _whisper(self, file_path: str, prompt_vocab: str) -> str:
        with open(file_path, "rb") as audio_file:
            resp = self._client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL,
                file=audio_file,
                prompt=prompt_vocab,
                temperature=0.0
            )
        return (resp.text or "").strip()

    def _local_transcribe(self, file_path: str, prompt_vocab: str) -> str:
        """faster-whisper on CPU (int8). Reads WebM/MP4 directly via its bundled decoder."""
        if self._local is None:
            from faster_whisper import WhisperModel
            self._local = WhisperModel(settings.LOCAL_WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, _info = self._local.transcribe(
            file_path,
            language="en",
            initial_prompt=f"Technical interview answer. Terms: {prompt_vocab}",
            vad_filter=True,             # skip silence before/after the answer
            beam_size=5,
        )
        return " ".join(s.text.strip() for s in segments).strip()

    def _gemini_transcribe(self, file_path: str, prompt_vocab: str) -> str:
        from google.genai import types

        # Browsers record WebM/Opus (Chrome, Firefox) or MP4/AAC (Safari); Gemini's documented
        # audio formats don't include WebM, so normalise to 16 kHz mono FLAC first.
        with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as tmp:
            flac_path = tmp.name
        try:
            proc = subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i", file_path, "-ac", "1", "-ar", "16000", flac_path],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode != 0 or os.path.getsize(flac_path) == 0:
                raise SpeechToTextError("The recording couldn't be read. Please record again.", status_code=422)
            with open(flac_path, "rb") as f:
                audio = f.read()
        finally:
            if os.path.exists(flac_path):
                os.remove(flac_path)

        resp = self._gemini.models.generate_content(
            model=settings.STT_GEMINI_MODEL,
            contents=[
                GEMINI_TRANSCRIBE_PROMPT.format(vocab=prompt_vocab),
                types.Part.from_bytes(data=audio, mime_type="audio/flac"),
            ],
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return (resp.text or "").strip()


stt_service = SpeechToTextService()
