from fastapi import APIRouter, Depends, Query, status
from app.schemas.relationships import (
    SkillRelationshipCreate,
    SkillRelationshipUpdate,
    SkillRelationshipOut,
    SkillRelationshipType,
)
from app.services.relationships import RelationshipService
from app.api.dependencies import get_relationship_service

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.post(
    "",
    response_model=SkillRelationshipOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a verified skill relationship",
)
async def create_relationship(
    data: SkillRelationshipCreate,
    service: RelationshipService = Depends(get_relationship_service),
):
    return await service.create_relationship(data)


@router.get(
    "",
    response_model=list[SkillRelationshipOut],
    summary="List skill relationships with pagination and filters",
)
async def list_relationships(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source_skill_id: str | None = None,
    target_skill_id: str | None = None,
    relationship_type: SkillRelationshipType | None = None,
    verification_status: str | None = None,
    search: str | None = None,
    service: RelationshipService = Depends(get_relationship_service),
):
    return await service.list_relationships(
        limit=limit,
        offset=offset,
        source_skill_id=source_skill_id,
        target_skill_id=target_skill_id,
        relationship_type=relationship_type,
        verification_status=verification_status,
        search=search,
    )


@router.get(
    "/{relationship_id}",
    response_model=SkillRelationshipOut,
    summary="Get a skill relationship by ID",
)
async def get_relationship(
    relationship_id: str,
    service: RelationshipService = Depends(get_relationship_service),
):
    return await service.get_relationship(relationship_id)


@router.patch(
    "/{relationship_id}",
    response_model=SkillRelationshipOut,
    summary="Update permitted fields of a skill relationship",
)
async def update_relationship(
    relationship_id: str,
    data: SkillRelationshipUpdate,
    service: RelationshipService = Depends(get_relationship_service),
):
    return await service.update_relationship(relationship_id, data)


@router.delete(
    "/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a skill relationship",
)
async def delete_relationship(
    relationship_id: str,
    service: RelationshipService = Depends(get_relationship_service),
):
    await service.delete_relationship(relationship_id)
