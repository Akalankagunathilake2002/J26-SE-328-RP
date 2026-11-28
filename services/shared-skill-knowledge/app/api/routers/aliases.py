import uuid
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import ADMIN_ROLES, READ_ROLES, get_alias_service, require_roles
from app.core.security import Principal
from app.schemas.aliases import (
    AliasCreate,
    AliasUpdate,
    AliasVerificationStatus,
    AliasVerifyRequest,
    RoleAliasOut,
    SkillAliasOut,
)
from app.services.aliases import AliasService

router = APIRouter(tags=["aliases"])


@router.get("/skills/{skill_id}/aliases", response_model=list[SkillAliasOut])
async def list_aliases_for_skill(
    skill_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    verification_status: AliasVerificationStatus | None = None,
    search: str | None = None,
    service: AliasService = Depends(get_alias_service),
    principal: Principal = Depends(require_roles(*READ_ROLES)),
):
    return await service.list_skill_aliases(
        caller_role=principal.role,
        limit=limit,
        offset=offset,
        entity_id=skill_id,
        verification_status=verification_status,
        search=search,
    )


@router.post("/skills/{skill_id}/aliases", response_model=SkillAliasOut, status_code=status.HTTP_201_CREATED)
async def create_skill_alias(
    skill_id: str,
    data: AliasCreate,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.create_skill_alias(skill_id, data)


@router.get("/roles/{role_id}/aliases", response_model=list[RoleAliasOut])
async def list_aliases_for_role(
    role_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    verification_status: AliasVerificationStatus | None = None,
    search: str | None = None,
    service: AliasService = Depends(get_alias_service),
    principal: Principal = Depends(require_roles(*READ_ROLES)),
):
    return await service.list_role_aliases(
        caller_role=principal.role,
        limit=limit,
        offset=offset,
        entity_id=role_id,
        verification_status=verification_status,
        search=search,
    )


@router.post("/roles/{role_id}/aliases", response_model=RoleAliasOut, status_code=status.HTTP_201_CREATED)
async def create_role_alias(
    role_id: str,
    data: AliasCreate,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.create_role_alias(role_id, data)


@router.get("/aliases/skills", response_model=list[SkillAliasOut])
async def list_skill_aliases(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    skill_id: str | None = None,
    verification_status: AliasVerificationStatus | None = None,
    search: str | None = None,
    service: AliasService = Depends(get_alias_service),
    principal: Principal = Depends(require_roles(*READ_ROLES)),
):
    return await service.list_skill_aliases(
        caller_role=principal.role,
        limit=limit,
        offset=offset,
        entity_id=skill_id,
        verification_status=verification_status,
        search=search,
    )


@router.get("/aliases/skills/{alias_id}", response_model=SkillAliasOut)
async def get_skill_alias(
    alias_id: uuid.UUID,
    service: AliasService = Depends(get_alias_service),
    principal: Principal = Depends(require_roles(*READ_ROLES)),
):
    return await service.get_skill_alias(alias_id, caller_role=principal.role)


@router.patch("/aliases/skills/{alias_id}", response_model=SkillAliasOut)
async def update_skill_alias(
    alias_id: uuid.UUID,
    data: AliasUpdate,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.update_skill_alias(alias_id, data)


@router.patch("/aliases/skills/{alias_id}/verify", response_model=SkillAliasOut)
async def verify_skill_alias(
    alias_id: uuid.UUID,
    data: AliasVerifyRequest,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.verify_skill_alias(alias_id, data)


@router.delete("/aliases/skills/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill_alias(
    alias_id: uuid.UUID,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    await service.delete_skill_alias(alias_id)


@router.get("/aliases/roles", response_model=list[RoleAliasOut])
async def list_role_aliases(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    role_id: str | None = None,
    verification_status: AliasVerificationStatus | None = None,
    search: str | None = None,
    service: AliasService = Depends(get_alias_service),
    principal: Principal = Depends(require_roles(*READ_ROLES)),
):
    return await service.list_role_aliases(
        caller_role=principal.role,
        limit=limit,
        offset=offset,
        entity_id=role_id,
        verification_status=verification_status,
        search=search,
    )


@router.get("/aliases/roles/{alias_id}", response_model=RoleAliasOut)
async def get_role_alias(
    alias_id: uuid.UUID,
    service: AliasService = Depends(get_alias_service),
    principal: Principal = Depends(require_roles(*READ_ROLES)),
):
    return await service.get_role_alias(alias_id, caller_role=principal.role)


@router.patch("/aliases/roles/{alias_id}", response_model=RoleAliasOut)
async def update_role_alias(
    alias_id: uuid.UUID,
    data: AliasUpdate,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.update_role_alias(alias_id, data)


@router.patch("/aliases/roles/{alias_id}/verify", response_model=RoleAliasOut)
async def verify_role_alias(
    alias_id: uuid.UUID,
    data: AliasVerifyRequest,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    return await service.verify_role_alias(alias_id, data)


@router.delete("/aliases/roles/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_alias(
    alias_id: uuid.UUID,
    service: AliasService = Depends(get_alias_service),
    _=Depends(require_roles(*ADMIN_ROLES)),
):
    await service.delete_role_alias(alias_id)
