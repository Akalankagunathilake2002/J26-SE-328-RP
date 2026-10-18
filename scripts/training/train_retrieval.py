"""Fine-tunes the learning-service retriever on the pairs from make_retrieval_pairs.py.

    export HF_HOME="/Volumes/Dilmith Ext/hf-cache"
    <train-venv>/bin/python scripts/training/train_retrieval.py baseline   # current bge-small, mines hard negatives
    <train-venv>/bin/python scripts/training/train_retrieval.py embedder   # MNRL fine-tune, best epoch on valid
    <train-venv>/bin/python scripts/training/train_retrieval.py reranker   # cross-encoder vs rule-based re-ranking

Retrieval is always over ALL corpus chunks; only the chunk a question was written from counts as relevant.
Splits are by source document, so test passages come from documents unseen in training. Queries are embedded
without an instruction prefix, as embedding_service.py does. Results go to retrieval/results.json.
"""
import json
import random
import sys
import time
import types
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset

REPO = Path(__file__).resolve().parents[2]
WORK = Path("/Volumes/Dilmith Ext/datasets/training/retrieval")
BASE_EMBEDDER = "BAAI/bge-small-en-v1.5"
BASE_RERANKER = "cross-encoder/ms-marco-MiniLM-L6-v2"
MAX_LENGTH = 256          # 600-char chunks are about 150 tokens
SEED = 7


def load_data():
    corpus = [json.loads(line) for line in open(WORK / "corpus.jsonl")]
    queries = {"train": [], "valid": [], "test": []}
    for line in open(WORK / "pairs.jsonl"):
        p = json.loads(line)
        for q in p["questions"]:
            queries[p["split"]].append({"question": q, "chunk_id": p["chunk_id"], "doc_id": p["doc_id"]})
    return corpus, queries


def embed_corpus(model, corpus):
    return model.encode([c["content"] for c in corpus], batch_size=64, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=False)


def rank(model, corpus_emb, queries, k=100):
    q = model.encode([x["question"] for x in queries], batch_size=64, normalize_embeddings=True,
                     convert_to_numpy=True, show_progress_bar=False)
    sims = q @ corpus_emb.T
    top = np.argsort(-sims, axis=1)[:, :k]
    return top, np.take_along_axis(sims, top, axis=1)


def retrieval_metrics(rankings, queries):
    """recall@1/3/10 and MRR@10 of each query's source chunk in its ranked chunk ids."""
    pos = []
    for ids, q in zip(rankings, queries):
        hit = np.where(np.asarray(ids) == q["chunk_id"])[0]
        pos.append(int(hit[0]) + 1 if len(hit) else 10 ** 6)
    pos = np.asarray(pos)
    return {"n": len(queries), **{f"recall@{k}": round(float(np.mean(pos <= k)), 4) for k in (1, 3, 10)},
            "mrr@10": round(float(np.mean(np.where(pos <= 10, 1.0 / pos, 0.0))), 4)}


def mine_negatives(top, queries, corpus, per_query):
    """Highest-ranked chunks from OTHER documents: neighbouring chunks of the same document overlap the
    positive and often answer the question too, so they would be false negatives."""
    out = []
    for ids, q in zip(top, queries):
        out.append([int(i) for i in ids if corpus[i]["doc_id"] != q["doc_id"]][:per_query])
    return out


def results():
    path = WORK / "results.json"
    return json.load(open(path)) if path.exists() else {}


def save_results(update):
    r = results()
    r.update(update)
    json.dump(r, open(WORK / "results.json", "w"), indent=2)
    print(json.dumps(update, indent=2), flush=True)


def baseline():
    from sentence_transformers import SentenceTransformer
    corpus, queries = load_data()
    model = SentenceTransformer(BASE_EMBEDDER, device="mps")
    model.max_seq_length = MAX_LENGTH
    t0 = time.time()
    corpus_emb = embed_corpus(model, corpus)
    out = {"corpus_chunks": len(corpus), "queries": {s: len(v) for s, v in queries.items()},
           "corpus_embed_minutes": round((time.time() - t0) / 60, 1)}
    for split in ("valid", "test"):
        top, _ = rank(model, corpus_emb, queries[split])
        out[f"baseline_{split}"] = retrieval_metrics(top, queries[split])
    # Hard negatives for training come from the train questions only
    top, _ = rank(model, corpus_emb, queries["train"], k=50)
    negs = mine_negatives(top, queries["train"], corpus, per_query=1)
    with open(WORK / "train_hard_negatives.jsonl", "w") as f:
        for q, n in zip(queries["train"], negs):
            f.write(json.dumps({**q, "negative_ids": n}) + "\n")
    save_results(out)


