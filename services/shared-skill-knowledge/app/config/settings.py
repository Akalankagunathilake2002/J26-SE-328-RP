from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "shared-skill-knowledge"
    version: str = "0.1.0"
    database_url: str = "postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/ssks_db"
    db_schema: str | None = None
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    auth_url: str | None = None
    internal_service_key: str = Field(
        default="",
        validation_alias=AliasChoices("INTERNAL_SERVICE_KEY", "SSKS_INTERNAL_SERVICE_KEY"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
