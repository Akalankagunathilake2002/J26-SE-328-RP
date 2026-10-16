from fastapi import APIRouter, Depends
from app.schemas.core import DomainOut, DomainCreate
from app.services.core import CoreService
from app.api.dependencies import get_core_service

router = APIRouter(prefix="/domains", tags=["domains"])

@router.get("/", response_model=list[DomainOut])
async def list_domains(service: CoreService = Depends(get_core_service)):
    return await service.list_domains()

@router.post("/", response_model=DomainOut)
async def create_domain(data: DomainCreate, service: CoreService = Depends(get_core_service)):
    return await service.create_domain(data)
