"""How closely does the interview evaluator agree with human graders? Runs it on Mohler ASAG.

Mohler ASAG (CC BY 4.0, nkazi/MohlerASAG on Hugging Face): 2,273 answers by computer-science
students to 79 data-structures questions, each scored 0-5 by two human graders, with the
instructor's answer. The evaluator's technical_accuracy (1-5) is compared with the graders' average.

Two modes, on the same answers:
  no_reference  question + answer only (how live interviews were graded before reference answers)
  reference     also gives the instructor answer as the reference answer
The two human graders' agreement on the same sample is reported as the ceiling to compare against.

Run inside the interview-service container (it needs the configured LLM); see
scripts/datasets/run_mohler_eval.sh:
    python -m evaluation.eval_mohler --data /tmp/mohler/open_ended.jsonl --out /tmp/mohler/results.json
"""
import argparse
import asyncio
import json
import random
import re
import time
from collections import defaultdict

import numpy as np

from app.core.config import settings
from app.services.evaluation_rag import evaluation_rag_service

TOPIC = "Data Structures"
BINS = [(0.0, 2.5), (2.5, 3.5), (3.5, 4.5), (4.5, 5.01)]   # human score_avg bands for stratified sampling


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("<STOP>", " ")).strip()


def load(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def sample(rows: list[dict], limit: int, how: str, seed: int) -> list[dict]:
    rng = random.Random(seed)
    if how == "all":                      # the file is already the sample (scripts/training splits)
        return rows[:limit]
    if how == "random":
        return rng.sample(rows, min(limit, len(rows)))
    # Equal numbers per score band, spread over as many questions as possible: half the dataset
    # scores 5/5, so a random sample would barely test whether weak answers get low scores
    picked = []
    per_bin = limit // len(BINS)
    for lo, hi in BINS:
        band = [r for r in rows if lo <= r["score_avg"] < hi]
        by_question = defaultdict(list)
        for r in band:
            by_question[r["question"]].append(r)
        for answers in by_question.values():
            rng.shuffle(answers)
        questions = list(by_question)
        rng.shuffle(questions)
        taken = []
        while len(taken) < per_bin and any(by_question.values()):
            for q in questions:
                if by_question[q] and len(taken) < per_bin:
                    taken.append(by_question[q].pop())
        picked += taken
    rng.shuffle(picked)
    return picked


def pearson(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 and np.std(a) and np.std(b) else float("nan")


def spearman(a, b):
    def ranks(x):
        order = np.argsort(x, kind="mergesort")
        r = np.empty(len(x))
        r[order] = np.arange(len(x))
        # average ranks for ties
        vals = np.asarray(x)
        for v in np.unique(vals):
            idx = vals == v
            r[idx] = r[idx].mean()
        return r
    return pearson(ranks(a), ranks(b))


def qwk(a, b, k=6):
    """Quadratic weighted kappa on integer scores 0..k-1."""
    a = np.clip(np.rint(a), 0, k - 1).astype(int)
    b = np.clip(np.rint(b), 0, k - 1).astype(int)
    observed = np.zeros((k, k))
    for x, y in zip(a, b):
        observed[x, y] += 1
    weights = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    expected = np.outer(observed.sum(1), observed.sum(0)) / max(observed.sum(), 1)
    denom = (weights * expected).sum()
    return float(1 - (weights * observed).sum() / denom) if denom else float("nan")


def agreement(human, model) -> dict:
    human, model = np.asarray(human, float), np.asarray(model, float)
    return {
        "n": int(len(human)),
        "pearson": round(pearson(human, model), 3),
        "spearman": round(spearman(human, model), 3),
        "qwk": round(qwk(human, model), 3),
        "mae": round(float(np.mean(np.abs(human - model))), 3),
        "mean_human": round(float(human.mean()), 2),
        "mean_model": round(float(model.mean()), 2),
    }


async def grade(row: dict, with_reference: bool) -> dict:
    t0 = time.perf_counter()
    data = await evaluation_rag_service._run_evaluation_chain(
        question=clean(row["question"]),
        topic=TOPIC,
        transcript=clean(row["student_answer"]),
        reference_answer=clean(row["instructor_answer"]) if with_reference else None,
    )
    return {
        "technical_accuracy": float(data["technical_accuracy"]),
        "content_mean": float(np.mean([data[k] for k in ("technical_accuracy", "relevance", "explanation_quality")])),
        "seconds": round(time.perf_counter() - t0, 1),
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--sample", choices=["stratified", "random", "all"], default="stratified")
    ap.add_argument("--modes", default="no_reference,reference")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rows = sample(load(args.data), args.limit, args.sample, args.seed)
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    print(f"Mohler ASAG: {len(rows)} answers ({args.sample}), modes {modes}, "
          f"LLM_PROVIDER={settings.LLM_PROVIDER}", flush=True)

    results = []
    for i, row in enumerate(rows, 1):
        item = {k: row[k] for k in ("id", "score_grader_1", "score_grader_2", "score_avg")}
        for mode in modes:
            try:
                item[mode] = await grade(row, with_reference=(mode == "reference"))
            except Exception as e:                  # one failed call shouldn't sink the run
                item[mode] = {"error": str(e)[:200]}
        results.append(item)
        status = "  ".join(f"{m}={item[m].get('technical_accuracy', 'ERR')}" for m in modes)
        print(f"[{i}/{len(rows)}] {row['id']} human={row['score_avg']}  {status}", flush=True)

    summary = {"dataset": "Mohler ASAG (nkazi/MohlerASAG, cleaned, open_ended)", "sample": args.sample,
               "seed": args.seed, "llm_provider": settings.LLM_PROVIDER, "modes": {}}
    both = [r for r in results if all("technical_accuracy" in r[m] for m in modes)]
    summary["human_vs_human"] = agreement([r["score_grader_1"] for r in both], [r["score_grader_2"] for r in both])
    # Every mode is scored on the same answers (those no mode failed on)
    for mode in modes:
        summary["modes"][mode] = {
            "technical_accuracy": agreement([r["score_avg"] for r in both], [r[mode]["technical_accuracy"] for r in both]),
            "content_mean": agreement([r["score_avg"] for r in both], [r[mode]["content_mean"] for r in both]),
            "failed_calls": sum(1 for r in results if "error" in r[mode]),
            "mean_seconds": round(float(np.mean([r[mode]["seconds"] for r in both])), 1) if both else None,
        }
    with open(args.out, "w") as f:
        json.dump({"summary": summary, "items": results}, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
