from enum import StrEnum


class SourceType(StrEnum):
    """What the student submitted (TAF task 2)."""

    CV = "cv"
    PROJECT_DESCRIPTION = "project_description"
    ACADEMIC_DOCUMENT = "academic_document"
    CERTIFICATE = "certificate"
    PORTFOLIO_LINK = "portfolio_link"


class EvidenceType(StrEnum):
    """How a skill is supported by the evidence (TAF tasks 1 and 6)."""

    PROJECT_DEMONSTRATED = "project_demonstrated"
    CV_SELF_REPORTED = "cv_self_reported"
    ACADEMIC_EXPOSURE = "academic_exposure"
    CERTIFICATE_SUPPORTED = "certificate_supported"
    PORTFOLIO_SUPPORTED = "portfolio_supported"
    UNVERIFIED_MENTION = "unverified_mention"
