"""Build one skill profile from several student documents (TAF task 2, feeding tasks 7 and 8).

Each document (CV, project description, academic document, certificate) is read and its skills
found on its own, with its source type. The type of an uploaded file is detected from its content
(app/collection/document_type.py), never taken from the student, because it decides how strong
the evidence is. The evidence for each skill from all documents is then
fused into one confidence: proof from independent documents adds up (Noisy-OR), and support from
several kinds of document raises it further (source diversity). So a skill listed in the CV and
backed by a project report and a certificate becomes strong, while a skill only listed stays weak.
"""
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.evidence.fusion import Evidence, confidence_level, fuse
from app.extraction.pipeline import extract_from_document
from app.schemas.evidence import SourceType
from app.schemas.extraction import DocumentExtraction, SkillMention
from app.schemas.profile import ProfileDocument, ProfileSkill, SkillProfile


@dataclass(frozen=True)
class SubmittedDocument:
    name: str
    data: bytes
    source_type: SourceType | None = None  # None: detect it (always, for student uploads)


Extractor = Callable[[bytes, str, SourceType], DocumentExtraction]
# File bytes and name -> detected type.
TypeDetector = Callable[[bytes, str], "DetectedType"]


def _detect_type(data: bytes, name: str):
    from app.collection.document_type import get_document_type_detector
    from app.extraction.reader import extract_text

    return get_document_type_detector().detect(extract_text(data, name))


def default_type_detector() -> TypeDetector:
    """The type detector the service uses (a FastAPI dependency, so tests can replace it)."""
    return _detect_type
# A portfolio link -> one (document name, extraction) per repository or work sample.
LinkReader = Callable[[str], list]


def _read_github(url: str) -> list:
    from app.collection.github import get_github_reader

    return get_github_reader().read(url)


def default_link_reader() -> LinkReader:
    """The link reader the service uses (a FastAPI dependency, so tests can replace it)."""
    return _read_github


def _unique_names(documents: list[SubmittedDocument]) -> list[str]:
    """Document names, with " (2)", " (3)" added to repeated ones so evidence stays separate."""
    seen: dict[str, int] = {}
    names = []
    for document in documents:
        seen[document.name] = seen.get(document.name, 0) + 1
        count = seen[document.name]
        names.append(document.name if count == 1 else f"{document.name} ({count})")
    return names


def fuse_skills(found: list[tuple[str, SourceType, SkillMention]]) -> list[ProfileSkill]:
    """One ProfileSkill per skill from (document name, source type, mention) triples."""
    by_skill: dict[str, list[tuple[str, SourceType, SkillMention]]] = {}
    for item in found:
        by_skill.setdefault(item[2].skill_id, []).append(item)
    skills = []
    for skill_id, items in by_skill.items():
        confidence, evidence = fuse(
            Evidence(name, source, m.evidence_type, m.match_score) for name, source, m in items
        )
        skills.append(ProfileSkill(
            skill_id=skill_id,
            name=items[0][2].name,
            confidence=confidence,
            confidence_level=confidence_level(confidence),
            evidence=evidence,
            documents=list(dict.fromkeys(name for name, _, _ in items)),
            source_types=list(dict.fromkeys(source for _, source, _ in items)),
            mentions=[m for _, _, m in items],
        ))
    return sorted(skills, key=lambda s: (-s.confidence, s.name))


def _read_all(documents: list[SubmittedDocument], extract: Extractor,
              links: Sequence[str] = (), read_link: LinkReader = _read_github,
              detect: TypeDetector = _detect_type):
    summaries, found, unlinked = [], [], []

    def add(name: str, source: SourceType, result: DocumentExtraction,
            detected_by: str | None = None, confidence: float | None = None) -> None:
        summaries.append(ProfileDocument(
            name=name, source_type=source, type_detected_by=detected_by,
            type_confidence=confidence, sections=result.sections,
            skill_count=len({m.skill_id for m in result.mentions})))
        found.extend((name, source, mention) for mention in result.mentions)
        unlinked.extend(result.unlinked)

    for name, document in zip(_unique_names(documents), documents):
        source, detected_by, confidence = document.source_type, None, None
        if source is None:
            detected = detect(document.data, document.name)
            source, detected_by, confidence = (detected.source_type, detected.method,
                                               detected.confidence)
        add(name, source, extract(document.data, document.name, source), detected_by, confidence)
    for link in links:
        for repository in read_link(link):
            add(repository.name, repository.source, repository.extraction, "github")
    return summaries, found, unlinked


def build_profile(documents: list[SubmittedDocument],
                  extract: Extractor = extract_from_document,
                  links: Sequence[str] = (),
                  read_link: LinkReader = _read_github,
                  detect: TypeDetector = _detect_type) -> SkillProfile:
    """Read every document and portfolio link, then fuse each skill's evidence across them."""
    summaries, found, unlinked = _read_all(documents, extract, links, read_link, detect)
    return SkillProfile(documents=summaries, skills=fuse_skills(found), unlinked=unlinked)


def profile_evidence(documents: list[SubmittedDocument],
                     extract: Extractor = extract_from_document) -> dict[str, list[Evidence]]:
    """Skill ID -> its evidence from all documents, unfused (for the sensitivity analysis)."""
    _, found, _ = _read_all(documents, extract)
    evidence: dict[str, list[Evidence]] = {}
    for name, source, m in found:
        evidence.setdefault(m.skill_id, []).append(
            Evidence(name, source, m.evidence_type, m.match_score))
    return evidence
