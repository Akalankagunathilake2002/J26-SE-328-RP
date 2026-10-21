"""Rule-based evidence context classification, v1 (TAF task 6).

Decides how strongly one mention supports a skill, from what was uploaded (source), the CV section
and the words in the sentence. v2 replaces this with a trained classifier and is compared with it.
"""
import re

from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.extraction import SectionType

# The student did something with the skill: "Built", "developed", "Configuring", "Led" ...
ACTION_VERB = re.compile(
    r"\b(?:built|build|develop|design|implement|creat|deploy|configur|install|automat|migrat|"
    r"program|coded|coding|engineer|maintain|manag|administ|test|debug|integrat|optimi[sz]|"
    r"analy[sz]|led|lead|train|conduct|prepar|utili[sz]|used|using|operat|support|wrote|writ|"
    r"deliver|launch|establish|coordinat|organi[sz]|recruit|negotiat|resolv|troubleshoot|"
    r"monitor|perform|execut|plann|research|present|facilitat|supervis|mentor|upgrad|"
    r"improv|reduc|increas|achiev|completed)\w*",
    re.IGNORECASE,
)
# The skill is only wished for or barely known: "interested in learning Kubernetes".
WEAK_PHRASE = re.compile(
    r"\b(?:interested in|interest in|keen to|eager to|willing to|want to|hope to|plan to|"
    r"currently learning|learning to|familiar with|familiarity with|basic knowledge|"
    r"exposure to|beginner|introduction to)\b",
    re.IGNORECASE,
)

SOURCE_DEFAULT = {
    SourceType.CERTIFICATE: EvidenceType.CERTIFICATE_SUPPORTED,
    SourceType.PORTFOLIO_LINK: EvidenceType.PORTFOLIO_SUPPORTED,
    SourceType.ACADEMIC_DOCUMENT: EvidenceType.ACADEMIC_EXPOSURE,
    SourceType.PROJECT_DESCRIPTION: EvidenceType.PROJECT_DEMONSTRATED,
}
SECTION_DEFAULT = {
    SectionType.SKILLS: EvidenceType.CV_SELF_REPORTED,
    SectionType.SUMMARY: EvidenceType.CV_SELF_REPORTED,
    SectionType.EDUCATION: EvidenceType.ACADEMIC_EXPOSURE,
    SectionType.CERTIFICATIONS: EvidenceType.CERTIFICATE_SUPPORTED,
}
WORK_SECTIONS = {SectionType.EXPERIENCE, SectionType.PROJECTS, SectionType.ACCOMPLISHMENTS}


def classify_evidence(source: SourceType, section: SectionType, sentence: str) -> EvidenceType:
    if WEAK_PHRASE.search(sentence):
        return EvidenceType.UNVERIFIED_MENTION
    if source in SOURCE_DEFAULT:
        return SOURCE_DEFAULT[source]
    if section in WORK_SECTIONS:
        if ACTION_VERB.search(sentence):
            return EvidenceType.PROJECT_DEMONSTRATED
        return EvidenceType.CV_SELF_REPORTED
    return SECTION_DEFAULT.get(section, EvidenceType.UNVERIFIED_MENTION)
