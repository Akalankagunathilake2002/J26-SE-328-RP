from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "shared-skill-knowledge"
    version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/ssks_db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
