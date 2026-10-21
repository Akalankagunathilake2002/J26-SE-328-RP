from app.collection.document_type import DESCRIPTIONS, DocumentTypeDetector
from app.schemas.evidence import SourceType
from tests.fakes import WordEncoder

DETECTOR = DocumentTypeDetector(WordEncoder())


def test_a_cv_is_recognised_by_its_sections():
    found = DETECTOR.detect("Jane Perera\nSkills\nPython, SQL\nExperience\nBuilt an API.\n")
    assert (found.source_type, found.method, found.confidence) == (SourceType.CV, "structure", 1.0)


def test_one_cv_heading_is_not_enough():
    found = DETECTOR.detect("Certificate\nSkills\nThis certificate states that a person has "
                            "successfully completed a course")
    assert found.source_type == SourceType.CERTIFICATE and found.method == "meaning"


def test_other_documents_are_recognised_by_meaning():
    certificate = "This certificate states that a person has successfully completed a course."
    transcript = "Academic transcript: university modules, credits, grades and the GPA."
    report = "Project report: how the system was designed, implemented and tested."
    assert DETECTOR.detect(certificate).source_type == SourceType.CERTIFICATE
    assert DETECTOR.detect(transcript).source_type == SourceType.ACADEMIC_DOCUMENT
    assert DETECTOR.detect(report).source_type == SourceType.PROJECT_DESCRIPTION


def test_meaning_never_chooses_cv_or_portfolio():
    assert set(DESCRIPTIONS) == {SourceType.CERTIFICATE, SourceType.PROJECT_DESCRIPTION,
                                 SourceType.ACADEMIC_DOCUMENT}
    assert DETECTOR.detect("").source_type in DESCRIPTIONS
