from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.extraction.pipeline import extract_from_document
from app.extraction.reader import DocumentError
from app.profile.builder import TypeDetector, default_type_detector
from app.schemas.extraction import DocumentExtraction

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

router = APIRouter(tags=["extraction"])


def _extract(data: bytes, filename: str, detect: TypeDetector) -> DocumentExtraction:
    return extract_from_document(data, filename, detect(data, filename).source_type)


@router.post("/extract", response_model=DocumentExtraction)
async def extract_document(
    file: UploadFile = File(..., description="PDF, DOCX or TXT document"),
    detect: TypeDetector = Depends(default_type_detector),
) -> DocumentExtraction:
    """Find the skills in one document, with the evidence and confidence for each skill.

    The document type is detected from its content, never taken from the student."""
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File is larger than 10 MB")
    try:
        return await run_in_threadpool(_extract, data, file.filename or "", detect)
    except DocumentError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
