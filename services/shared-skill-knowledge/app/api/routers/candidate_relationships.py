from fastapi import APIRouter, Depends, Query, status
from app.schemas.relationships import (
    CandidateRelationshipCreate,
    CandidateRelationshipReview,
    CandidateRelationshipOut,
    SkillRelationshipType,
    CandidateRelationshipReviewStatus,
)
from app.services.relationships import CandidateRelationshipService
from app.api.dependencies import get_candidate_relationship_service, verify_reviewer

router = APIRouter(prefix="/candidates/relationships", tags=["candidate-relationships"])


@router.post(
    "",
    response_model=CandidateRelationshipOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a proposed skill relationship",
)
async def submit_candidate_relationship(
    data: CandidateRelationshipCreate,
    service: CandidateRelationshipService = Depends(get_candidate_relationship_service),
):
    return await service.submit_candidate(data)


@router.get(
    "",
    response_model=list[CandidateRelationshipOut],
    summary="List candidate skill relationships with pagination and filters",
)
async def list_candidate_relationships(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source_skill_id: str | None = None,
    target_skill_id: str | None = None,
    proposed_relationship_type: SkillRelationshipType | None = Query(None, alias="relationship_type"),
    review_status: CandidateRelationshipReviewStatus | None = None,
    service: CandidateRelationshipService = Depends(get_candidate_relationship_service),
):
    return await service.list_candidates(
        limit=limit,
        offset=offset,
        source_skill_id=source_skill_id,
        target_skill_id=target_skill_id,
        proposed_relationship_type=proposed_relationship_type,
        review_status=review_status,
    )


@router.get(
    "/{candidate_relationship_id}",
    response_model=CandidateRelationshipOut,
    summary="Get a candidate skill relationship by ID",
)
async def get_candidate_relationship(
    candidate_relationship_id: str,
    service: CandidateRelationshipService = Depends(get_candidate_relationship_service),
):
    return await service.get_candidate(candidate_relationship_id)


@router.patch(
    "/{candidate_relationship_id}/review",
    response_model=CandidateRelationshipOut,
    summary="Review candidate skill relationship (approve or reject)",
)
async def review_candidate_relationship(
    candidate_relationship_id: str,
    review_data: CandidateRelationshipReview,
    service: CandidateRelationshipService = Depends(get_candidate_relationship_service),
    reviewer_id: str = Depends(verify_reviewer),
):
    return await service.review_candidate(candidate_relationship_id, review_data)
