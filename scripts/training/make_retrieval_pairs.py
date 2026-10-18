"""Builds (student question, passage) pairs for fine-tuning the learning-service retriever.

    <train-venv>/bin/python scripts/training/make_retrieval_pairs.py [N_CHUNKS]

Chunks services/learning-service/data/ exactly as ingestion does (DocumentLoader strips the <!-- -->
headers, MarkdownChunker 600 chars / 100 overlap) and writes every chunk to corpus.jsonl. Source documents
are split 80/10/10 (seed 7) so test passages come from documents the model never saw. N_CHUNKS (default
1,000) chunks are sampled stratified by role/source and the local Gemma (port 8082, OpenAI-compatible API)
writes 3 realistic student questions for each -> pairs.jsonl, appended per chunk so a rerun resumes.
"""
import json
import random
import re
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "learning-service"))
from ingestion.chunker import MarkdownChunker  # noqa: E402
from ingestion.loader import DocumentLoader  # noqa: E402

OUT = Path("/Volumes/Dilmith Ext/datasets/training/retrieval")
LLM_URL = "http://127.0.0.1:8082/v1/chat/completions"
N_CHUNKS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
MIN_CHARS = 200          # shorter chunks (headings, link lists) don't support three distinct questions
SEED = 7

PROMPT = """Below is a passage from study material for a {role} career track (topic: {topic}).
Write 3 different questions a student might type into a learning assistant that this passage answers.
Make them realistic: short, natural wording, the way a student asks, not copied phrases from the passage.
Each question must be answerable from this passage alone and must not mention "the passage" or "the text".
Reply with only a JSON array of 3 strings.

Passage:
{passage}"""


def build_corpus():
    """All chunks of the corpus, with a document-level split."""
    docs = DocumentLoader.load_directory(str(REPO / "services" / "learning-service" / "data"))
    chunker = MarkdownChunker(chunk_size=600, chunk_overlap=100)
    order = list(range(len(docs)))
    random.Random(SEED).shuffle(order)
    n_train, n_valid = int(0.8 * len(docs)), int(0.1 * len(docs))
    split_of = {d: ("train" if i < n_train else "valid" if i < n_train + n_valid else "test")
                for i, d in enumerate(order)}
    corpus = []
    for d, doc in enumerate(docs):
        for c in chunker.split_text(doc["content"], {}):
            corpus.append({"chunk_id": len(corpus), "doc_id": d, "split": split_of[d], "title": doc["title"],
                           "topic": doc["topic"], "target_role": doc["target_role"], "source": doc["source"],
                           "content": c.content})
    return corpus


def sample(corpus, n):
    """Stratified by (role, source): each stratum gets its share of the n chunks (at least one)."""
    strata = defaultdict(list)
    for c in corpus:
        if len(c["content"]) >= MIN_CHARS:
            strata[(c["target_role"], c["source"])].append(c)
    rng = random.Random(SEED)
    total = sum(len(v) for v in strata.values())
    picked = []
    for key in sorted(strata):
        pool = strata[key]
        rng.shuffle(pool)
        picked += pool[:max(1, round(n * len(pool) / total))]
    rng.shuffle(picked)
    return sorted(picked[:n], key=lambda c: c["chunk_id"])


def ask(chunk):
    body = {"model": "default_model", "temperature": 0.7, "max_tokens": 300,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": PROMPT.format(
                role=chunk["target_role"], topic=chunk["topic"], passage=chunk["content"])}]}
    req = urllib.request.Request(LLM_URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    text = json.load(urllib.request.urlopen(req, timeout=180))["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", text, re.S)
    questions = [q.strip() for q in json.loads(m.group(0)) if isinstance(q, str) and q.strip()] if m else []
    return questions[:3]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    corpus = build_corpus()
    with open(OUT / "corpus.jsonl", "w") as f:
        for c in corpus:
            f.write(json.dumps(c) + "\n")
    chunks = sample(corpus, N_CHUNKS)
    pairs_path = OUT / "pairs.jsonl"
    done = {json.loads(line)["chunk_id"] for line in open(pairs_path)} if pairs_path.exists() else set()
    print(f"{len(corpus)} chunks from {len({c['doc_id'] for c in corpus})} documents; "
          f"{len(chunks)} sampled, {len(done)} already done", flush=True)
    t0, failed = time.time(), 0
    with open(pairs_path, "a") as f:
        for i, c in enumerate(chunks):
            if c["chunk_id"] in done:
                continue
            questions = []
            for _ in range(3):              # malformed JSON or a timeout: try again
                try:
                    questions = ask(c)
                    if len(questions) == 3:
                        break
                except Exception as e:      # noqa: BLE001
                    print(f"chunk {c['chunk_id']}: {e}", flush=True)
            if len(questions) != 3:
                failed += 1
                continue
            f.write(json.dumps({"chunk_id": c["chunk_id"], "doc_id": c["doc_id"], "split": c["split"],
                                "target_role": c["target_role"], "source": c["source"],
                                "questions": questions}) + "\n")
            f.flush()
            if i % 50 == 0:
                print(f"{i}/{len(chunks)} {time.time() - t0:.0f}s", flush=True)
    print(f"done in {(time.time() - t0) / 60:.1f} min, {failed} chunks failed", flush=True)


if __name__ == "__main__":
    main()
