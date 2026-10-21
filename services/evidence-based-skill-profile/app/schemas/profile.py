from pydantic import BaseModel, Field

from app.schemas.evidence import SourceType
from app.schemas.extraction import (
    ConfidenceLevel, EvidenceContribution, SectionType, SkillMention, UnlinkedSpan,
)


class ProfileDocument(BaseModel):
    """One submitted document and what was found in it."""

    name: str
    source_type: SourceType
    type_detected_by: str | None = Field(
        None, description="How the type was detected: structure, meaning, or github")
    type_confidence: float | None = None
    sections: list[SectionType]
    skill_count: int


class ProfileSkill(BaseModel):
    """One skill with the evidence from every document fused into one confidence (TAF tasks 2, 7)."""

    skill_id: str
    name: str
    confidence: float
    confidence_level: ConfidenceLevel
    evidence: list[EvidenceContribution]
    documents: list[str] = Field(description="Documents that mention the skill")
    source_types: list[SourceType]
    mentions: list[SkillMention]


class StudentProfile(BaseModel):
    """A student's skill profile built from all their documents (before student verification)."""

    documents: list[ProfileDocument]
    skills: list[ProfileSkill]
    unlinked: list[UnlinkedSpan] = Field(default_factory=list,
                                         description="Skill-like phrases without a skill ID")
