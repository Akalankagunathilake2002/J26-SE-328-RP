"""Get everything the service needs before it starts (used by the Dockerfile).

    python -m scripts.prepare_models

1. Loads the pretrained models once (sentence-transformer, cross-encoder, GLiNER), downloading
   any that are not in the Hugging Face cache yet.
2. Builds the semantic skill index (data/index) if it is missing.
3. Trains the SetFit evidence classifier (models/evidence-setfit) if it is missing.

Steps 2 and 3 are skipped when their output already exists, so a build that ships a ready index
and model is fast, and a build from a clean clone still produces both.
"""
import subprocess
import sys

from app.config.settings import get_settings


def main() -> None:
    settings = get_settings()

    from gliner import GLiNER
    from sentence_transformers import CrossEncoder, SentenceTransformer

    print(f"Loading {settings.embedding_model}", flush=True)
    SentenceTransformer(settings.embedding_model, device="cpu")
    print(f"Loading {settings.reranker_model}", flush=True)
    CrossEncoder(settings.reranker_model, device="cpu")
    print(f"Loading {settings.gliner_model}", flush=True)
    GLiNER.from_pretrained(settings.gliner_model)

    if not (settings.index_dir / "ssks.faiss").exists():
        subprocess.run([sys.executable, "-m", "scripts.build_skill_index"], check=True)
    else:
        print(f"Skill index found in {settings.index_dir}", flush=True)

    if not settings.evidence_model_dir.exists():
        subprocess.run([sys.executable, "-m", "scripts.train_evidence_model"], check=True)
    else:
        print(f"Evidence model found in {settings.evidence_model_dir}", flush=True)


if __name__ == "__main__":
    main()
