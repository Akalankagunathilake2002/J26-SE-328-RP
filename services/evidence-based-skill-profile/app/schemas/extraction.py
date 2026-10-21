from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.normalisation import MatchMethod


class SectionType(StrEnum):
    """Standard CV section a line belongs to (TAF task 3)."""

    HEADER = "header"
    SUMMARY = "summary"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    ACCOMPLISHMENTS = "accomplishments"
    OTHER = "other"


class Section(BaseModel):
    type: SectionType
    heading: str
    text: str
    start: int


class SkillMention(BaseModel):
    """One place in a document where a skill was found (TAF tasks 4 and 6)."""

    skill_id: str
    name: str
    matched_text: str
    start: int
    end: int
    section: SectionType
    sentence: str
    method: str = Field(description="Extraction layer that found it: dictionary or gliner")
    match_method: MatchMethod = Field(MatchMethod.EXACT,
                                      description="How the text was mapped to the skill ID")
    match_score: float = Field(1.0, description="Detection x mapping certainty, 0-1")
    evidence_type: EvidenceType


class UnlinkedSpan(BaseModel):
    """A skill-like phrase the AI extractor found but no skill ID matched: a new-skill candidate."""

    text: str
    section: SectionType
    sentence: str
    detection_score: float


class ConfidenceLevel(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class EvidenceContribution(BaseModel):
    """What one kind of evidence from one source type adds to a skill's confidence (TAF task 7)."""

    source: SourceType
    evidence_type: EvidenceType
    mentions: int
    strength: float


class DocumentSkill(BaseModel):
    """All mentions of one skill in one document, with the fused confidence."""

    skill_id: str
    name: str
    mention_count: int
    evidence_types: list[EvidenceType]
    sections: list[SectionType]
    confidence: float
    confidence_level: ConfidenceLevel
    evidence: list[EvidenceContribution]


class DocumentExtraction(BaseModel):
    source_type: SourceType
    sections: list[SectionType]
    mentions: list[SkillMention]
    skills: list[DocumentSkill]
    unlinked: list[UnlinkedSpan] = Field(default_factory=list)
