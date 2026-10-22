"""Document → cleaned text → sections → skill mentions with evidence types (TAF tasks 3, 4, 6).

Skills are found by a hybrid of two layers (task 4):
1. dictionary  spaCy PhraseMatcher over every dictionary name and alias (exact, very precise)
2. gliner      GLiNER zero-shot extraction of skill phrases in any wording; each phrase is mapped
               to a skill ID by the normalisation engine (task 5). Phrases overlapping a
               dictionary match are skipped (the dictionary already has the ID). Phrases
               without an ID, or linked only by a weak meaning match (cosine below
               settings.neural_semantic_min), are returned as `unlinked` (new-skill candidates).
"""
import logging
import re
from functools import lru_cache

from app.config.settings import get_settings
from app.evidence.fusion import Evidence, confidence_level, fuse
from app.evidence.rules import classify_evidence
from app.extraction.cleaner import clean_text
from app.extraction.matcher import METHOD, SkillMatcher
from app.extraction.neural import SpanExtractor, chunks
from app.extraction.reader import extract_text
from app.extraction.sections import split_sections
from app.normalisation.normaliser import Normaliser
from app.schemas.evidence import SourceType
from app.schemas.extraction import (
    DocumentExtraction, DocumentSkill, Section, SkillMention, UnlinkedSpan,
)
from app.schemas.normalisation import MatchMethod

logger = logging.getLogger(__name__)
NEURAL_METHOD = "gliner"
# Single words GLiNER marks as skills that are too general to be one ("software" is not
# "Software libraries"). Found by reading GLiNER output on the Kaggle CVs.
GENERIC_WORDS = {
    "ability", "abilities", "computer", "computers", "experience", "experienced", "expertise",
    "hardware", "it", "knowledge", "skill", "skills", "software", "system", "systems",
    "technical", "technologies", "technology", "tool", "tools",
}
DEFAULT = object()  # "use the configured layer"

# Each document is scored on its own here; the profile (task 8) fuses across documents.
DOCUMENT = "document"
SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z])|\n")


@lru_cache
def get_matcher() -> SkillMatcher:
    settings = get_settings()
    return SkillMatcher.from_csv(settings.dictionary_path, settings.matcher_rules_path)


def _sentence_around(text: str, start: int, end: int) -> str:
    """The sentence (or line) that contains text[start:end]."""
    left = 0
    for found in SENTENCE_BREAK.finditer(text, 0, start):
        left = found.end()
    right_match = SENTENCE_BREAK.search(text, end)
    right = right_match.start() if right_match else len(text)
    return text[left:right].strip()


def _skill(skill_id: str, found: list[SkillMention], source: SourceType) -> DocumentSkill:
    confidence, evidence = fuse(
        Evidence(DOCUMENT, source, m.evidence_type, m.match_score) for m in found
    )
    return DocumentSkill(
        skill_id=skill_id,
        name=found[0].name,
        mention_count=len(found),
        evidence_types=list(dict.fromkeys(m.evidence_type for m in found)),
        sections=list(dict.fromkeys(m.section for m in found)),
        confidence=confidence,
        confidence_level=confidence_level(confidence),
        evidence=evidence,
    )


def _group_by_skill(mentions: list[SkillMention], source: SourceType) -> list[DocumentSkill]:
    """One entry per skill, most confident first."""
    grouped: dict[str, list[SkillMention]] = {}
    for mention in mentions:
        grouped.setdefault(mention.skill_id, []).append(mention)
    skills = [_skill(skill_id, found, source) for skill_id, found in grouped.items()]
    return sorted(skills, key=lambda s: (-s.confidence, s.name))


def _default_layers() -> tuple[SpanExtractor | None, Normaliser | None]:
    """The configured GLiNER layer and normaliser, or (None, None) when off or not loadable."""
    if not get_settings().use_neural_extraction:
        return None, None
    try:
        from app.extraction.neural import get_span_extractor
        from app.normalisation.normaliser import get_normaliser

        return get_span_extractor(), get_normaliser()
    except Exception as error:  # a missing model must not stop dictionary extraction
        logger.warning("GLiNER layer off, dictionary only: %s", error)
        return None, None


