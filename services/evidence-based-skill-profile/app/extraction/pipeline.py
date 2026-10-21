"""Document → cleaned text → sections → skill mentions with evidence types (TAF tasks 3, 4, 6)."""
import re
from functools import lru_cache

from app.config.settings import get_settings
from app.evidence.rules import classify_evidence
from app.extraction.cleaner import clean_text
from app.extraction.matcher import METHOD, SkillMatcher
from app.extraction.reader import extract_text
from app.extraction.sections import split_sections
from app.schemas.evidence import SourceType
from app.schemas.extraction import DocumentExtraction, DocumentSkill, SkillMention

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


def _group_by_skill(mentions: list[SkillMention]) -> list[DocumentSkill]:
    grouped: dict[str, list[SkillMention]] = {}
    for mention in mentions:
        grouped.setdefault(mention.skill_id, []).append(mention)
    return [
        DocumentSkill(
            skill_id=skill_id,
            name=found[0].name,
            mention_count=len(found),
            evidence_types=list(dict.fromkeys(m.evidence_type for m in found)),
            sections=list(dict.fromkeys(m.section for m in found)),
        )
        for skill_id, found in grouped.items()
    ]


def extract_from_text(
    raw_text: str, source: SourceType = SourceType.CV, matcher: SkillMatcher | None = None
) -> DocumentExtraction:
    matcher = matcher or get_matcher()
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
                evidence_type=classify_evidence(source, section.type, sentence),
            ))
    return DocumentExtraction(
        source_type=source,
        sections=[section.type for section in sections],
        mentions=mentions,
        skills=_group_by_skill(mentions),
    )


def extract_from_document(
    data: bytes, filename: str, source: SourceType = SourceType.CV,
    matcher: SkillMatcher | None = None,
) -> DocumentExtraction:
    return extract_from_text(extract_text(data, filename), source, matcher)
