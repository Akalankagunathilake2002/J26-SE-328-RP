from enum import StrEnum

from pydantic import BaseModel

from app.schemas.evidence import EvidenceType, SourceType


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
    method: str
    evidence_type: EvidenceType


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