def embedder():
    from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                       SentenceTransformerTrainingArguments)
    from sentence_transformers.losses import CachedMultipleNegativesRankingLoss
    from sentence_transformers.training_args import BatchSamplers
    corpus, queries = load_data()
    train = [json.loads(line) for line in open(WORK / "train_hard_negatives.jsonl")]
    train = [r for r in train if r["negative_ids"]]
    data = Dataset.from_dict({"anchor": [r["question"] for r in train],
                              "positive": [corpus[r["chunk_id"]]["content"] for r in train],
                              "negative": [corpus[r["negative_ids"][0]]["content"] for r in train]})
    torch.manual_seed(SEED)
    # Eager attention: MPS's fused attention has no dropout, which the cached loss's replayed forward needs
    model = SentenceTransformer(BASE_EMBEDDER, device="mps", model_kwargs={"attn_implementation": "eager"})
    model.max_seq_length = MAX_LENGTH
    out_dir = WORK / "embedder-checkpoints"
    args = SentenceTransformerTrainingArguments(
        output_dir=str(out_dir), num_train_epochs=2, learning_rate=2e-5, warmup_ratio=0.1,
        per_device_train_batch_size=32, batch_sampler=BatchSamplers.NO_DUPLICATES, save_strategy="epoch",
        logging_steps=20, seed=SEED, report_to=[])
    t0 = time.time()
    # Same loss and in-batch negatives as MultipleNegativesRankingLoss at batch 32, computed in mini-batches
    # of 8: the plain loss keeps activations for 96 texts of up to 256 tokens (about 11 GB) and on 18 Oct
    # swapped this 16 GB machine to a stall
    SentenceTransformerTrainer(model=model, args=args, train_dataset=data,
                               loss=CachedMultipleNegativesRankingLoss(model, mini_batch_size=8)).train()
    minutes = round((time.time() - t0) / 60, 1)

    # One checkpoint per epoch; keep the one with the best validation MRR
    epochs, embs = {}, {}
    for ckpt in sorted(out_dir.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[1])):
        m = SentenceTransformer(str(ckpt), device="mps")
        m.max_seq_length = MAX_LENGTH
        embs[ckpt.name] = embed_corpus(m, corpus)
        top, _ = rank(m, embs[ckpt.name], queries["valid"])
        epochs[ckpt.name] = retrieval_metrics(top, queries["valid"])
    best = max(epochs, key=lambda k: epochs[k]["mrr@10"])
    model = SentenceTransformer(str(out_dir / best), device="mps")
    model.max_seq_length = MAX_LENGTH
    corpus_emb = embs[best]
    top, _ = rank(model, corpus_emb, queries["test"])
    model.save(str(WORK / "embedder"))
    np.save(WORK / "embedder_corpus.npy", corpus_emb)
    save_results({"embedder": {"train_triplets": len(train), "train_minutes": minutes, "valid_by_epoch": epochs,
                               "selected": best, "test": retrieval_metrics(top, queries["test"])}})


def rule_based_reranker():
    """The service's reranker, importable without its pydantic settings (it doesn't use them)."""
    sys.path.insert(0, str(REPO / "services" / "learning-service"))
    stub = types.ModuleType("app.core.config")
    stub.settings = None
    sys.modules["app.core.config"] = stub
    from app.services.reranker import reranker_service
    return reranker_service


def candidates(model, corpus_emb, corpus, queries):
    top, sims = rank(model, corpus_emb, queries, k=10)
    return [[{"chunk_id": int(i), "content": corpus[i]["content"], "title": corpus[i]["title"],
              "topic": corpus[i]["topic"], "similarity_score": float(s)} for i, s in zip(ids, ss)]
            for ids, ss in zip(top, sims)]


