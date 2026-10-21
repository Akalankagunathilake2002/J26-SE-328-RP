from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.routers.extraction import MAX_UPLOAD_BYTES
from app.collection.github import GitHubError
from app.extraction.reader import DocumentError
from app.profile.builder import (
    LinkReader, SubmittedDocument, TypeDetector, build_profile, default_link_reader,
    default_type_detector,
)
from app.schemas.profile import StudentProfile

MAX_DOCUMENTS = 10
MAX_LINKS = 3

router = APIRouter(tags=["profile"])


def _split(values: list[str]) -> list[str]:
    """Form lists may arrive as separate values or as one comma-separated value (Swagger UI)."""
    return [part.strip() for value in values for part in value.split(",") if part.strip()]


@router.post("/build", response_model=StudentProfile)
async def build_student_profile(
    files: list[UploadFile] = File(
        default=[], description="PDF, DOCX or TXT documents: CV, certificates, project or "
                                "internship reports, transcripts. Each file's type is detected "
                                "from its content."),
    portfolio_links: list[str] = Form(
        default=[], description="GitHub user or repository links (comma-separated is fine)"),
    read_link: LinkReader = Depends(default_link_reader),
    detect: TypeDetector = Depends(default_type_detector),
) -> StudentProfile:
    """Build one skill profile from documents and GitHub links, fusing each skill's evidence."""
    portfolio_links = _split(portfolio_links)
    files = [upload for upload in files if upload.filename]
    if not files and not portfolio_links:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            "Give at least one document or portfolio link")
    if len(portfolio_links) > MAX_LINKS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            f"At most {MAX_LINKS} portfolio links")
    if len(files) > MAX_DOCUMENTS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            f"At most {MAX_DOCUMENTS} documents")
    documents = []
    for upload in files:
        data = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE,
                                f"{upload.filename} is larger than 10 MB")
        documents.append(SubmittedDocument(upload.filename or "document", data))
    try:
        return await run_in_threadpool(build_profile, documents, links=portfolio_links,
                                       read_link=read_link, detect=detect)
    except (DocumentError, GitHubError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
