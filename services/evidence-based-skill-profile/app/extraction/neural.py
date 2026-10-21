"""AI skill extraction with GLiNER, the second layer of the hybrid extractor (TAF task 4).

GLiNER (Zaratiana et al., NAACL 2024) is a pretrained zero-shot named entity recognition model:
it is given the entity types to look for as plain words ("skill") and marks the matching phrases,
with no training on our data. It finds skills the dictionary does not know or that are written in
other words ("analysed customer feedback with sentiment models"). It only finds phrases; the
normalisation engine (task 5) then gives each phrase a skill ID.

GLiNER reads at most a few hundred tokens at a time, so text is passed in chunks: one sentence or
line each, long ones cut into pieces of CHUNK_WORDS words.

Distractor labels: GLiNER gives each phrase the best of the labels it is asked for. Asking only for
"skill" makes it call job titles ("Receptionist") and degrees ("Computer Information Systems")
skills. So it is also asked for "job title", "degree" and "organization", and only phrases labelled
with one of keep_labels are returned.
"""
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.config.settings import get_settings

CHUNK_WORDS = 120
SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z])|\n")
WORD = re.compile(r"\S+")


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    text: str
    score: float
    label: str = "skill"


class SpanExtractor(Protocol):
    def find(self, texts: list[str]) -> list[list[Span]]:
        """Skill phrases in each text, with character offsets into that text."""
        ...


def chunks(text: str) -> list[tuple[int, str]]:
    """(offset, chunk) pairs covering the text: sentences or lines, long ones cut by words."""
    pieces = []
    start = 0
    for found in [*SENTENCE_BREAK.finditer(text), None]:
        end = found.start() if found else len(text)
        sentence = text[start:end]
        words = list(WORD.finditer(sentence))
        for i in range(0, len(words), CHUNK_WORDS):
            group = words[i:i + CHUNK_WORDS]
            a, b = group[0].start(), group[-1].end()
            pieces.append((start + a, sentence[a:b]))
        if found:
            start = found.end()
    return pieces


class GlinerExtractor:
    def __init__(self, model_name: str, labels: list[str], keep_labels: list[str],
                 threshold: float, batch_size: int = 8):
        from gliner import GLiNER  # heavy import, load on first use

        self._model = GLiNER.from_pretrained(model_name)
        self._model.eval()
        self.labels, self.keep_labels = labels, set(keep_labels)
        self.threshold, self.batch_size = threshold, batch_size

    def find(self, texts: list[str]) -> list[list[Span]]:
        if not texts:
            return []
        predictions = self._model.inference(texts, self.labels, threshold=self.threshold,
                                            batch_size=self.batch_size)
        return [
            [Span(p["start"], p["end"], p["text"], float(p["score"]), p["label"])
             for p in found if p["label"] in self.keep_labels]
            for found in predictions
        ]


@lru_cache
def get_span_extractor() -> GlinerExtractor:
    settings = get_settings()
    return GlinerExtractor(settings.gliner_model, settings.gliner_labels,
                           settings.gliner_keep_labels, settings.gliner_threshold)
