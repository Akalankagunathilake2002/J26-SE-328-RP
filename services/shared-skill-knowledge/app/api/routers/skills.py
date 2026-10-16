from fastapi import APIRouter, Depends, Query
from app.schemas.core import SkillOut, SkillCreate, SkillType, SkillNature
from app.services.core import CoreService
from app.api.dependencies import get_core_service

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("/", response_model=list[SkillOut])
async def list_skills(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    skill_type: SkillType | None = None,
    skill_nature: SkillNature | None = None,
    domain_id: str | None = None,
    service: CoreService = Depends(get_core_service),
):
    return await service.list_skills(
        limit=limit, offset=offset, status=status,
        skill_type=skill_type, skill_nature=skill_nature, domain_id=domain_id,
    )

@router.get("/{skill_id}", response_model=SkillOut)
async def get_skill(skill_id: str, service: CoreService = Depends(get_core_service)):
    return await service.get_skill(skill_id)

@router.post("/", response_model=SkillOut)
async def create_skill(data: SkillCreate, service: CoreService = Depends(get_core_service)):
    return await service.create_skill(data)
