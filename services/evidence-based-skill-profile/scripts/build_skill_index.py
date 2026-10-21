"""Build the semantic skill indexes (FAISS) used to match skills by meaning (TAF tasks 4, 5).

    python -m scripts.build_skill_index            ssks index (C02 dictionary, ~1,850 skills)
    python -m scripts.build_skill_index --esco     also the esco fallback index (~13,000 skills)

Each skill's name, aliases and "name: description" are embedded with the model in
settings.embedding_model and written to settings.index_dir as <name>.faiss + <name>.json.
Rebuild after the dictionary or the embedding model changes.
"""
import argparse
import time

from app.config.settings import get_settings
from app.extraction.matcher import load_entries
from app.semantic.encoder import get_encoder
from app.semantic.skill_index import SkillIndex, load_esco_entries, load_ssks_esco_uris

SSKS, ESCO = "ssks", "esco"


def _build(name: str, entries: list, directory) -> None:
    started = time.perf_counter()
    index = SkillIndex.build(entries, get_encoder())
    index.save(directory, name)
    print(f"{name}: {len(entries)} skills, {len(index.rows)} vectors "
          f"({time.perf_counter() - started:.0f}s) -> {directory / name}.faiss")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--esco", action="store_true", help="also build the ESCO fallback index")
    args = parser.parse_args()

    settings = get_settings()
    print(f"Embedding model: {settings.embedding_model}")
    _build(SSKS, load_entries(settings.dictionary_path), settings.index_dir)
    if args.esco:
        in_ssks = load_ssks_esco_uris(settings.ssks_external_ids_path)
        _build(ESCO, load_esco_entries(settings.esco_skills_path, in_ssks), settings.index_dir)


if __name__ == "__main__":
    main()
