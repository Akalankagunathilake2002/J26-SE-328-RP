"""Splits Mohler ASAG by question for training the answer scorer and calibrating the LLM evaluator.

    <train-venv>/bin/python scripts/training/prepare_mohler_splits.py [MOHLER_JSONL] [OUT_DIR]

Splitting by question (not by answer) keeps every test question unseen in training, so test scores
measure how the scorer handles new questions, as in a real interview. Outputs in OUT_DIR:
  train.jsonl / valid.jsonl / test.jsonl   all answers of each question group (55 / 12 / 12 questions)
  valid_llm.jsonl                          score-balanced subset of valid, for fitting the LLM calibration
  test_llm.jsonl                           score-balanced subset of test, where every method is compared
  split.json                               which question went where (seed 7)
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Dilmith Ext/datasets/raw/mohler-asag/open_ended.jsonl")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/Volumes/Dilmith Ext/datasets/training/mohler")
SEED = 7
N_TRAIN, N_VALID = 55, 12                 # questions; the remaining 12 are the test set
BINS = [(0.0, 2.5), (2.5, 3.5), (3.5, 4.5), (4.5, 5.01)]
LLM_PER_BIN = {"valid": 30, "test": 40}   # Gemma takes ~17 s per answer, so it grades a balanced subset


def balanced(rows, per_bin, rng):
    picked = []
    for lo, hi in BINS:
        band = [r for r in rows if lo <= r["score_avg"] < hi]
        picked += rng.sample(band, min(per_bin, len(band)))
    rng.shuffle(picked)
    return picked


def main():
    rows = [json.loads(line) for line in open(SRC) if line.strip()]
    questions = sorted({r["question"] for r in rows})
    rng = random.Random(SEED)
    rng.shuffle(questions)
    part_of = {q: "train" if i < N_TRAIN else "valid" if i < N_TRAIN + N_VALID else "test"
               for i, q in enumerate(questions)}
    parts = defaultdict(list)
    for r in rows:
        parts[part_of[r["question"]]].append(r)

    OUT.mkdir(parents=True, exist_ok=True)
    def write(name, items):
        with open(OUT / f"{name}.jsonl", "w") as f:
            for r in items:
                f.write(json.dumps(r) + "\n")
        bands = Counter(next(i for i, (lo, hi) in enumerate(BINS) if lo <= r["score_avg"] < hi) for r in items)
        print(f"{name:10s} {len(items):5d} answers  per score band {dict(sorted(bands.items()))}")
    for name in ("train", "valid", "test"):
        write(name, parts[name])
    for name in ("valid", "test"):
        write(f"{name}_llm", balanced(parts[name], LLM_PER_BIN[name], random.Random(SEED)))
    json.dump({"seed": SEED, "questions": {p: sorted(q for q, v in part_of.items() if v == p)
                                           for p in ("train", "valid", "test")}},
              open(OUT / "split.json", "w"), indent=1)


if __name__ == "__main__":
    main()
