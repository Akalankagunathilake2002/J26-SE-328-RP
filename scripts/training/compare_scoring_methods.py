"""Calibrates the LLM evaluator and compares every scoring method on the same unseen test answers.

    <train-venv>/bin/python scripts/training/compare_scoring_methods.py [SPLIT_DIR]

Needs gemma_valid_llm.json and gemma_test_llm.json (eval_mohler.py, "reference" mode, on the
valid_llm / test_llm subsets) and the exported answer scorer. Everything fitted (the isotonic
calibration, the blend weight) is fitted on the validation subset only; the test subset is used once.

Writes services/interview-service/models/answer_scorer/scoring_config.json, which the interview
service reads, and SPLIT_DIR/../scoring-comparison.json.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, str(Path(__file__).parent))
from metrics import agreement  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SPLITS = Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Dilmith Ext/datasets/training/mohler")
MODEL_DIR = REPO / "services" / "interview-service" / "models" / "answer_scorer"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("<STOP>", " ")).strip()


def load_rows(name):
    return {r["id"]: r for r in map(json.loads, open(SPLITS / f"{name}.jsonl"))}


def gemma_scores(name):
    items = json.load(open(SPLITS / f"gemma_{name}.json"))["items"]
    return {i["id"]: i["reference"]["technical_accuracy"] for i in items if "technical_accuracy" in i["reference"]}


class OnnxScorer:
    def __init__(self, path: Path):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        meta = json.load(open(path / "metadata.json"))
        self.inputs = meta["inputs"]
        self.session = ort.InferenceSession(str(path / "model.onnx"), providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tokenizer.enable_truncation(meta["max_length"])

    def score(self, question, reference, answer) -> float:
        e = self.tokenizer.encode(f"Question: {clean(question)} Reference: {clean(reference)}", clean(answer))
        feed = {"input_ids": e.ids, "attention_mask": e.attention_mask, "token_type_ids": e.type_ids}
        logit = self.session.run(None, {n: np.asarray([feed[n]], np.int64) for n in self.inputs})[0].reshape(-1)[0]
        return float(5.0 / (1.0 + np.exp(-logit)))


def main():
    scorer = OnnxScorer(MODEL_DIR)
    data = {}
    for part in ("valid_llm", "test_llm"):
        rows, gemma = load_rows(part), gemma_scores(part)
        ids = [i for i in rows if i in gemma]                 # answers Gemma graded successfully
        data[part] = {
            "human": np.array([rows[i]["score_avg"] for i in ids]),
            "gemma": np.array([gemma[i] for i in ids]),
            "trained": np.array([scorer.score(rows[i]["question"], rows[i]["instructor_answer"],
                                              rows[i]["student_answer"]) for i in ids]),
        }

    v, t = data["valid_llm"], data["test_llm"]
    iso = IsotonicRegression(y_min=0.0, y_max=5.0, out_of_bounds="clip").fit(v["gemma"], v["human"])
    v_cal, t_cal = iso.predict(v["gemma"]), iso.predict(t["gemma"])
    # Blend weight on calibrated Gemma, chosen by validation MAE
    grid = np.round(np.arange(0.0, 1.01, 0.05), 2)
    w = float(min(grid, key=lambda g: np.mean(np.abs(v["human"] - (g * v_cal + (1 - g) * v["trained"])))))
    blend = w * t_cal + (1 - w) * t["trained"]

    results = {
        "test_answers": int(len(t["human"])), "valid_answers": int(len(v["human"])), "blend_weight_gemma": w,
        "test": {
            "gemma_raw": agreement(t["human"], t["gemma"]),
            "gemma_calibrated": agreement(t["human"], t_cal),
            "trained_scorer": agreement(t["human"], t["trained"]),
            "blend": agreement(t["human"], blend),
        },
        "valid": {
            "gemma_raw": agreement(v["human"], v["gemma"]),
            "gemma_calibrated": agreement(v["human"], v_cal),
            "trained_scorer": agreement(v["human"], v["trained"]),
        },
    }
    # Default method for the service: the best on the *validation* subset by Pearson + QWK
    valid_blend = w * v_cal + (1 - w) * v["trained"]
    candidates = {"llm": v["gemma"], "calibrated": v_cal, "trained": v["trained"], "blend": valid_blend}
    def quality(pred):
        a = agreement(v["human"], pred)
        return a["pearson"] + a["qwk"]
    results["selected_mode"] = max(candidates, key=lambda m: quality(candidates[m]))

    json.dump({
        "mode": results["selected_mode"],
        "selection": "best validation Pearson + QWK among llm, calibrated, trained, blend",
        "calibration": {"x": [float(x) for x in iso.X_thresholds_], "y": [float(y) for y in iso.y_thresholds_]},
        "blend_weight_llm": w,
        "fitted_on": "Mohler ASAG valid_llm subset (12 questions not used for training)",
        "test_metrics": results["test"],
    }, open(MODEL_DIR / "scoring_config.json", "w"), indent=2)
    json.dump(results, open(SPLITS.parent / "scoring-comparison.json", "w"), indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
