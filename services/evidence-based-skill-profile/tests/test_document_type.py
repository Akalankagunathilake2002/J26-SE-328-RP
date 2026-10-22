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
    assert found.source_type == SourceType.CERTIFICATE and found.method == "wording"


def test_certificates_are_recognised_by_their_standard_wording():
    mongodb = ("Proof of Completion\nCongratulations to\nAkalanka Gunathilake\nFor successfully "
               "completing\nMongoDB Atlas Administrator Path\nOn 10-26-2025\nMongoDB, Inc")
    event = "This Certificate is Proudly Awarded to K.R. Perera for the participation of the event"
    for text in (mongodb, event):
        found = DETECTOR.detect(text)
        assert (found.source_type, found.method) == (SourceType.CERTIFICATE, "wording")


def test_a_certificate_whose_wording_is_an_image_is_recognised_by_its_layout():
    # Only the filled-in fields are text; "Proof of Completion" is part of the background image.
    mongodb = "Akalanka Gunathilake\nMongoDB Atlas Administrator Path\n10-26-2025\nMDBh0u7fznzum"
    found = DETECTOR.detect(mongodb)
    assert (found.source_type, found.method) == (SourceType.CERTIFICATE, "layout")
    assert DETECTOR.detect("Jane Perera\nPython for Everybody\nMarch 3, 2025").method == "layout"
    # Little text without a date is not enough.
    assert DETECTOR.detect("Project report\nA booking system").method == "meaning"


def test_one_weak_phrase_or_a_long_document_is_not_enough():
    report = "Project report. We successfully completed the system design and testing."
    assert DETECTOR.detect(report).method == "meaning"
    long_report = "This is to certify that the project is my own work. " + "Design. " * 300
    assert DETECTOR.detect(long_report).method == "meaning"


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
