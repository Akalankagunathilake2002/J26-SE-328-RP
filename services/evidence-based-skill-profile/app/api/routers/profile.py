import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.routers.extraction import MAX_UPLOAD_BYTES
from app.collection.github import GitHubError
from app.extraction.reader import DocumentError
from app.profile.builder import (
    LinkReader, SubmittedDocument, TypeDetector, build_profile, default_link_reader,
    default_type_detector,
)
from app.profile.store import STORE_ERRORS, ProfileStore, default_profile_store
from app.schemas.profile import SkillProfile

MAX_DOCUMENTS = 10
MAX_LINKS = 3

router = APIRouter(tags=["profile"])
logger = logging.getLogger(__name__)


def _split(values: list[str]) -> list[str]:
    """Form lists may arrive as separate values or as one comma-separated value (Swagger UI)."""
    return [part.strip() for value in values for part in value.split(",") if part.strip()]


@router.post("/build", response_model=SkillProfile)
async def build_skill_profile(
    files: list[UploadFile] = File(
        default=[], description="PDF, DOCX or TXT documents: CV, certificates, project or "
                                "internship reports, transcripts. Each file's type is detected "
                                "from its content."),
    portfolio_links: list[str] = Form(
        default=[], description="GitHub user or repository links (comma-separated is fine)"),
    user_id: str | None = Form(
        default=None, description="The logged-in user's ID; the profile is saved for them"),
    store: ProfileStore = Depends(default_profile_store),
    read_link: LinkReader = Depends(default_link_reader),
    detect: TypeDetector = Depends(default_type_detector),
) -> SkillProfile:
    """Build one skill profile from documents and GitHub links, fusing each skill's evidence.

    With a user_id the profile is also saved, replacing the user's previous one.
    """
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
        profile = await run_in_threadpool(build_profile, documents, links=portfolio_links,
                                          read_link=read_link, detect=detect)
    except (DocumentError, GitHubError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    if user_id and user_id.strip():
        try:
            profile.saved_at = await store.save(user_id.strip(), profile)
        except STORE_ERRORS:
            # The user still gets the profile; saved_at stays empty so the website can say so.
            logger.exception("Could not save the profile for %s", user_id)
    return profile


@router.get("/users/{user_id}", response_model=SkillProfile)
async def get_saved_profile(
    user_id: str, store: ProfileStore = Depends(default_profile_store),
) -> SkillProfile:
    """The user's last saved profile (shown again after a refresh or a new login)."""
    try:
        profile = await store.load(user_id)
    except STORE_ERRORS as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Saved profiles are unavailable right now") from error
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No saved profile yet")
    return profile


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_saved_profile(
    user_id: str, store: ProfileStore = Depends(default_profile_store),
) -> None:
    """Delete the user's saved profile, so they can start again (clearing twice is fine)."""
    try:
        await store.delete(user_id)
    except STORE_ERRORS as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Saved profiles are unavailable right now") from error
