from fastapi import APIRouter, Depends, Query
from app.schemas.core import RoleOut, RoleCreate
from app.services.core import CoreService
from app.api.dependencies import get_core_service

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=list[RoleOut])
async def list_roles(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    domain_id: str | None = None,
    search: str | None = None,
    service: CoreService = Depends(get_core_service),
):
    return await service.list_roles(limit=limit, offset=offset, status=status, domain_id=domain_id, search=search)

@router.get("/{role_id}", response_model=RoleOut)
async def get_role(role_id: str, service: CoreService = Depends(get_core_service)):
    return await service.get_role(role_id)

@router.post("/", response_model=RoleOut)
async def create_role(data: RoleCreate, service: CoreService = Depends(get_core_service)):
    return await service.create_role(data)
