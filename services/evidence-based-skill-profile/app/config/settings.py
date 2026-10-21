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
    matcher_rules_path: Path = SERVICE_DIR / "data" / "dictionary" / "matcher_rules.csv"
    esco_skills_path: Path = SERVICE_DIR / "data" / "esco" / "skills_en.csv"
    ssks_external_ids_path: Path = (
        SERVICE_DIR.parent / "shared-skill-knowledge" / "seed" / "import_ready" / "external_ids.csv"
    )
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    index_dir: Path = SERVICE_DIR / "data" / "index"
    # Cross-encoder that re-ranks the top semantic candidates. On the 53-term dev set it added one
    # correct paraphrase (83.0% -> 84.9%, scripts/evaluate_normalisation.py): small, not yet proven.
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    use_reranker: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
