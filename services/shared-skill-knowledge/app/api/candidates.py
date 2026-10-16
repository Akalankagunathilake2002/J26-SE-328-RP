from fastapi import APIRouter, Depends, Query, status
from app.schemas.candidates import (
    CandidateEntityCreate,
    CandidateEntityReview,
    CandidateEntityOut,
    CandidateEntityType,
    CandidateReviewStatus,
)
from app.services.candidates import CandidateService
from app.api.dependencies import get_candidate_service, verify_reviewer

candidates_router = APIRouter(prefix="/candidates", tags=["candidates"])

@candidates_router.post(
    "/entities",
    response_model=CandidateEntityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit candidate entity",
)
async def submit_candidate_entity(
    data: CandidateEntityCreate,
    service: CandidateService = Depends(get_candidate_service),
):
    return await service.create_candidate(data)

@candidates_router.get(
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
):
    return await service.list_candidates(
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        review_status=review_status,
    )

@candidates_router.get(
    "/entities/{candidate_entity_id}",
    response_model=CandidateEntityOut,
    summary="Get candidate entity by ID",
)
async def get_candidate_entity(
    candidate_entity_id: str,
    service: CandidateService = Depends(get_candidate_service),
):
    return await service.get_candidate(candidate_entity_id)

@candidates_router.patch(
    "/entities/{candidate_entity_id}/review",
    response_model=CandidateEntityOut,
    summary="Review candidate entity (approve or reject)",
)
async def review_candidate_entity(
    candidate_entity_id: str,
    review_data: CandidateEntityReview,
    service: CandidateService = Depends(get_candidate_service),
    reviewer_id: str = Depends(verify_reviewer),
):
    return await service.review_candidate(candidate_entity_id, review_data)
