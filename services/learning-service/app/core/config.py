from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Service Information
    SERVICE_NAME: str = "learning-service"
    LEARNING_SERVICE_PORT: int | None = None
    SERVICE_PORT: int | None = None
    ENVIRONMENT: str = "development"

    @property
    def port(self) -> int:
        port_val = self.LEARNING_SERVICE_PORT or self.SERVICE_PORT
        if port_val is None:
            raise ValueError("LEARNING_SERVICE_PORT must be configured in .env")
        return port_val


    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "learning_db"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

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

    # RAG Parameters
    TOP_K: int = 4
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_STRATEGY: Literal["hybrid_rrf", "dense_only", "sparse_only"] = "hybrid_rrf"
    RRF_K: int = 60
    DENSE_WEIGHT: float = 0.5
    SPARSE_WEIGHT: float = 0.5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
