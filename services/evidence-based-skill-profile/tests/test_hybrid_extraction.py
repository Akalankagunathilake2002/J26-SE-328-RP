import re

import pytest

from app.extraction.matcher import SkillEntry, SkillMatcher
from app.extraction.neural import CHUNK_WORDS, Span, chunks
from app.extraction.pipeline import extract_from_text
from app.normalisation.normaliser import Normaliser
from app.schemas.evidence import EvidenceType
from app.semantic.skill_index import SkillIndex
from tests.fakes import WordEncoder

ENTRIES = [
    SkillEntry("SK-1", "Python", ()),
    SkillEntry("SK-2", "Natural Language Processing", ("NLP",), "sentiment models"),
    SkillEntry("SK-3", "JavaScript", ("JS",)),
]
CV = """Skills
Python, Javascrpit
Projects
Built a chatbot in Python using LangChain. Analysed reviews with sentiment models.
"""


class PhraseSpans:
    """Stand-in for GLiNER: marks the given phrases wherever they appear."""

    def __init__(self, *phrases: str):
        self.phrases = phrases
        self.seen: list[str] = []

    def find(self, texts: list[str]) -> list[list[Span]]:
        self.seen += texts
        return [
            [Span(m.start(), m.end(), m.group(), 0.9)
             for phrase in self.phrases for m in re.finditer(re.escape(phrase), text)]
            for text in texts
        ]


@pytest.fixture
def layers():
    encoder = WordEncoder()
    return (SkillMatcher(ENTRIES),
            Normaliser(ENTRIES, encoder, SkillIndex.build(ENTRIES, encoder)))


def test_chunks_are_sentences_with_offsets_and_long_ones_are_cut():
    text = "Built an API. Wrote tests.\nDeployed it"
    assert [chunk for _, chunk in chunks(text)] == ["Built an API.", "Wrote tests.", "Deployed it"]
    for offset, chunk in chunks(text):
        assert text[offset:offset + len(chunk)] == chunk
    long = " ".join(f"w{i}" for i in range(CHUNK_WORDS + 5))
    assert [len(chunk.split()) for _, chunk in chunks(long)] == [CHUNK_WORDS, 5]


def test_gliner_adds_skills_the_dictionary_misses(layers):
    matcher, normaliser = layers
    spans = PhraseSpans("Javascrpit", "sentiment models", "LangChain", "Python")
    result = extract_from_text(CV, matcher=matcher, neural=spans, normaliser=normaliser)
    by_skill = {s.skill_id: s for s in result.skills}

    js = next(m for m in result.mentions if m.skill_id == "SK-3")
    assert (js.method, js.match_method, js.matched_text) == ("gliner", "fuzzy", "Javascrpit")
    assert js.evidence_type == EvidenceType.CV_SELF_REPORTED

    nlp = next(m for m in result.mentions if m.skill_id == "SK-2")
    assert (nlp.method, nlp.match_method) == ("gliner", "semantic")
    assert nlp.evidence_type == EvidenceType.PROJECT_DEMONSTRATED
    assert 0 < nlp.match_score < 0.9
    assert "SK-2" in by_skill and "SK-3" in by_skill

    # "LangChain" is not in the dictionary: kept as a new-skill candidate, not a skill.
    assert [u.text for u in result.unlinked] == ["LangChain"]


def test_dictionary_matches_win_over_gliner_spans(layers):
    matcher, normaliser = layers
    result = extract_from_text(CV, matcher=matcher, neural=PhraseSpans("Python"),
                               normaliser=normaliser)
    python = [m for m in result.mentions if m.skill_id == "SK-1"]
    assert len(python) == 2 and all(m.method == "dictionary" for m in python)


def test_offsets_of_gliner_mentions_point_into_the_cleaned_text(layers):
    from app.extraction.cleaner import clean_text

    matcher, normaliser = layers
    result = extract_from_text(CV, matcher=matcher, neural=PhraseSpans("sentiment models"),
                               normaliser=normaliser)
    text = clean_text(CV)
    for mention in result.mentions:
        assert text[mention.start:mention.end] == mention.matched_text


