"""Step 3, model B: fine-tune JobBERT (jjzha/jobbert-base-cased) for skill NER on SkillSpan.

    .venv/bin/python src/train_jobbert.py [--version 0.1.0] [--epochs 5]

Runs on a CUDA GPU, the Apple GPU (MPS) or the CPU, whichever is available. Saves
models/jobbert-skill-ner-<version>/ with the model of the epoch with the best validation span F1,
its tokenizer and metadata.json (version, settings, data fingerprints, scores).

Google Colab (GPU runtime), if the local run is too slow:
    1. Upload src/common.py, src/train_jobbert.py and data/skillspan/{train,validation}.jsonl,
       keeping the same folders (ml/c01-skill-ner/src, ml/c01-skill-ner/data/skillspan).
    2. !pip install "transformers>=4.45" "datasets>=3.0" "accelerate>=1.0"
    3. !cd ml/c01-skill-ner && python src/train_jobbert.py
    4. Download models/jobbert-skill-ner-<version>/ into the same place on your computer.
Only SkillSpan goes to Colab; topjobs ads stay on your computer.

JobBERT (Zhang et al., 2022) has no licence stated on its model page: cite it and keep the model
out of git.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import UTC, datetime

import numpy as np
import torch
import transformers
from datasets import load_dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

from common import DATA, LABELS, MODELS, SEED, bio_to_spans, file_sha256, set_seed, write_json

BASE_MODEL = "jjzha/jobbert-base-cased"
TAGS = ["O"] + [f"{prefix}-{label}" for label in LABELS for prefix in ("B", "I")]
TAG_ID = {tag: i for i, tag in enumerate(TAGS)}
MAX_LENGTH = 256


def tokenize(batch, tokenizer):
    """Subword tokens; each word's label goes on its first subword (-100 elsewhere)."""
    encoded = tokenizer(batch["tokens"], is_split_into_words=True, truncation=True, max_length=MAX_LENGTH)
    labels = []
    for i, tags in enumerate(batch["ner_tags"]):
        previous, row = None, []
        for word in encoded.word_ids(batch_index=i):
            row.append(-100 if word is None or word == previous else TAG_ID[tags[word]])
            previous = word
        labels.append(row)
    encoded["labels"] = labels
    return encoded


def span_f1(predictions, label_ids) -> dict:
    """Exact-match span precision / recall / F1 over both labels (first-subword tags)."""
    tp = n_pred = n_gold = 0
    for pred_row, gold_row in zip(np.argmax(predictions, axis=-1), label_ids):
        keep = gold_row != -100
        pred = [TAGS[t] for t in pred_row[keep]]
        gold = [TAGS[t] for t in gold_row[keep]]
        pred_spans = {s for label in LABELS for s in bio_to_spans(_only(pred, label), label)}
        gold_spans = {s for label in LABELS for s in bio_to_spans(_only(gold, label), label)}
        tp += len(pred_spans & gold_spans)
        n_pred += len(pred_spans)
        n_gold += len(gold_spans)
    precision = tp / n_pred if n_pred else 0.0
    recall = tp / n_gold if n_gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def _only(tags: list[str], label: str) -> list[str]:
    return [t.split("-")[0] if t.endswith(label) else "O" for t in tags]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    set_seed(SEED)

    out = MODELS / f"jobbert-skill-ner-{args.version}"
    files = {split: str(DATA / "skillspan" / f"{split}.jsonl") for split in ("train", "validation")}
    data = load_dataset("json", data_files=files)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    encoded = data.map(lambda b: tokenize(b, tokenizer), batched=True, remove_columns=["tokens", "ner_tags"])
    model = AutoModelForTokenClassification.from_pretrained(
        BASE_MODEL, num_labels=len(TAGS), id2label=dict(enumerate(TAGS)), label2id=TAG_ID
    )
    training_args = TrainingArguments(
        output_dir=str(out / "checkpoints"),
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        warmup_steps=0.1,  # below 1: a share of all training steps (10% warm-up)
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        seed=SEED,
        data_seed=SEED,
        logging_steps=50,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=encoded["train"],
        eval_dataset=encoded["validation"],
        processing_class=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=lambda p: span_f1(p.predictions, p.label_ids),
    )
    started = datetime.now(UTC)
    trainer.train()
    scores = trainer.evaluate()
    trainer.save_model(str(out))
    tokenizer.save_pretrained(str(out))

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    write_json(out / "metadata.json", {
        "model": "jobbert-skill-ner",
        "version": args.version,
        "trained_at": started.isoformat(timespec="seconds"),
        "training_minutes": round((datetime.now(UTC) - started).total_seconds() / 60, 1),
        "device": device,
        "seed": SEED,
        "base_model": BASE_MODEL,
        "tags": TAGS,
        "settings": {"epochs": args.epochs, "learning_rate": args.learning_rate, "batch_size": args.batch_size,
                     "weight_decay": 0.01, "warmup": "first 10% of steps", "max_length": MAX_LENGTH,
                     "label_on": "first subword of each word"},
        "train_file_sha256": file_sha256(DATA / "skillspan" / "train.jsonl"),
        "best_validation_scores": {k: round(v, 4) for k, v in scores.items() if isinstance(v, float)},
        "versions": {"transformers": transformers.__version__, "torch": torch.__version__,
                     "python": platform.python_version()},
    })
    print(f"saved {out}; validation:", {k: round(v, 3) for k, v in scores.items() if k.startswith("eval_")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