def reranker():
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.cross_encoder import (CrossEncoder, CrossEncoderTrainer,
                                                     CrossEncoderTrainingArguments)
    from sentence_transformers.cross_encoder.losses import BinaryCrossEntropyLoss
    corpus, queries = load_data()
    emb = SentenceTransformer(str(WORK / "embedder"), device="mps")
    emb.max_seq_length = MAX_LENGTH
    corpus_emb = np.load(WORK / "embedder_corpus.npy")

    # Negatives from the fine-tuned embedder's top 10: the candidates the re-ranker will see in service
    top, _ = rank(emb, corpus_emb, queries["train"], k=30)
    negs = mine_negatives(top, queries["train"], corpus, per_query=3)
    q, p, y = [], [], []
    for x, n in zip(queries["train"], negs):
        q.append(x["question"]); p.append(corpus[x["chunk_id"]]["content"]); y.append(1.0)
        for i in n:
            q.append(x["question"]); p.append(corpus[i]["content"]); y.append(0.0)
    train = Dataset.from_dict({"query": q, "passage": p, "label": y})
    cand = {s: candidates(emb, corpus_emb, corpus, queries[s]) for s in ("valid", "test")}

    torch.manual_seed(SEED)
    model = CrossEncoder(BASE_RERANKER, num_labels=1, max_length=MAX_LENGTH)

    def ce_rank(m, split):
        out = []
        for x, cs in zip(queries[split], cand[split]):
            s = m.predict([(x["question"], c["content"]) for c in cs], batch_size=32, show_progress_bar=False)
            out.append([cs[i]["chunk_id"] for i in np.argsort(-np.asarray(s))])
        return out

    rule = rule_based_reranker()
    out = {"train_pairs": len(y), "candidates": "fine-tuned embedder top 10"}
    for split in ("valid", "test"):
        out[split] = {
            "embedder_order": retrieval_metrics([[c["chunk_id"] for c in cs] for cs in cand[split]], queries[split]),
            "rule_based": retrieval_metrics(
                [[c["chunk_id"] for c in rule.rerank_candidates(x["question"], cs, top_k=10, use_model=False)]
                 for x, cs in zip(queries[split], cand[split])], queries[split]),
            "ms_marco_minilm_untuned": retrieval_metrics(ce_rank(model, split), queries[split])}
    args = CrossEncoderTrainingArguments(
        output_dir=str(WORK / "reranker-checkpoints"), num_train_epochs=1, learning_rate=2e-5, warmup_ratio=0.1,
        per_device_train_batch_size=32, save_strategy="no", logging_steps=50, seed=SEED, report_to=[])
    t0 = time.time()
    CrossEncoderTrainer(model=model, args=args, train_dataset=train,
                        loss=BinaryCrossEntropyLoss(model)).train()
    out["train_minutes"] = round((time.time() - t0) / 60, 1)
    for split in ("valid", "test"):
        out[split]["fine_tuned"] = retrieval_metrics(ce_rank(model, split), queries[split])
    model.save_pretrained(str(WORK / "reranker"))
    out["onnx"] = export_reranker(model, queries["test"][:40], cand["test"][:40])
    save_results({"reranker": out})


