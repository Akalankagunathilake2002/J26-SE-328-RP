from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_core_service,
    require_admin,
    require_authenticated_user,
)
from app.schemas.core import EntityStatus, SkillCreate, SkillNature, SkillOut, SkillType, SkillUpdate
from app.services.core import CoreService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/", response_model=list[SkillOut])
async def list_skills(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: EntityStatus | None = None,
    skill_type: SkillType | None = None,
    skill_nature: SkillNature | None = None,
    domain_id: str | None = None,
    search: str | None = None,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_skills(
        limit=limit,
        offset=offset,
        status=status,
        skill_type=skill_type,
        skill_nature=skill_nature,
        domain_id=domain_id,
        search=search,
    )


@router.get("/{skill_id}", response_model=SkillOut)
async def get_skill(
    skill_id: str,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_authenticated_user),
):
    return await service.get_skill(skill_id)


@router.post("/", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_admin),
):
    return await service.create_skill(data)


@router.patch("/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_admin),
):
    return await service.update_skill(skill_id, data)


@router.post("/{skill_id}/retire", response_model=SkillOut)
async def retire_skill(
    skill_id: str,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_admin),
):
    return await service.retire_skill(skill_id)
