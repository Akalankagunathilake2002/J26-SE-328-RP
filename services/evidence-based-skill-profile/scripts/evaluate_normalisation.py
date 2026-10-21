"""Ablation study of the normalisation cascade (TAF tasks 5 and 10).

Runs each configuration on a labelled file (term, expected_skill_id, category) and prints accuracy
per category, so the gain of each layer is visible. expected_skill_id may list several acceptable
IDs separated by "|" (e.g. "version control" is Git or Version control software); an empty one
means the term is not a skill and must stay unmatched.

    exact      dictionary names and aliases only
    +clean     + version/suffix cleaning
    +fuzzy     + spelling-mistake matching
    +semantic  + BERT sentence-embedding search
    +rerank    + cross-encoder re-ranking (off in the service unless settings.use_reranker)

    python -m scripts.evaluate_normalisation
    python -m scripts.evaluate_normalisation --file data/evaluation/normalisation_dev.csv --errors
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

from app.config.settings import SERVICE_DIR, get_settings
from app.extraction.matcher import load_entries
from app.normalisation.normaliser import CrossEncoderReranker, Normaliser
from app.semantic.encoder import get_encoder
from app.semantic.skill_index import SkillIndex

DEFAULT_FILE = SERVICE_DIR / "data" / "evaluation" / "normalisation_dev.csv"


def _correct(result_id: str | None, expected: str) -> bool:
    return (result_id or "") in (expected.split("|") if expected else [""])


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--errors", action="store_true",
                        help="list the mistakes of the configuration the service uses")
    args = parser.parse_args()

    settings = get_settings()
    rows = _read(args.file)
    entries = load_entries(settings.dictionary_path)
    encoder = get_encoder()
    index = SkillIndex.load(settings.index_dir, "ssks", settings.embedding_model)
    reranker = CrossEncoderReranker(settings.reranker_model)
    configs = {
        "exact": Normaliser(entries, use_cleaning=False, use_fuzzy=False),
        "+clean": Normaliser(entries, use_fuzzy=False),
        "+fuzzy": Normaliser(entries),
        "+semantic": Normaliser(entries, encoder, index),
        "+rerank": Normaliser(entries, encoder, index, reranker),
    }
    service_config = "+rerank" if settings.use_reranker else "+semantic"
    categories = list(dict.fromkeys(row["category"] for row in rows))
    totals = {c: sum(1 for row in rows if row["category"] == c) for c in categories}
    terms = [row["term"] for row in rows]

    print(f"{len(rows)} terms from {args.file.name}; accuracy per category (correct / total)\n")
    print(f"{'config':<10}" + "".join(f"{c:>12}" for c in categories) + f"{'overall':>10}")
    service_results = []
    for label, normaliser in configs.items():
        results = normaliser.normalise(terms)
        correct: dict[str, int] = defaultdict(int)
        for row, result in zip(rows, results):
            correct[row["category"]] += _correct(result.skill_id, row["expected_skill_id"])
        cells = "".join(f"{correct[c]:>8}/{totals[c]:<3}" for c in categories)
        print(f"{label:<10}{cells}{sum(correct.values()) / len(rows):>10.1%}")
        if label == service_config:
            service_results = results

    if args.errors:
        print(f"\nMistakes of the service configuration ({service_config}):")
        for row, result in zip(rows, service_results):
            if not _correct(result.skill_id, row["expected_skill_id"]):
                print(f"  {row['term']!r}: expected {row['expected_skill_id'] or 'unmatched'}, "
                      f"got {result.skill_id or 'unmatched'} {result.name or ''} "
                      f"({result.method}, {result.score:.2f})")


if __name__ == "__main__":
    main()
