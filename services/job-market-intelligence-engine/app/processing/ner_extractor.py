"""Skill mentions found by a trained NER model (see ml/c01-skill-ner/).

Used when SKILLBRIDGE_SKILL_EXTRACTOR is ``ner`` or ``both``; SKILLBRIDGE_NER_MODEL points to the
model folder: a spaCy pipeline (with config.cfg) or a Hugging Face token-classification model
(with config.json), e.g. ml/c01-skill-ner/models/spacy-skill-ner-0.1.0/model-best.

The models are trained with two labels, SKILL (an ability, often a phrase) and KNOWLEDGE (a short
name such as "Python"). Both are skill mentions here; the label is kept for the record.

The NER packages are optional (``pip install -e ".[ner]"``, Python 3.12) and imported only when a
model is loaded, so the rest of the service runs without them.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# Bullets, quotes and punctuation trimmed around a mention ("." and "#"/"+" are kept where they
# belong to a name: ".NET", "C#", "C++").
LEADING_JUNK = re.compile(r"^[\s,;:()\[\]{}\"'•·*\-–—=>~|/\\]+")
TRAILING_JUNK = re.compile(r"[\s,;:.()\[\]{}\"'•·*\-–—=>~|/\\]+$")


@dataclass(frozen=True)
class Mention:
    text: str  # as written in the ad
    start: int  # character offsets in the text given to ``extract``
    end: int
    label: str  # SKILL or KNOWLEDGE


class NerExtractor(Protocol):
    def extract(self, text: str) -> list[Mention]: ...


def load_ner(path: Path | str) -> NerExtractor:
    path = Path(path)
    if (path / "config.cfg").is_file():
        return SpacyNer(path)
    if (path / "config.json").is_file():
        return TransformersNer(path)
    raise FileNotFoundError(f"No NER model in {path} (expected a spaCy or Hugging Face model folder)")


class SpacyNer:
    def __init__(self, path: Path) -> None:
        import spacy

        self.nlp = spacy.load(path)

    def extract(self, text: str) -> list[Mention]:
        lines = list(_lines(text))
        mentions = []
        for (offset, _), doc in zip(lines, self.nlp.pipe(line for _, line in lines)):
            for ent in doc.ents:
                mention = clean_mention(text, offset + ent.start_char, offset + ent.end_char, ent.label_)
                if mention:
                    mentions.append(mention)
        return mentions


class TransformersNer:
    def __init__(self, path: Path) -> None:
        from transformers import pipeline

        self.pipe = pipeline("token-classification", model=str(path), aggregation_strategy="first")

    def extract(self, text: str) -> list[Mention]:
        lines = list(_lines(text))
        mentions = []
        for (offset, _), entities in zip(lines, self.pipe([line for _, line in lines]) if lines else []):
            for entity in entities:
                mention = clean_mention(
                    text, offset + entity["start"], offset + entity["end"], entity["entity_group"]
                )
                if mention:
                    mentions.append(mention)
        return mentions


def clean_mention(text: str, start: int, end: int, label: str) -> Mention | None:
    """Trim punctuation and bullets around a mention; drop it if no word is left."""
    raw = text[start:end]
    leading = LEADING_JUNK.match(raw)
    skip = leading.end() if leading else 0
    trimmed = TRAILING_JUNK.sub("", raw[skip:])
    if len(trimmed) < 2 or not re.search(r"[A-Za-z]", trimmed):
        return None
    return Mention(trimmed, start + skip, start + skip + len(trimmed), label)


def _lines(text: str) -> Iterator[tuple[int, str]]:
    """Non-empty lines with their offsets: flyers are read line by line, so a skill never spans two."""
    offset = 0
    for line in text.split("\n"):
        if line.strip():
            yield offset, line
        offset += len(line) + 1
