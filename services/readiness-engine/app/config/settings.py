from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = "readiness-engine"
    version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/readiness_engine_db"

    # Candidate discovery settings
    ssks_base_url: str = "http://localhost:8005"
    candidate_similarity_threshold: float = 0.60
    candidate_max_submissions_per_run: int = 10
    candidate_discovery_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    candidate_discovery_timeout_seconds: float = 10.0
    candidate_discovery_max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
