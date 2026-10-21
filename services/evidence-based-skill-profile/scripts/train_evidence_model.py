"""Train the SetFit evidence classifier and compare it with the rules (TAF tasks 6 and 10).

Reads hand-labelled sentences (id, section, sentence, rule_label, label, split): rows with
split=train train the model, rows with split=test are only used to compare SetFit with the rules.
Rows whose label is empty or "skip" are left out. The model is saved to settings.evidence_model_dir
(not committed; anyone can re-train it from the CSV with this command).

    python -m scripts.train_evidence_model
    python -m scripts.train_evidence_model --file data/evaluation/evidence_labels.csv --seed 42
"""
import argparse
import csv
from pathlib import Path

from app.config.settings import SERVICE_DIR, get_settings
from app.evidence.classifier import MODEL_LABELS, model_input

DEFAULT_FILE = SERVICE_DIR / "data" / "evaluation" / "evidence_labels.csv"
BASE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _rows(path: Path, split: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f)
                if r["split"] == split and r["label"] not in ("", "skip")]


def _report(name: str, gold: list[str], predicted: list[str]) -> None:
    from sklearn.metrics import accuracy_score, classification_report, f1_score

    labels = [str(label) for label in MODEL_LABELS if label in set(gold) | set(predicted)]
    print(f"\n{name}: accuracy {accuracy_score(gold, predicted):.1%}, "
          f"macro F1 {f1_score(gold, predicted, labels=labels, average='macro', zero_division=0):.3f}")
    print(classification_report(gold, predicted, labels=labels, zero_division=0, digits=3))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--iterations", type=int, default=20, help="sentence pairs per example")
    args = parser.parse_args()

    from datasets import Dataset
    from setfit import SetFitModel, Trainer, TrainingArguments

    train, test = _rows(args.file, "train"), _rows(args.file, "test")
    print(f"train {len(train)} sentences, test {len(test)} sentences")
    for label in MODEL_LABELS:
        print(f"  {label:<22} train {sum(r['label'] == label for r in train):>3}   "
              f"test {sum(r['label'] == label for r in test):>3}")

    model = SetFitModel.from_pretrained(BASE_MODEL, labels=[str(label) for label in MODEL_LABELS])
    dataset = Dataset.from_dict({
        "text": [model_input(r["section"], r["sentence"]) for r in train],
        "label": [r["label"] for r in train],
    })
    trainer = Trainer(model=model, train_dataset=dataset, args=TrainingArguments(
        batch_size=16, num_epochs=1, num_iterations=args.iterations, seed=args.seed))
    trainer.train()

    gold = [r["label"] for r in test]
    _report("Rules (v1)", gold, [r["rule_label"] for r in test])
    _report("SetFit (v2)", gold,
            [str(p) for p in model.predict([model_input(r["section"], r["sentence"])
                                             for r in test])])

    out = get_settings().evidence_model_dir
    model.save_pretrained(str(out))
    print(f"Model saved to {out}")


if __name__ == "__main__":
    main()
