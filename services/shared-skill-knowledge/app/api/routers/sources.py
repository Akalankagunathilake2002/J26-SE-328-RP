import uuid
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_source_service, require_authenticated_user
from app.schemas.sources import KnowledgeSourceOut, RoleExternalIdOut, SkillExternalIdOut
from app.services.sources import SourceService

router = APIRouter(tags=["sources", "external-ids"])


@router.get("/sources", response_model=list[KnowledgeSourceOut])
async def list_knowledge_sources(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    service: SourceService = Depends(get_source_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_sources(limit=limit, offset=offset, search=search)


@router.get("/sources/{source_id}", response_model=KnowledgeSourceOut)
async def get_knowledge_source(
    source_id: uuid.UUID,
    service: SourceService = Depends(get_source_service),
    _=Depends(require_authenticated_user),
):
    return await service.get_source(source_id)


@router.get("/skills/{skill_id}/external-ids", response_model=list[SkillExternalIdOut])
async def list_external_ids_for_skill(
    skill_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source_id: uuid.UUID | None = None,
    service: SourceService = Depends(get_source_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_skill_external_ids(
        limit=limit, offset=offset, skill_id=skill_id, source_id=source_id
    )


@router.get("/roles/{role_id}/external-ids", response_model=list[RoleExternalIdOut])
async def list_external_ids_for_role(
    role_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source_id: uuid.UUID | None = None,
    service: SourceService = Depends(get_source_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_role_external_ids(
        limit=limit, offset=offset, role_id=role_id, source_id=source_id
    )


@router.get("/external-ids/skills", response_model=list[SkillExternalIdOut])
async def list_skill_external_ids(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    skill_id: str | None = None,
    source_id: uuid.UUID | None = None,
    service: SourceService = Depends(get_source_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_skill_external_ids(
        limit=limit, offset=offset, skill_id=skill_id, source_id=source_id
    )


@router.get("/external-ids/roles", response_model=list[RoleExternalIdOut])
async def list_role_external_ids(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    role_id: str | None = None,
    source_id: uuid.UUID | None = None,
    service: SourceService = Depends(get_source_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_role_external_ids(
        limit=limit, offset=offset, role_id=role_id, source_id=source_id
    )
