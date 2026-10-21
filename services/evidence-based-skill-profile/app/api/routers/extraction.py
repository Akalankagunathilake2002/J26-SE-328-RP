from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.extraction.pipeline import extract_from_document
from app.extraction.reader import DocumentError
from app.schemas.evidence import SourceType
from app.schemas.extraction import DocumentExtraction

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

router = APIRouter(tags=["extraction"])


@router.post("/extract", response_model=DocumentExtraction)
async def extract_document(
    file: UploadFile = File(..., description="PDF, DOCX or TXT document"),
    source_type: SourceType = Form(SourceType.CV),
) -> DocumentExtraction:
    """Find the skills in one document, with the evidence and confidence for each skill."""
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File is larger than 10 MB")
    try:
        return await run_in_threadpool(
            extract_from_document, data, file.filename or "", source_type,
        )
    except DocumentError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
