"""Paths, the fixed seed, and the span rules shared by data preparation, training and evaluation."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # ml/c01-skill-ner/
DATA = ROOT / "data"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
SEED = 42

# Training keeps SkillSpan's two kinds of span apart: KNOWLEDGE is a short name ("docker",
# "agile"), SKILL an ability, often a phrase ("design and implement end-to-end tests").
# For evaluation and in the service both count as one kind: a skill mention (MERGED_LABEL).
LABELS = ("SKILL", "KNOWLEDGE")
MERGED_LABEL = "SKILL"


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    try:
        import numpy

        numpy.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass


@dataclass(frozen=True)
class Span:
    start: int  # first token (or character, for text spans)
    end: int  # one past the last
    label: str

    def overlaps(self, other: Span) -> bool:
        return self.start < other.end and other.start < self.end


def bio_to_spans(tags: list[str], label: str) -> list[Span]:
    """Spans from one BIO column ("B", "I", "O"); an "I" without a "B" starts a span."""
    spans, start = [], None
    for i, tag in enumerate([*tags, "O"]):
        tag = tag.split("-")[0]
        if tag in ("B", "O") or (tag == "I" and start is None):
            if start is not None:
                spans.append(Span(start, i, label))
                start = None
            if tag in ("B", "I"):
                start = i
    return spans


def skillspan_spans(row: dict) -> tuple[list[Span], int]:
    """A SkillSpan sentence's spans with both labels. Where a skill and a knowledge span overlap,
    the knowledge span is kept: it is the shorter name that SSKS can match. Returns the spans and
    how many skill spans were dropped."""
    knowledge = bio_to_spans(row["tags_knowledge"], "KNOWLEDGE")
    skills = bio_to_spans(row["tags_skill"], "SKILL")
    kept = [s for s in skills if not any(s.overlaps(k) for k in knowledge)]
    return sorted(knowledge + kept, key=lambda s: s.start), len(skills) - len(kept)


def spans_to_bio(n_tokens: int, spans: list[Span]) -> list[str]:
    tags = ["O"] * n_tokens
    for span in spans:
        tags[span.start] = f"B-{span.label}"
        for i in range(span.start + 1, span.end):
            tags[i] = f"I-{span.label}"
    return tags


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
