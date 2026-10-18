from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "evidence-based-skill-profile"
    version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/profile_db"
    dictionary_path: Path = SERVICE_DIR / "data" / "dictionary" / "clean_skills.csv"


@lru_cache
def get_settings() -> Settings:
    return Settings()
