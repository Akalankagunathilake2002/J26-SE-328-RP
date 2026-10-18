"""Database models for Readiness Engine."""

from app.db.base import Base
from app.models.analysis import (
    Analysis,
    AnalysisPrioritySkill,
    AnalysisReport,
    AnalysisSkillResult,
    AnalysisStatus,
    CandidateDiscoveryRun,
)
from app.models.cache import (
    CachedAlias,
    CachedRelationship,
    CachedSkill,
    CachedSkillEmbedding,
    KnowledgeSnapshot,
)
from app.models.profiles import (
    IndustryProfile,
    IndustryProfileRequirement,
    IndustrySkillEvidence,
    SkillEvidence,
    UserSkillProfile,
    UserSkillProfileSkill,
)

# Backward-compatibility aliases
StudentProfile = UserSkillProfile
StudentProfileSkill = UserSkillProfileSkill

__all__ = [
    "Analysis",
    "AnalysisPrioritySkill",
    "AnalysisReport",
    "AnalysisSkillResult",
    "AnalysisStatus",
    "Base",
    "CachedAlias",
    "CachedRelationship",
    "CachedSkill",
    "CachedSkillEmbedding",
    "CandidateDiscoveryRun",
    "IndustryProfile",
    "IndustryProfileRequirement",
    "IndustrySkillEvidence",
    "KnowledgeSnapshot",
    "SkillEvidence",
    "StudentProfile",
    "StudentProfileSkill",
    "UserSkillProfile",
    "UserSkillProfileSkill",
]
