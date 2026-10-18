"""Step 3, model A: train the spaCy skill NER on SkillSpan (CPU).

    .venv/bin/python src/train_spacy.py [--version 0.1.0]

Saves models/spacy-skill-ner-<version>/ with model-best (best SkillSpan validation F1),
model-last, train.log and metadata.json (version, settings, data fingerprints, scores).
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime

import spacy

from common import DATA, MODELS, ROOT, SEED, file_sha256, write_json

CONFIG = ROOT / "configs" / "spacy_ner.cfg"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()

    out = MODELS / f"spacy-skill-ner-{args.version}"
    out.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    with (out / "train.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "train", str(CONFIG), "--output", str(out)],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
        )
    if result.returncode != 0:
        print(f"training failed, see {out / 'train.log'}")
        return result.returncode

    best = json.loads((out / "model-best" / "meta.json").read_text())
    write_json(out / "metadata.json", {
        "model": "spacy-skill-ner",
        "version": args.version,
        "trained_at": started.isoformat(timespec="seconds"),
        "training_minutes": round((datetime.now(UTC) - started).total_seconds() / 60, 1),
        "seed": SEED,
        "base_pipeline": "en_core_web_md 3.8.0 (tok2vec and vectors reused, NER trained from scratch)",
        "labels": best["labels"]["ner"],
        "config": str(CONFIG.relative_to(ROOT)),
        "config_sha256": file_sha256(CONFIG),
        "training_data": json.loads((DATA / "skillspan" / "stats.json").read_text()),
        "train_file_sha256": file_sha256(DATA / "skillspan" / "train.spacy"),
        "best_validation_scores": best["performance"],
        "versions": {"spacy": spacy.__version__, "python": platform.python_version()},
    })
    scores = {k: round(v, 3) for k, v in best["performance"].items() if isinstance(v, float)}
    print(f"saved {out}; validation:", scores)
    return 0


if __name__ == "__main__":
    sys.exit(main())
