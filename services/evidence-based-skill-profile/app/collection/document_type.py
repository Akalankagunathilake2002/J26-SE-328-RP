"""Detect what kind of document a student uploaded (TAF task 2).

The type decides how strong the document's evidence is (a certificate file is among the strongest
kinds), so it is never taken from the student: a CV uploaded as "certificate" would otherwise get
the strongest weight. The service detects it from the content, in four steps:

1. Structure: a document with at least CV_MIN_SECTIONS standard CV sections (skills, experience,
   education, summary, projects, certifications) is a CV.
2. Wording: a short document (at most CERTIFICATE_MAX_WORDS words) that uses the standard wording
   of certificates ("Certificate of Completion", "Proof of Completion", "This is to certify",
   "awarded to", "Credential ID") is a certificate. One strong phrase is enough; weaker ones
   ("congratulations", "successfully completed", "in recognition of") are needed twice. Found in
   testing: an event certificate ("This Certificate is Proudly Awarded to ...").
3. Layout: a document with almost no text (at most SPARSE_MAX_WORDS words) that contains a date is
   a certificate. Online platforms print the wording as part of a background image, so the PDF
   text is only the name, the course, the date and an ID. Found in testing: a MongoDB "Proof of
   Completion" certificate gave only "Akalanka Gunathilake / MongoDB Atlas Administrator Path /
   10-26-2025 / MDBh0u7fznzum" and was judged a project report by meaning. Reports and transcripts
   always have much more text.
4. Meaning (zero-shot): otherwise the opening of the document is embedded with the same sentence-
   transformer as the skill index and compared with short descriptions of a certificate, a project
   report and an academic document; the closest type wins. No training data is needed. A CV is
   only recognised by its structure: in testing, a short project report was otherwise judged
   slightly closer to "CV" than to "project report".

Portfolio evidence comes only from GitHub links, which can be checked; an uploaded work sample is
a project description. Detection says what kind of document it is, not whether it is genuine:
checking certificates with their issuer is future work.
"""
import re
from dataclasses import dataclass
from functools import lru_cache


from app.extraction.cleaner import clean_text
from app.extraction.sections import split_sections
from app.schemas.evidence import SourceType
from app.schemas.extraction import SectionType
from app.semantic.encoder import Encoder

CV_SECTIONS = {SectionType.SKILLS, SectionType.EXPERIENCE, SectionType.EDUCATION,
               SectionType.SUMMARY, SectionType.PROJECTS, SectionType.CERTIFICATIONS}
CV_MIN_SECTIONS = 2
OPENING_WORDS = 200
# Certificates are one page; reports and transcripts that quote "certified" are longer.
CERTIFICATE_MAX_WORDS = 250
CERTIFICATE_STRONG = re.compile(
    r"\bcertificate of (?:completion|achievement|participation|appreciation|attendance|"
    r"excellence|merit|recognition|accomplishment)\b|\bproof of completion\b|"
    r"\bthis is to certify\b|\bhereby certif(?:y|ies)\b|\bcertif(?:y|ies) that\b|"
    r"\b(?:awarded|presented|issued) to\b|\bcredential (?:id|url)\b|\bcertificate (?:id|no)\b",
    re.IGNORECASE)
CERTIFICATE_WEAK = re.compile(
    r"\bcongratulations\b|\bsuccessfully (?:completed|completing|passed)\b|"
    r"\bhas (?:completed|passed|participated)\b|\bin recognition of\b|\bcertificate\b|"
    r"\bfor (?:participating|participation|completing)\b",
    re.IGNORECASE)
SPARSE_MAX_WORDS = 40
DATE = re.compile(
    r"\b\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|"
    r"dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|"
    r"mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*,?\s+\d{4}\b",
    re.IGNORECASE)

DESCRIPTIONS: dict[SourceType, list[str]] = {
    SourceType.CERTIFICATE: [
        "A certificate stating that a person has successfully completed a course or passed an "
        "exam.",
        "Certificate of completion or professional certification awarded to a named person, "
        "with an issuer and a date.",
    ],
    SourceType.PROJECT_DESCRIPTION: [
        "A project report describing how a software system or business project was designed, "
        "implemented and tested.",
        "Project documentation or internship report explaining the work done, the methods used "
        "and the results.",
        "Final year project report for a degree: abstract, system design, implementation, "
        "testing and conclusion of the system the student built.",
    ],
    SourceType.ACADEMIC_DOCUMENT: [
        "An academic transcript listing university modules, credits, grades and the GPA.",
        "A course syllabus or module outline describing learning outcomes, topics and "
        "assessments.",
    ],
}


@dataclass(frozen=True)
class DetectedType:
    source_type: SourceType
    confidence: float          # cosine similarity of the chosen type, or 1.0 for the CV rule
    method: str                # "structure", "wording", "layout" or "meaning"


class DocumentTypeDetector:
    def __init__(self, encoder: Encoder):
        self.encoder = encoder
        self.types = list(DESCRIPTIONS)
        vectors = encoder.encode([d for t in self.types for d in DESCRIPTIONS[t]])
        self._vectors = vectors
        self._owner = [t for t in self.types for _ in DESCRIPTIONS[t]]

    def detect(self, raw_text: str) -> DetectedType:
        text = clean_text(raw_text)
        cv_sections = {s.type for s in split_sections(text)} & CV_SECTIONS
        if len(cv_sections) >= CV_MIN_SECTIONS:
            return DetectedType(SourceType.CV, 1.0, "structure")
        if _certificate_wording(text):
            return DetectedType(SourceType.CERTIFICATE, 1.0, "wording")
        if len(text.split()) <= SPARSE_MAX_WORDS and DATE.search(text):
            return DetectedType(SourceType.CERTIFICATE, 1.0, "layout")
        opening = " ".join(text.split()[:OPENING_WORDS]) or "empty document"
        scores = self._vectors @ self.encoder.encode([opening])[0]
        best: dict[SourceType, float] = {}
        for owner, score in zip(self._owner, scores):
            best[owner] = max(best.get(owner, -1.0), float(score))
        chosen = max(best, key=best.get)
        return DetectedType(chosen, round(best[chosen], 3), "meaning")


def _certificate_wording(text: str) -> bool:
    if len(text.split()) > CERTIFICATE_MAX_WORDS:
        return False
    return bool(CERTIFICATE_STRONG.search(text)) or len(CERTIFICATE_WEAK.findall(text)) >= 2


@lru_cache
def get_document_type_detector() -> DocumentTypeDetector:
    from app.semantic.encoder import get_encoder

    return DocumentTypeDetector(get_encoder())