def export_reranker(model, queries, cands):
    """ONNX int8 export as in train_answer_scorer.py, checked against the PyTorch model's ranking."""
    import onnxruntime as ort
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from tokenizers import Tokenizer
    out = WORK / "reranker-onnx"
    out.mkdir(exist_ok=True)
    hf_model, tok = model.model.eval().cpu(), model.tokenizer
    enc = tok(["a question"] * 2, ["a passage", "another passage"], padding=True, truncation=True,
              max_length=MAX_LENGTH, return_tensors="pt")
    names = [n for n in ("input_ids", "attention_mask", "token_type_ids") if n in enc]
    dynamic = {n: {0: "batch", 1: "sequence"} for n in names}
    dynamic["logits"] = {0: "batch"}
    torch.onnx.export(hf_model, tuple(enc[n] for n in names), str(out / "model.fp32.onnx"), input_names=names,
                      output_names=["logits"], dynamic_axes=dynamic, opset_version=17, dynamo=False)
    quantize_dynamic(str(out / "model.fp32.onnx"), str(out / "model.onnx"), weight_type=QuantType.QInt8)
    tok.backend_tokenizer.save(str(out / "tokenizer.json"))
    model.to("cpu")

    sess = ort.InferenceSession(str(out / "model.onnx"), providers=["CPUExecutionProvider"])
    t = Tokenizer.from_file(str(out / "tokenizer.json"))
    t.enable_truncation(MAX_LENGTH)
    t.enable_padding()
    same_top1, onnx_seconds = 0, 0.0
    for x, cs in zip(queries, cands):
        e = t.encode_batch([(x["question"], c["content"]) for c in cs])
        feed = {"input_ids": [i.ids for i in e], "attention_mask": [i.attention_mask for i in e],
                "token_type_ids": [i.type_ids for i in e]}
        t0 = time.time()
        onnx_scores = sess.run(None, {n: np.asarray(feed[n], np.int64) for n in names})[0].reshape(-1)
        onnx_seconds += time.time() - t0
        torch_scores = model.predict([(x["question"], c["content"]) for c in cs], show_progress_bar=False)
        same_top1 += int(np.argmax(onnx_scores) == np.argmax(torch_scores))
    return {"inputs": names, "top1_agreement_int8_vs_torch": f"{same_top1}/{len(queries)}",
            "size_mb": round((out / "model.onnx").stat().st_size / 2 ** 20, 1),
            "cpu_ms_per_query_top10": round(onnx_seconds / len(queries) * 1000, 1)}


def onnx_embed(sess, tok, texts, batch_size=32):
    """CLS vector, L2-normalised: what the services' embedding_service.py computes from the ONNX model."""
    out = np.zeros((len(texts), 384), np.float32)
    order = np.argsort([len(t) for t in texts])          # similar lengths per batch: less padding
    for s in range(0, len(texts), batch_size):
        idx = order[s:s + batch_size]
        enc = tok.encode_batch([texts[i] for i in idx])
        feed = {"input_ids": [e.ids for e in enc], "attention_mask": [e.attention_mask for e in enc],
                "token_type_ids": [e.type_ids for e in enc]}
        hidden = sess.run(None, {k: np.asarray(v, np.int64) for k, v in feed.items()})[0]
        cls = hidden[:, 0]
        out[idx] = cls / np.linalg.norm(cls, axis=1, keepdims=True)
    return out


