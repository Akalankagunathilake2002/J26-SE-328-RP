from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "interview-service"
    INTERVIEW_SERVICE_PORT: int | None = None
    SERVICE_PORT: int | None = None
    ENVIRONMENT: str = "development"

    @property
    def port(self) -> int:
        port_val = self.INTERVIEW_SERVICE_PORT or self.SERVICE_PORT
        if port_val is None:
            raise ValueError("INTERVIEW_SERVICE_PORT must be configured in .env")
        return port_val


    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "interview_db"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # AI Configuration
    # "local" = OpenAI-compatible server on the host Mac (mlx_lm.server, Huggingbay/start-llm.sh)
    LLM_PROVIDER: Literal["openai", "gemini", "local", "mock"] = "openai"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    LOCAL_LLM_URL: str = "http://host.docker.internal:8082"
    LOCAL_LLM_TIMEOUT: float = 170.0          # under the gateway's 180 s proxy timeout
    LOCAL_LLM_THINKING: bool = False          # thinking mode: much slower, rarely better here

    # Embeddings ("local" = fastembed ONNX model inside this container, no API key)
    EMBEDDING_PROVIDER: Literal["openai", "gemini", "local", "mock"] = "gemini"
    EMBEDDING_MODEL_NAME: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 1536
    # bge-small-en-v1.5 fine-tuned on the learning corpus (scripts/training/train_retrieval.py), 384 dimensions.
    # "BAAI/bge-small-en-v1.5" loads the original through fastembed; changing it needs a re-ingestion.
    LOCAL_EMBEDDING_MODEL: str = "models/embedder"

    # Speech-to-Text
    # "auto": OpenAI Whisper if OPENAI_API_KEY is set, otherwise Gemini.
    # "local": faster-whisper inside this container, no API key.
    STT_PROVIDER: Literal["auto", "whisper_api", "gemini", "local", "mock"] = "auto"
    # Technical-accuracy score: "auto" uses the mode chosen on validation data (models/answer_scorer/
    # scoring_config.json); "llm", "calibrated", "trained" or "blend" force one (app/services/answer_scorer.py)
    SCORING_MODE: Literal["auto", "llm", "calibrated", "trained", "blend"] = "auto"
    WHISPER_MODEL: str = "whisper-1"
    STT_GEMINI_MODEL: str = "gemini-2.5-flash"
    LOCAL_WHISPER_MODEL: str = "small.en"

    # RAG Parameters
    TOP_K: int = 3

    # Realistic Human Interviewer (HeyGen LiveAvatar streaming avatar)
    LIVEAVATAR_API_KEY: str = ""
    LIVEAVATAR_API_URL: str = "https://api.liveavatar.com"
    # Sandbox mode costs no credits but only allows the "Wayne" avatar and ends sessions after ~1 minute
    LIVEAVATAR_SANDBOX: bool = True
    LIVEAVATAR_AVATAR_ID: str = "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a"
    LIVEAVATAR_VOICE_ID: str = ""
    LIVEAVATAR_MAX_SESSION_SECONDS: int = 1200

    # Which interviewer the frontend uses: HeyGen LiveAvatar, the local avatar engine
    # (LivePortrait + MuseTalk on the host Mac, see Huggingbay/start-avatar.sh), or none
    # (portrait + browser voice).
    AVATAR_PROVIDER: Literal["liveavatar", "local", "none"] = "liveavatar"
    # The local engine needs the Mac's GPU, so it runs on the host, not in Docker.
    LOCAL_AVATAR_URL: str = "http://host.docker.internal:8768"
    LOCAL_AVATAR_NAME: str = "elena"
    LOCAL_AVATAR_VOICE: str = "Samantha"
    LOCAL_AVATAR_DECODER: Literal["fast", "quality"] = "fast"

    # Interview structure: welcome and introductions, role questions while time allows, then a closing
    INTERVIEWER_NAME: str = "Elena"
    INTERVIEW_DEFAULT_MINUTES: int = 25
    INTERVIEW_MIN_QUESTIONS: int = 2          # role questions asked even when the time budget is tight
    INTERVIEW_MAX_QUESTIONS: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