def test_dictionary_only_when_the_layer_is_off(layers):
    matcher, _ = layers
    result = extract_from_text(CV, matcher=matcher, neural=None, normaliser=None)
    assert {m.method for m in result.mentions} == {"dictionary"}
    assert result.unlinked == []


def test_weak_meaning_links_from_gliner_are_kept_unlinked(layers, monkeypatch):
    from app.config.settings import get_settings

    matcher, normaliser = layers
    monkeypatch.setattr(get_settings(), "neural_semantic_min", 0.99)
    result = extract_from_text(CV, matcher=matcher, neural=PhraseSpans("sentiment models"),
                               normaliser=normaliser)
    assert "SK-2" not in {m.skill_id for m in result.mentions}
    assert [u.text for u in result.unlinked] == ["sentiment models"]


def test_generic_single_words_from_gliner_are_ignored(layers):
    matcher, normaliser = layers
    result = extract_from_text("Projects\nInstalled software and new technology.", matcher=matcher,
                               neural=PhraseSpans("software", "technology"), normaliser=normaliser)
    assert result.mentions == [] and result.unlinked == []


def test_confidence_uses_the_match_score(layers):
    matcher, normaliser = layers
    result = extract_from_text(CV, matcher=matcher, neural=PhraseSpans("sentiment models"),
                               normaliser=normaliser)
    nlp = next(s for s in result.skills if s.skill_id == "SK-2")
    mention = next(m for m in result.mentions if m.skill_id == "SK-2")
    from app.evidence.fusion import Evidence, fuse

    assert mention.match_score < 1
    assert nlp.confidence == fuse([Evidence("document", "cv", mention.evidence_type,
                                            mention.match_score)])[0]
    assert nlp.confidence < fuse([Evidence("document", "cv", mention.evidence_type)])[0]


class FixedClassifier:
    """Stand-in for the SetFit model: every CV sentence is project evidence."""

    def __init__(self):
        self.calls = []

    def predict(self, items):
        self.calls.append(items)
        return [EvidenceType.PROJECT_DEMONSTRATED for _ in items]


def test_a_trained_classifier_replaces_the_rules_for_cvs(layers):
    matcher, _ = layers
    classifier = FixedClassifier()
    result = extract_from_text(CV, matcher=matcher, neural=None, normaliser=None,
                               evidence_classifier=classifier)
    assert {m.evidence_type for m in result.mentions} == {EvidenceType.PROJECT_DEMONSTRATED}
    assert len(classifier.calls) == 1  # one batch per document
    assert len(classifier.calls[0]) == len(set(classifier.calls[0]))  # each sentence once


def test_other_documents_keep_their_source_evidence_type(layers):
    from app.schemas.evidence import SourceType

    matcher, _ = layers
    result = extract_from_text("Python certificate", source=SourceType.CERTIFICATE,
                               matcher=matcher, neural=None, normaliser=None,
                               evidence_classifier=FixedClassifier())
    assert {m.evidence_type for m in result.mentions} == {EvidenceType.CERTIFICATE_SUPPORTED}


def test_the_model_decides_every_cv_sentence(layers):
    matcher, _ = layers
    classifier = FixedClassifier()
    text = "Summary\nInterested in learning JavaScript.\nSkills\nPython"
    result = extract_from_text(text, matcher=matcher, neural=None, normaliser=None,
                               evidence_classifier=classifier)
    assert {m.evidence_type for m in result.mentions} == {EvidenceType.PROJECT_DEMONSTRATED}
    assert [s for _, s in classifier.calls[0]] == ["Interested in learning JavaScript.", "Python"]


def test_without_a_trained_model_the_rules_are_the_fallback(monkeypatch, tmp_path):
    from app.config.settings import get_settings
    from app.evidence.classifier import get_evidence_classifier

    get_evidence_classifier.cache_clear()
    monkeypatch.setattr(get_settings(), "evidence_classifier", "setfit")
    monkeypatch.setattr(get_settings(), "evidence_model_dir", tmp_path / "missing")
    try:
        assert get_evidence_classifier() is None
    finally:
        get_evidence_classifier.cache_clear()
