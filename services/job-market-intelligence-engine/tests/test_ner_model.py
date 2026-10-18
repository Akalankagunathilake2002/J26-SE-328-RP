"""The real trained NER model, through the service's extractor. Skipped unless SKILLBRIDGE_NER_MODEL
points to a model folder and the NER packages are installed (ml/c01-skill-ner/README.md)."""

import os
from pathlib import Path

import pytest

MODEL = os.environ.get("SKILLBRIDGE_NER_MODEL")
pytestmark = pytest.mark.skipif(not MODEL or not Path(MODEL).is_dir(), reason="SKILLBRIDGE_NER_MODEL not set")


def test_model_returns_mentions_with_their_offsets():
    from app.processing.ner_extractor import load_ner

    text = "Requirements:\nExperience with Python, SQL and Power BI\nExcellent communication and teamwork skills"
    mentions = load_ner(MODEL).extract(text)

    assert mentions, "the model found no skill in an obvious requirements text"
    assert all(text[m.start:m.end] == m.text for m in mentions)
    assert all("\n" not in m.text and m.label in ("SKILL", "KNOWLEDGE") for m in mentions)
