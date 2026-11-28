import uuid
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    ADMIN_ROLES,
    CANDIDATE_QUEUE_ROLES,
    CANDIDATE_SUBMIT_ROLES,
    get_candidate_service,
    require_reviewer,
    require_roles,
)
from app.core.security import Principal
from app.schemas.candidates import (
    CandidateEntityCreate,
    CandidateEntityOut,
    CandidateEntityReview,
    CandidateEntityType,
    CandidateMergeAsAliasRequest,
    CandidateMergeAsAliasResponse,
    CandidateReviewStatus,
)
from app.services.candidates import CandidateService

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post(
    "/entities",
    response_model=CandidateEntityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit candidate entity",
)
async def submit_candidate_entity(
    data: CandidateEntityCreate,
    service: CandidateService = Depends(get_candidate_service),
    _=Depends(require_roles(*CANDIDATE_SUBMIT_ROLES)),
):
    return await service.create_candidate(data)


@router.get(
    "/entities",
    response_model=list[CandidateEntityOut],
    summary="List candidate entities",
)
async def list_candidate_entities(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    entity_type: CandidateEntityType | None = None,
    review_status: CandidateReviewStatus | None = None,
    service: CandidateService = Depends(get_candidate_service),
    _=Depends(require_roles(*CANDIDATE_QUEUE_ROLES)),
):
    return await service.list_candidates(
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        review_status=review_status,
    )


@router.get(
    "/entities/{candidate_entity_id}",
    response_model=CandidateEntityOut,
    summary="Get candidate entity by ID",
)
async def get_candidate_entity(
    candidate_entity_id: uuid.UUID,
    service: CandidateService = Depends(get_candidate_service),
    _=Depends(require_roles(*CANDIDATE_QUEUE_ROLES)),
):
    return await service.get_candidate(candidate_entity_id)


@router.patch(
    "/entities/{candidate_entity_id}/review",
    response_model=CandidateEntityOut,
    summary="Review candidate entity (approve or reject)",
)
async def review_candidate_entity(
    candidate_entity_id: uuid.UUID,
    review_data: CandidateEntityReview,
    service: CandidateService = Depends(get_candidate_service),
    reviewer: Principal = Depends(require_reviewer),
):
    return await service.review_candidate(
        candidate_entity_id,
        review_data,
        reviewer_id=reviewer.user_id,
    )


@router.post(
    "/entities/{candidate_entity_id}/merge-as-alias",
    response_model=CandidateMergeAsAliasResponse,
    summary="Merge a candidate into an existing canonical concept as an alias",
)
async def merge_candidate_as_alias(
    candidate_entity_id: uuid.UUID,
    data: CandidateMergeAsAliasRequest,
    service: CandidateService = Depends(get_candidate_service),
    admin: Principal = Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.merge_candidate_as_alias(
        candidate_entity_id,
        data,
        reviewer_id=admin.user_id,
    )
