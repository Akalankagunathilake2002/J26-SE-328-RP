from fastapi import APIRouter, Depends, status
from app.schemas.core import DomainOut
from app.schemas.relationships import SkillDomainAssociationOut
from app.services.relationships import DomainAssociationService
from app.api.dependencies import get_domain_association_service

router = APIRouter(prefix="/skills", tags=["skills", "domains"])


@router.get(
    "/{skill_id}/domains",
    response_model=list[DomainOut],
    summary="List domains associated with a skill",
)
async def list_skill_domains(
    skill_id: str,
    service: DomainAssociationService = Depends(get_domain_association_service),
):
    return await service.list_skill_domains(skill_id)


@router.put(
    "/{skill_id}/domains/{domain_id}",
    response_model=SkillDomainAssociationOut,
    status_code=status.HTTP_200_OK,
    summary="Associate a domain with a skill",
)
async def associate_skill_domain(
    skill_id: str,
    domain_id: str,
    service: DomainAssociationService = Depends(get_domain_association_service),
):
    assoc = await service.associate_skill_domain(skill_id, domain_id)
    return SkillDomainAssociationOut(skill_id=assoc.skill_id, domain_id=assoc.domain_id)


@router.delete(
    "/{skill_id}/domains/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a domain association from a skill",
)
async def remove_skill_domain(
    skill_id: str,
    domain_id: str,
    service: DomainAssociationService = Depends(get_domain_association_service),
):
    await service.remove_skill_domain(skill_id, domain_id)
