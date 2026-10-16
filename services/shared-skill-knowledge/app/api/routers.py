from fastapi import APIRouter, Depends, Query
from typing import Sequence
from app.schemas.core import DomainOut, DomainCreate, SkillOut, SkillCreate, RoleOut, RoleCreate, SkillType, SkillNature
from app.services.core import CoreService
from app.api.dependencies import get_core_service

domains_router = APIRouter(prefix="/domains", tags=["domains"])
skills_router = APIRouter(prefix="/skills", tags=["skills"])
roles_router = APIRouter(prefix="/roles", tags=["roles"])

@domains_router.get("/", response_model=list[DomainOut])
async def list_domains(service: CoreService = Depends(get_core_service)):
    return await service.list_domains()

@domains_router.post("/", response_model=DomainOut)
async def create_domain(data: DomainCreate, service: CoreService = Depends(get_core_service)):
    return await service.create_domain(data)

@skills_router.get("/", response_model=list[SkillOut])
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

@skills_router.get("/{skill_id}", response_model=SkillOut)
async def get_skill(skill_id: str, service: CoreService = Depends(get_core_service)):
    return await service.get_skill(skill_id)

@skills_router.post("/", response_model=SkillOut)
async def create_skill(data: SkillCreate, service: CoreService = Depends(get_core_service)):
    return await service.create_skill(data)

@roles_router.get("/", response_model=list[RoleOut])
async def list_roles(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    domain_id: str | None = None,
    service: CoreService = Depends(get_core_service),
):
    return await service.list_roles(limit=limit, offset=offset, status=status, domain_id=domain_id)

@roles_router.get("/{role_id}", response_model=RoleOut)
async def get_role(role_id: str, service: CoreService = Depends(get_core_service)):
    return await service.get_role(role_id)

@roles_router.post("/", response_model=RoleOut)
async def create_role(data: RoleCreate, service: CoreService = Depends(get_core_service)):
    return await service.create_role(data)
