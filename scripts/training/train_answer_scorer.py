"""Fine-tunes a cross-encoder to score short technical answers 0-5 against a reference answer.

    export HF_HOME="/Volumes/Dilmith Ext/hf-cache"
    <train-venv>/bin/python scripts/training/train_answer_scorer.py [SPLIT_DIR]

Input pair: ("Question: ... Reference: ...", student answer); target: human score / 5. Trained on the
train questions of prepare_mohler_splits.py, model selected on valid, reported on the unseen test
questions. The result is exported to ONNX (with its tokenizer) for the interview service, which runs
it with onnxruntime and no PyTorch:
    services/interview-service/models/answer_scorer/{model.onnx, tokenizer.json, metadata.json}
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from sentence_transformers.cross_encoder import CrossEncoder, CrossEncoderTrainer, CrossEncoderTrainingArguments
from sentence_transformers.cross_encoder.losses import BinaryCrossEntropyLoss

sys.path.insert(0, str(Path(__file__).parent))
from metrics import agreement  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SPLITS = Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Dilmith Ext/datasets/training/mohler")
WORK = SPLITS.parent / "answer-scorer"
EXPORT = REPO / "services" / "interview-service" / "models" / "answer_scorer"
# Candidates (all Apache-2.0); the one with the best validation agreement is kept. MiniLM was pre-trained
# for search relevance, the STS-B models for semantic similarity, which is closer to grading.
CANDIDATES = ["cross-encoder/ms-marco-MiniLM-L6-v2", "cross-encoder/stsb-distilroberta-base",
              "cross-encoder/stsb-roberta-base"]
MAX_LENGTH = 256
SEED = 7


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("<STOP>", " ")).strip()


def pair_text(question: str, reference: str) -> str:
    # The interview service builds the same string (app/services/answer_scorer.py)
    return f"Question: {clean(question)} Reference: {clean(reference)}"


def load(name):
    return [json.loads(line) for line in open(SPLITS / f"{name}.jsonl") if line.strip()]


def to_dataset(rows):
    return Dataset.from_dict({
        "reference": [pair_text(r["question"], r["instructor_answer"]) for r in rows],
        "answer": [clean(r["student_answer"]) for r in rows],
        "label": [r["score_avg"] / 5.0 for r in rows],
    })


def predict(model, rows):
    """Score 0-5 = 5 * sigmoid(logit). Raw logits are taken explicitly: the models' saved default activation
    differs (MiniLM's is identity), and the interview service applies the same sigmoid to the ONNX output."""
    pairs = [(pair_text(r["question"], r["instructor_answer"]), clean(r["student_answer"])) for r in rows]
    logits = np.asarray(model.predict(pairs, batch_size=32, show_progress_bar=False,
                                      activation_fn=torch.nn.Identity()), float).reshape(-1)
    return 5.0 / (1.0 + np.exp(-logits))


def export_onnx(model: CrossEncoder, sample_rows):
    EXPORT.mkdir(parents=True, exist_ok=True)
    hf_model, tokenizer = model.model.eval().cpu(), model.tokenizer
    enc = tokenizer([pair_text(r["question"], r["instructor_answer"]) for r in sample_rows[:2]],
                    [clean(r["student_answer"]) for r in sample_rows[:2]],
                    padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
    names = [n for n in ("input_ids", "attention_mask", "token_type_ids") if n in enc]
    dynamic = {n: {0: "batch", 1: "sequence"} for n in names}
    dynamic["logits"] = {0: "batch"}
    torch.onnx.export(hf_model, tuple(enc[n] for n in names), str(EXPORT / "model.onnx"),
                      input_names=names, output_names=["logits"], dynamic_axes=dynamic, opset_version=17,
                      dynamo=False)
    tokenizer.backend_tokenizer.save(str(EXPORT / "tokenizer.json"))
    return names


def check_onnx(model: CrossEncoder, rows, names):
    """The exported model must score like the trained one."""
    import onnxruntime as ort
    from tokenizers import Tokenizer
    sess = ort.InferenceSession(str(EXPORT / "model.onnx"), providers=["CPUExecutionProvider"])
    tok = Tokenizer.from_file(str(EXPORT / "tokenizer.json"))
    tok.enable_truncation(MAX_LENGTH)
    diffs = []
    reference = predict(model, rows)
    for r, ref_score in zip(rows, reference):
        e = tok.encode(pair_text(r["question"], r["instructor_answer"]), clean(r["student_answer"]))
        feed = {"input_ids": [e.ids], "attention_mask": [e.attention_mask], "token_type_ids": [e.type_ids]}
        logit = sess.run(None, {n: np.asarray(feed[n], np.int64) for n in names})[0][0][0]
        diffs.append(abs(5.0 / (1.0 + np.exp(-logit)) - ref_score))
    return float(max(diffs))


def train_one(base: str, train, valid):
    torch.manual_seed(SEED)
    model = CrossEncoder(base, num_labels=1, max_length=MAX_LENGTH)
    args = CrossEncoderTrainingArguments(
        output_dir=str(WORK / base.split("/")[-1]), num_train_epochs=4, learning_rate=2e-5, warmup_ratio=0.1,
        per_device_train_batch_size=16, per_device_eval_batch_size=32, eval_strategy="epoch",
        save_strategy="epoch", save_total_limit=1, load_best_model_at_end=True,
        metric_for_best_model="eval_loss", logging_steps=50, seed=SEED, report_to=[])
    t0 = time.time()
    CrossEncoderTrainer(model=model, args=args, train_dataset=to_dataset(train), eval_dataset=to_dataset(valid),
                        loss=BinaryCrossEntropyLoss(model)).train()
    return model, round((time.time() - t0) / 60, 1)


def main():
    train, valid, test, test_llm = load("train"), load("valid"), load("test"), load("test_llm")
    human_valid = [r["score_avg"] for r in valid]
    runs, best = {}, None
    for base in CANDIDATES:
        model, minutes = train_one(base, train, valid)
        runs[base] = {"train_minutes": minutes, "valid": agreement(human_valid, predict(model, valid))}
        print(base, runs[base], flush=True)
        score = runs[base]["valid"]["pearson"] + runs[base]["valid"]["qwk"]
        if best is None or score > best[0]:
            best = (score, base, model)
    _, base, model = best

    # The test questions are used once, for the selected model only
    results = {"selected": base, "selection": "highest validation Pearson + QWK", "train_answers": len(train),
               "device": str(model.device), "candidates": runs,
               "test": agreement([r["score_avg"] for r in test], predict(model, test)),
               "test_llm": agreement([r["score_avg"] for r in test_llm], predict(model, test_llm))}
    model.save_pretrained(str(WORK / "final"))
    names = export_onnx(model, test)
    results["onnx_max_abs_diff"] = round(check_onnx(model, test[:40], names), 5)
    # 8-bit weights: a quarter of the size (RoBERTa-base 499 -> 125 MB) with no measurable accuracy loss
    from onnxruntime.quantization import QuantType, quantize_dynamic
    fp32 = WORK / "model.fp32.onnx"
    (EXPORT / "model.onnx").replace(fp32)
    quantize_dynamic(str(fp32), str(EXPORT / "model.onnx"), weight_type=QuantType.QInt8)
    model.to("cpu")
    t0 = time.time()
    predict(model, test[:100])
    results["cpu_ms_per_answer"] = round((time.time() - t0) * 10, 1)
    json.dump({"base_model": base, "max_length": MAX_LENGTH, "inputs": names, "quantization": "dynamic int8",
               "pair_format": "Question: {question} Reference: {reference}",
               "output": "logit; score = 5 * sigmoid(logit)",
               "trained_on": "Mohler ASAG train split (55 questions, 1,574 answers)",
               "metrics": {"valid": runs[base]["valid"], "test": results["test"], "test_llm": results["test_llm"]}},
              open(EXPORT / "metadata.json", "w"), indent=2)
    json.dump(results, open(WORK / "results.json", "w"), indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
