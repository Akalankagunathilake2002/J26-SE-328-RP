from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_core_service,
    require_admin,
    require_authenticated_user,
)
from app.schemas.core import DomainCreate, DomainOut, DomainUpdate, EntityStatus
from app.services.core import CoreService

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("/", response_model=list[DomainOut])
async def list_domains(
    status: EntityStatus | None = None,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_authenticated_user),
):
    return await service.list_domains(status=status)


@router.get("/{domain_id}", response_model=DomainOut)
async def get_domain(
    domain_id: str,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_authenticated_user),
):
    return await service.get_domain(domain_id)


@router.post("/", response_model=DomainOut, status_code=status.HTTP_201_CREATED)
async def create_domain(
    data: DomainCreate,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_admin),
):
    return await service.create_domain(data)


@router.patch("/{domain_id}", response_model=DomainOut)
async def update_domain(
    domain_id: str,
    data: DomainUpdate,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_admin),
):
    return await service.update_domain(domain_id, data)


@router.post("/{domain_id}/retire", response_model=DomainOut)
async def retire_domain(
    domain_id: str,
    service: CoreService = Depends(get_core_service),
    _=Depends(require_admin),
):
    return await service.retire_domain(domain_id)
