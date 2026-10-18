"""Technical-accuracy scoring from the trained answer scorer and the LLM calibration.

Both come from scripts/training (Mohler ASAG, split by question) and live in models/answer_scorer:
  model.onnx + tokenizer.json   fine-tuned cross-encoder: (question + reference answer, answer) -> 0-5
  scoring_config.json           isotonic calibration of the LLM's score, blend weight, and the mode
                                that agreed best with human graders on validation questions
Modes: "llm" (the LLM's own score), "calibrated", "trained", "blend" (calibrated LLM + trained model).
Only technical accuracy changes, and only when the question has a reference answer to score against;
the LLM still writes all feedback. Missing model files leave the LLM's score unchanged.
"""
import json
import re
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import settings

MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "answer_scorer"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("<STOP>", " ")).strip()


class AnswerScorer:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = model_dir
        self._session = None
        self._tokenizer = None
        self._inputs: list[str] = []
        self._config: Optional[dict] = None

    @property
    def config(self) -> dict:
        if self._config is None:
            path = self.model_dir / "scoring_config.json"
            self._config = json.loads(path.read_text()) if path.exists() else {}
        return self._config

    @property
    def mode(self) -> str:
        return settings.SCORING_MODE if settings.SCORING_MODE != "auto" else self.config.get("mode", "llm")

    def _load_model(self):
        if self._session is None:
            import onnxruntime as ort
            from tokenizers import Tokenizer
            meta = json.loads((self.model_dir / "metadata.json").read_text())
            self._inputs = meta["inputs"]
            self._tokenizer = Tokenizer.from_file(str(self.model_dir / "tokenizer.json"))
            self._tokenizer.enable_truncation(meta["max_length"])
            self._session = ort.InferenceSession(str(self.model_dir / "model.onnx"), providers=["CPUExecutionProvider"])

    def trained_score(self, question: str, reference: str, answer: str) -> float:
        """0-5 from the fine-tuned cross-encoder (about 30 ms on CPU)."""
        self._load_model()
        e = self._tokenizer.encode(f"Question: {_clean(question)} Reference: {_clean(reference)}", _clean(answer))
        feed = {"input_ids": e.ids, "attention_mask": e.attention_mask, "token_type_ids": e.type_ids}
        logit = self._session.run(None, {n: np.asarray([feed[n]], np.int64) for n in self._inputs})[0].reshape(-1)[0]
        return float(5.0 / (1.0 + np.exp(-logit)))

    def calibrate(self, llm_score: float) -> float:
        cal = self.config.get("calibration")
        if not cal:
            return llm_score
        return float(np.interp(llm_score, cal["x"], cal["y"]))

    def technical_accuracy(self, llm_score: float, question: str, reference: Optional[str],
                           answer: str, role: Optional[str] = None) -> tuple[float, str]:
        """Final technical-accuracy score (1-5, the interview's scale) and the method that produced it.
        Non-technical roles keep the LLM's score: the scorer and calibration were fitted on CS answers."""
        from app.core.roles import is_technical
        mode = self.mode
        if mode == "llm" or not reference or not is_technical(role):
            return llm_score, "llm"
        try:
            if mode == "calibrated":
                score = self.calibrate(llm_score)
            elif mode == "trained":
                score = self.trained_score(question, reference, answer)
            elif mode == "blend":
                w = float(self.config.get("blend_weight_llm", 0.5))
                score = w * self.calibrate(llm_score) + (1 - w) * self.trained_score(question, reference, answer)
            else:
                return llm_score, "llm"
        except Exception as e:                       # missing or broken model files: keep the LLM's score
            print(f"[Warning] Answer scorer unavailable ({e}); using the LLM score.")
            return llm_score, "llm"
        return round(min(5.0, max(1.0, score)), 2), mode


answer_scorer = AnswerScorer()