def bootstrap_diff(a, b, n=10000):
    """Paired bootstrap 95% interval of mean(a - b) over questions."""
    d = np.asarray(a, float) - np.asarray(b, float)
    rng = np.random.default_rng(SEED)
    means = d[rng.integers(0, len(d), (n, len(d)))].mean(1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def reciprocal_ranks(rankings, queries):
    rr = []
    for ids, q in zip(rankings, queries):
        hit = list(ids[:10]).index(q["chunk_id"]) + 1 if q["chunk_id"] in list(ids[:10]) else 0
        rr.append(1.0 / hit if hit else 0.0)
    return rr


def export_embedder():
    """ONNX export (fp32 and dynamic int8), checked by retrieval over all chunks with onnxruntime as deployed,
    plus paired bootstrap intervals for the test gains of the embedder and the int8 re-ranker."""
    import onnxruntime as ort
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from sentence_transformers import SentenceTransformer
    from tokenizers import Tokenizer
    corpus, queries = load_data()
    test = queries["test"]
    out = WORK / "embedder-onnx"
    out.mkdir(exist_ok=True)
    model = SentenceTransformer(str(WORK / "embedder"), device="cpu")
    hf_model, tok = model[0].auto_model.eval(), model.tokenizer
    enc = tok(["a question", "a longer passage about indexes"], padding=True, return_tensors="pt")
    names = ["input_ids", "attention_mask", "token_type_ids"]
    class Encoder(torch.nn.Module):               # BertModel's positional arguments vary between versions
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.m(input_ids=input_ids, attention_mask=attention_mask,
                          token_type_ids=token_type_ids).last_hidden_state

    torch.onnx.export(Encoder(hf_model), tuple(enc[n] for n in names), str(out / "model.fp32.onnx"),
                      input_names=names, output_names=["last_hidden_state"], opset_version=17, dynamo=False,
                      dynamic_axes={**{n: {0: "batch", 1: "sequence"} for n in names},
                                    "last_hidden_state": {0: "batch", 1: "sequence"}})
    quantize_dynamic(str(out / "model.fp32.onnx"), str(out / "model.onnx"), weight_type=QuantType.QInt8)
    tok.backend_tokenizer.save(str(out / "tokenizer.json"))

    t = Tokenizer.from_file(str(out / "tokenizer.json"))
    t.enable_truncation(512)                              # fastembed's limit for bge-small, kept in service
    t.enable_padding()
    texts = [c["content"] for c in corpus]
    res = {}
    rankings = {}
    for name in ("model.fp32.onnx", "model.onnx"):
        sess = ort.InferenceSession(str(out / name), providers=["CPUExecutionProvider"])
        t0 = time.time()
        corpus_emb = onnx_embed(sess, t, texts)
        q = onnx_embed(sess, t, [x["question"] for x in test])
        top = np.argsort(-(q @ corpus_emb.T), axis=1)[:, :10]
        rankings[name] = top
        res[name] = {**retrieval_metrics(top, test), "corpus_embed_minutes": round((time.time() - t0) / 60, 1),
                     "size_mb": round((out / name).stat().st_size / 2 ** 20, 1)}
        if name == "model.onnx":
            np.save(WORK / "embedder_int8_corpus.npy", corpus_emb)

    # Baseline ranks for the paired comparison (same bge-small and settings as the baseline stage)
    base = SentenceTransformer(BASE_EMBEDDER, device="mps")
    base.max_seq_length = MAX_LENGTH
    base_top, _ = rank(base, embed_corpus(base, corpus), test, k=10)
    rr_base, rr_int8 = reciprocal_ranks(base_top, test), reciprocal_ranks(rankings["model.onnx"], test)
    res["mrr_gain_int8_vs_baseline_95ci"] = bootstrap_diff(rr_int8, rr_base)

    # Re-ranker int8 ONNX on the int8 embedder's candidates, against the rule-based re-ranker
    rsess = ort.InferenceSession(str(WORK / "reranker-onnx" / "model.onnx"), providers=["CPUExecutionProvider"])
    rt = Tokenizer.from_file(str(WORK / "reranker-onnx" / "tokenizer.json"))
    rt.enable_truncation(MAX_LENGTH)
    rt.enable_padding()
    rule = rule_based_reranker()
    ce_rank, rule_rank = [], []
    for qi, (x, ids) in enumerate(zip(test, rankings["model.onnx"])):   # q, corpus_emb: the int8 model's
        e = rt.encode_batch([(x["question"], corpus[i]["content"]) for i in ids])
        feed = {"input_ids": [i.ids for i in e], "attention_mask": [i.attention_mask for i in e],
                "token_type_ids": [i.type_ids for i in e]}
        s = rsess.run(None, {k: np.asarray(v, np.int64) for k, v in feed.items()})[0].reshape(-1)
        ce_rank.append([int(ids[i]) for i in np.argsort(-s)])
        cands = [{"chunk_id": int(i), "content": corpus[i]["content"], "title": corpus[i]["title"],
                  "topic": corpus[i]["topic"], "similarity_score": float(q[qi] @ corpus_emb[i])} for i in ids]
        rule_rank.append([c["chunk_id"] for c in rule.rerank_candidates(x["question"], cands, top_k=10, use_model=False)])
    res["reranker_int8"] = retrieval_metrics(ce_rank, test)
    res["rule_based_on_int8_candidates"] = retrieval_metrics(rule_rank, test)
    res["mrr_gain_reranker_int8_vs_embedder_order_95ci"] = bootstrap_diff(
        reciprocal_ranks(ce_rank, test), rr_int8)
    json.dump({"base_model": BASE_EMBEDDER, "fine_tuned_on": "learning-service corpus, 2,388 Gemma questions",
               "inputs": names, "output": "last_hidden_state; embedding = L2-normalised CLS vector",
               "dimension": 384, "max_length": 512, "quantization": "dynamic int8",
               "test": res["model.onnx"]}, open(out / "metadata.json", "w"), indent=2)
    save_results({"export": res})


if __name__ == "__main__":
    random.seed(SEED)
    {"baseline": baseline, "embedder": embedder, "reranker": reranker,
     "export": export_embedder}[sys.argv[1]]()
