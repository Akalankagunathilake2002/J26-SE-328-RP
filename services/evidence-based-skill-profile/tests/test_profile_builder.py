import pytest
from httpx import AsyncClient

from app.profile.builder import SubmittedDocument, build_profile
from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.extraction import DocumentExtraction, SectionType, SkillMention

CV, REPORT, CERTIFICATE = SourceType.CV, SourceType.PROJECT_DESCRIPTION, SourceType.CERTIFICATE


def _mention(skill_id: str, evidence_type: EvidenceType, score: float = 1.0) -> SkillMention:
    return SkillMention(skill_id=skill_id, name=skill_id.title(), matched_text=skill_id, start=0,
                        end=1, section=SectionType.SKILLS, sentence="", method="dictionary",
                        match_score=score, evidence_type=evidence_type)


FOUND = {
    "cv.txt": [_mention("python", EvidenceType.CV_SELF_REPORTED),
               _mention("java", EvidenceType.CV_SELF_REPORTED)],
    "report.txt": [_mention("python", EvidenceType.PROJECT_DEMONSTRATED)],
    "cert.txt": [_mention("python", EvidenceType.CERTIFICATE_SUPPORTED)],
}


def fake_extract(data: bytes, name: str, source: SourceType) -> DocumentExtraction:
    return DocumentExtraction(source_type=source, sections=[SectionType.SKILLS],
                              mentions=FOUND[name], skills=[])


def _profile(*documents: tuple[str, SourceType]):
    return build_profile([SubmittedDocument(n, b"", s) for n, s in documents], fake_extract)


def test_evidence_from_several_documents_is_fused():
    cv_only = _profile(("cv.txt", CV))
    full = _profile(("cv.txt", CV), ("report.txt", REPORT), ("cert.txt", CERTIFICATE))

    python_cv = next(s for s in cv_only.skills if s.skill_id == "python")
    python = next(s for s in full.skills if s.skill_id == "python")
    assert python_cv.confidence_level == "weak"
    assert python.confidence_level == "strong"
    assert python.documents == ["cv.txt", "report.txt", "cert.txt"]
    assert python.source_types == [CV, REPORT, CERTIFICATE]
    assert len(python.evidence) == 3 and len(python.mentions) == 3
    # Java has only the CV claim, so it is unchanged and ranked below Python.
    assert [s.skill_id for s in full.skills] == ["python", "java"]
    assert full.skills[1].confidence == next(
        s for s in cv_only.skills if s.skill_id == "java").confidence


def test_documents_are_summarised_and_repeated_names_kept_apart():
    profile = _profile(("cv.txt", CV), ("cv.txt", CV))
    assert [d.name for d in profile.documents] == ["cv.txt", "cv.txt (2)"]
    assert [d.skill_count for d in profile.documents] == [2, 2]  # python, java
    python = next(s for s in profile.skills if s.skill_id == "python")
    # Two separate CVs are two pieces of evidence (no repeat decay across documents).
    assert python.confidence > _profile(("cv.txt", CV)).skills[0].confidence


@pytest.mark.anyio
async def test_build_endpoint_detects_each_documents_type(client: AsyncClient):
    files = [("files", ("cv.txt", b"Skills\nPython, Java\n", "text/plain")),
             ("files", ("cert.txt", b"Python certificate", "text/plain"))]
    # A type sent by the student is ignored: it must not be able to fake strong evidence.
    response = await client.post("/api/v1/profile/build", files=files,
                                 data={"source_types": ["certificate", "certificate"]})
    assert response.status_code == 200
    body = response.json()
    assert [(d["source_type"], d["type_detected_by"]) for d in body["documents"]] == [
        ("cv", "structure"), ("certificate", "meaning")]
    python = next(s for s in body["skills"] if s["name"] == "Python")
    assert python["source_types"] == ["cv", "certificate"]


def test_given_types_are_used_only_internally_and_detection_fills_the_rest():
    detected = []

    def detect(data, name):
        detected.append(name)
        from app.collection.document_type import DetectedType
        return DetectedType(CERTIFICATE, 0.8, "meaning")

    profile = build_profile([SubmittedDocument("cv.txt", b"", CV), SubmittedDocument("cert.txt", b"")],
                            fake_extract, detect=detect)
    assert detected == ["cert.txt"]
    assert [(d.source_type, d.type_detected_by) for d in profile.documents] == [
        (CV, None), (CERTIFICATE, "meaning")]
