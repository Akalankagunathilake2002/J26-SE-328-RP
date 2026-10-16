from fastapi import APIRouter, Depends, status
from app.schemas.core import DomainOut
from app.schemas.relationships import RoleDomainAssociationOut
from app.services.relationships import DomainAssociationService
from app.api.dependencies import get_domain_association_service

router = APIRouter(prefix="/roles", tags=["roles", "domains"])


@router.get(
    "/{role_id}/domains",
    response_model=list[DomainOut],
    summary="List domains associated with a role",
)
async def list_role_domains(
    role_id: str,
    service: DomainAssociationService = Depends(get_domain_association_service),
):
    return await service.list_role_domains(role_id)


@router.put(
    "/{role_id}/domains/{domain_id}",
    response_model=RoleDomainAssociationOut,
    status_code=status.HTTP_200_OK,
    summary="Associate a domain with a role",
)
async def associate_role_domain(
    role_id: str,
    domain_id: str,
    service: DomainAssociationService = Depends(get_domain_association_service),
):
    assoc = await service.associate_role_domain(role_id, domain_id)
    return RoleDomainAssociationOut(role_id=assoc.role_id, domain_id=assoc.domain_id)


@router.delete(
    "/{role_id}/domains/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a domain association from a role",
)
async def remove_role_domain(
    role_id: str,
    domain_id: str,
    service: DomainAssociationService = Depends(get_domain_association_service),
):
    await service.remove_role_domain(role_id, domain_id)
