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
    # Cross-encoder that re-ranks the top semantic candidates. On the 53-term dev set it added one
    # correct paraphrase (83.0% -> 84.9%, scripts/evaluate_normalisation.py): small, not yet proven.
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    use_reranker: bool = True
    # Second extraction layer (TAF task 4): GLiNER zero-shot skill extraction.
    use_neural_extraction: bool = True
    gliner_model: str = "urchade/gliner_small-v2.1"
    # Asked for; only keep_labels are used, the others draw job titles, degrees and employers away.
    gliner_labels: list[str] = ["skill", "tool", "technology", "job title", "degree",
                                "organization"]
    gliner_keep_labels: list[str] = ["skill", "tool", "technology"]
    gliner_threshold: float = 0.5
    # A GLiNER phrase linked only by meaning needs this cosine; weaker links go to `unlinked`.
    neural_semantic_min: float = 0.65
    # Evidence type for CV sentences (TAF task 6): "setfit" (v2, trained by
    # scripts/train_evidence_model.py into evidence_model_dir) or "rules" (v1 baseline). Without a
    # trained model, setfit falls back to the rules with a warning.
    evidence_classifier: str = "setfit"
    evidence_model_dir: Path = SERVICE_DIR / "models" / "evidence-setfit"
    # GitHub portfolio links (TAF task 2). A token raises the API limit from 60 to 5,000 an hour.
    github_token: str = ""
    github_max_repos: int = 8
    github_min_language_share: float = 0.05
    index_dir: Path = SERVICE_DIR / "data" / "index"


@lru_cache
def get_settings() -> Settings:
    return Settings()
