"""Step 2: pick the topjobs test ads and export them for labelling in Label Studio.

    .venv/bin/python src/export_label_studio.py [--n 100]

Picks --n ads at random (seed 42) from the collected topjobs ads with readable text. The text is
exactly what the extractors read: the ad's OCR text with "About us", benefits, salary and
how-to-apply sections, URLs and the company name left out (skill_text in the service).

Left out of the draw: the 5 ads the lexicon was tuned on, so the comparison isn't biased towards it.
These ads are the TEST set only: never used for training or weak labels.

Writes data/topjobs_test/tasks.json (import into Label Studio, with configs/label_studio.xml as the
labelling interface) and data/topjobs_test/selection.json (which ads, and a fingerprint of each
text so the evaluation can check the labels belong to the same text).
"""

from __future__ import annotations

import argparse
import hashlib
import random
import sys
from pathlib import Path

from app.collectors.config import load_settings
from app.collectors.storage import Storage
from app.processing.skills import MIN_WORDS, WORD, skill_text

from common import DATA, SEED, write_json

OUT = DATA / "topjobs_test"
# The lexicon (config/skills_lexicon.yaml) was tuned on these ads in October 2026.
TUNING_ADS = {
    "topjobs:0001557624", "topjobs:0001558206", "topjobs:0001558758", "topjobs:0001560024", "topjobs:0001560048",
}


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--data-dir", type=Path, help="the service's data folder (default: its settings)")
    args = parser.parse_args()

    if (OUT / "tasks.json").exists():
        print(f"error: {OUT / 'tasks.json'} exists; the test set is drawn once. Delete it to draw again.",
              file=sys.stderr)
        return 2
    storage = Storage(args.data_dir or load_settings().data_dir)
    texts = {ad.key: (ad, skill_text(ad)) for ad in storage.read_jsonl("topjobs")}
    eligible = sorted(key for key, (_, text) in texts.items()
                      if key not in TUNING_ADS and len(WORD.findall(text)) >= MIN_WORDS)
    if len(eligible) < args.n:
        print(f"error: only {len(eligible)} ads with readable text (not counting the {len(TUNING_ADS)} tuning ads); "
              f"{args.n} are needed. Collect more ads first (scripts/sync.sh).", file=sys.stderr)
        return 1

    chosen = random.Random(SEED).sample(eligible, args.n)
    tasks = [
        {"id": i, "data": {"text": texts[key][1], "ad": key, "sectors": ", ".join(texts[key][0].sectors),
                           "job_title": texts[key][0].job_title or ""}}
        for i, key in enumerate(chosen, start=1)
    ]
    write_json(OUT / "tasks.json", tasks)
    write_json(OUT / "selection.json", {
        "seed": SEED,
        "n": args.n,
        "eligible_ads": len(eligible),
        "excluded_tuning_ads": sorted(TUNING_ADS),
        "ads": [{"task": i, "ad": key, "text_sha256": text_fingerprint(texts[key][1])}
                for i, key in enumerate(chosen, start=1)],
    })
    print(f"{args.n} of {len(eligible)} eligible ads written to {OUT / 'tasks.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