def _neural_mentions(
    sections: list[Section], taken: list[tuple[int, int]], source: SourceType,
    neural: SpanExtractor, normaliser: Normaliser, semantic_min: float,
) -> tuple[list[SkillMention], list[UnlinkedSpan]]:
    pieces = [(section, offset, chunk) for section in sections
              for offset, chunk in chunks(section.text)]
    found = []
    for (section, offset, _), spans in zip(pieces, neural.find([c for _, _, c in pieces])):
        for span in spans:
            if span.text.strip().lower() in GENERIC_WORDS:
                continue
            start, end = section.start + offset + span.start, section.start + offset + span.end
            if any(start < b and a < end for a, b in taken):
                continue
            found.append((section, offset + span.start, offset + span.end, span))
    texts = list(dict.fromkeys(span.text for *_, span in found))
    linked = dict(zip(texts, normaliser.normalise(texts)))

    mentions, unlinked = [], []
    for section, start, end, span in found:
        sentence = _sentence_around(section.text, start, end)
        result = linked[span.text]
        weak_link = result.method == MatchMethod.SEMANTIC and result.score < semantic_min
        if result.skill_id is None or result.method == MatchMethod.ESCO_CANDIDATE or weak_link:
            unlinked.append(UnlinkedSpan(text=span.text, section=section.type, sentence=sentence,
                                         detection_score=round(span.score, 3)))
            continue
        mentions.append(SkillMention(
            skill_id=result.skill_id,
            name=result.name,
            matched_text=span.text,
            start=section.start + start,
            end=section.start + end,
            section=section.type,
            sentence=sentence,
            method=NEURAL_METHOD,
            match_method=result.method,
            match_score=round(span.score * result.score, 3),
            evidence_type=classify_evidence(source, section.type, sentence, span.text),
        ))
    return mentions, unlinked


def _classify_with_model(mentions: list[SkillMention], classifier) -> list[SkillMention]:
    """Set the evidence type of every CV mention from the SetFit model (one batch per document)."""
    items = list(dict.fromkeys((m.section, m.sentence) for m in mentions))
    predicted = dict(zip(items, classifier.predict(items)))
    return [m.model_copy(update={"evidence_type": predicted[(m.section, m.sentence)]})
            for m in mentions]


def extract_from_text(
    raw_text: str, source: SourceType = SourceType.CV, matcher: SkillMatcher | None = None,
    neural: SpanExtractor | None = DEFAULT, normaliser: Normaliser | None = DEFAULT,
    evidence_classifier=DEFAULT,
) -> DocumentExtraction:
    """Find the skills in one document. neural/normaliser default to the configured GLiNER layer
    and evidence_classifier to the configured one (rules or SetFit); pass None to turn a layer
    off (dictionary only, rules only)."""
    matcher = matcher or get_matcher()
    if evidence_classifier is DEFAULT:
        from app.evidence.classifier import get_evidence_classifier

        evidence_classifier = get_evidence_classifier()
    if neural is DEFAULT or normaliser is DEFAULT:
        default_neural, default_normaliser = _default_layers()
        neural = default_neural if neural is DEFAULT else neural
        normaliser = default_normaliser if normaliser is DEFAULT else normaliser
    text = clean_text(raw_text)
    sections = split_sections(text)
    mentions = []
    for section in sections:
        for match in matcher.find(section.text):
            sentence = _sentence_around(section.text, match.start, match.end)
            mentions.append(SkillMention(
                skill_id=match.skill_id,
                name=match.name,
                matched_text=match.matched_text,
                start=section.start + match.start,
                end=section.start + match.end,
                section=section.type,
                sentence=sentence,
                method=METHOD,
                evidence_type=classify_evidence(source, section.type, sentence,
                                                match.matched_text),
            ))
    unlinked = []
    if neural is not None and normaliser is not None:
        taken = [(m.start, m.end) for m in mentions]
        extra, unlinked = _neural_mentions(sections, taken, source, neural, normaliser,
                                           get_settings().neural_semantic_min)
        mentions = sorted(mentions + extra, key=lambda m: m.start)
    if evidence_classifier is not None and source == SourceType.CV and mentions:
        mentions = _classify_with_model(mentions, evidence_classifier)
    return DocumentExtraction(
        source_type=source,
        sections=[section.type for section in sections],
        mentions=mentions,
        skills=_group_by_skill(mentions, source),
        unlinked=unlinked,
    )


def extract_from_document(
    data: bytes, filename: str, source: SourceType = SourceType.CV,
    matcher: SkillMatcher | None = None,
    neural: SpanExtractor | None = DEFAULT, normaliser: Normaliser | None = DEFAULT,
    evidence_classifier=DEFAULT,
) -> DocumentExtraction:
    return extract_from_text(extract_text(data, filename), source, matcher, neural, normaliser,
                             evidence_classifier)
