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
    LLM_PROVIDER: Literal["openai", "gemini", "mock"] = "openai"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2

    # Embeddings
    EMBEDDING_PROVIDER: Literal["openai", "gemini", "local", "mock"] = "gemini"
    EMBEDDING_MODEL_NAME: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 1536

    # Speech-to-Text
    STT_PROVIDER: Literal["whisper_api", "mock"] = "whisper_api"
    WHISPER_MODEL: str = "whisper-1"

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
