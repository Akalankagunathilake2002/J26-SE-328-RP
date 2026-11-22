"""Does the fine-tuned embedder pick better interview questions than the original bge-small?

The embedder was fine-tuned on learning-corpus questions (train_retrieval.py), but the interview service uses it
too, to choose a question for a role, level and topic. This measures that use directly on the question bank
(services/interview-service/data/*.json), the way interview_rag.py searches it:

  query    "<role> <level> <topic>"       (what generate_interview_question builds, without CV skills)
  corpus   "<title> <topic> <question> <expected answer>" for every bank item of that role
           (ingest_rubrics.py embeds the same text; the search is filtered to the role)
  relevant items of the same role and topic

Metrics per query: MRR@10 (first relevant item), precision@5 (share of the top 5 on the topic) and
level-match@5 (share of the top 5 on the topic AND at the requested level). One query per distinct
(role, level, topic) in the bank. Paired permutation test on per-query MRR.

Run (the training venv has sentence-transformers):
  "/Volumes/Dilmith Ext/datasets/train-venv/bin/python" scripts/training/eval_interview_retrieval.py \\
      --tuned "/Volumes/Dilmith Ext/datasets/training/retrieval/embedder" --out results.json
"""
import argparse
import glob
import json
import os
import random
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANK = os.path.join(ROOT, "services", "interview-service", "data")


def load_bank():
    items = []
    for path in sorted(glob.glob(os.path.join(BANK, "*.json"))):
        with open(path, encoding="utf-8") as f:
            items += json.load(f)
    return items


def doc_text(item):
    return f"{item['title']} {item['topic']} {item['content']} {item.get('expected_answer', '')}"


def evaluate(model, items, queries, k=10):
    by_role = defaultdict(list)
    for i, it in enumerate(items):
        by_role[it["role"]].append(i)
    doc_vecs = model.encode([doc_text(it) for it in items], batch_size=16, normalize_embeddings=True,
                            show_progress_bar=False)
    q_vecs = model.encode([q["text"] for q in queries], batch_size=32, normalize_embeddings=True,
                          show_progress_bar=False)
    rows = []
    for q, qv in zip(queries, q_vecs):
        pool = by_role[q["role"]]
        sims = doc_vecs[pool] @ qv
        ranked = [pool[j] for j in np.argsort(-sims)[:k]]
        on_topic = [items[i]["topic"] == q["topic"] for i in ranked]
        level_ok = [items[i]["topic"] == q["topic"] and items[i]["difficulty"] == q["level"] for i in ranked]
        mrr = next((1.0 / r for r, hit in enumerate(on_topic, 1) if hit), 0.0)
        rows.append({"mrr@10": mrr, "precision@5": sum(on_topic[:5]) / 5, "level_match@5": sum(level_ok[:5]) / 5,
                     "hit@1": float(on_topic[0])})
    return rows


def mean(rows, key):
    return round(float(np.mean([r[key] for r in rows])), 4)


def permutation_p(diffs, n=10000, seed=7):
    rng = random.Random(seed)
    obs = abs(np.mean(diffs))
    extreme = sum(abs(np.mean([d if rng.random() < 0.5 else -d for d in diffs])) >= obs - 1e-12 for _ in range(n))
    return round((extreme + 1) / (n + 1), 4)


def main():
    from sentence_transformers import SentenceTransformer
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--tuned", default="/Volumes/Dilmith Ext/datasets/training/retrieval/embedder")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    items = load_bank()
    seen, queries = set(), []
    for it in items:
        key = (it["role"], it["difficulty"], it["topic"])
        if key not in seen:
            seen.add(key)
            queries.append({"role": key[0], "level": key[1], "topic": key[2], "text": " ".join(key)})
    # Only topics with an alternative to find are informative, but every query counts (a topic with one
    # item still has to rank that item first)
    print(f"{len(items)} bank items, {len({i['role'] for i in items})} roles, {len(queries)} queries")

    results = {}
    per_query = {}
    for name, path in (("base", args.base), ("fine_tuned", args.tuned)):
        model = SentenceTransformer(path, device="cpu")
        rows = evaluate(model, items, queries)
        per_query[name] = rows
        results[name] = {m: mean(rows, m) for m in ("mrr@10", "hit@1", "precision@5", "level_match@5")}
        print(name, results[name])
        del model

    diffs = [t["mrr@10"] - b["mrr@10"] for b, t in zip(per_query["base"], per_query["fine_tuned"])]
    results["mrr_difference"] = round(float(np.mean(diffs)), 4)
    results["p_value_mrr"] = permutation_p(diffs)
    results["queries"] = len(queries)
    results["bank_items"] = len(items)
    print("MRR difference", results["mrr_difference"], "p =", results["p_value_mrr"])
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
