from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.core.security import (
    ROLE_ADMIN,
    ROLE_HR,
    ROLE_SERVICE,
    ROLE_USER,
    Principal,
    resolve_principal,
)
from app.db.session import get_session
from app.repositories.aliases import RoleAliasRepository, SkillAliasRepository
from app.repositories.candidates import CandidateRepository
from app.repositories.core import DomainRepository, RoleRepository, SkillRepository
from app.repositories.embeddings import SkillEmbeddingRepository
from app.repositories.relationships import (
    CandidateRelationshipRepository,
    DomainAssociationRepository,
    SkillRelationshipRepository,
)
from app.repositories.sources import (
    KnowledgeSourceRepository,
    RoleExternalIdRepository,
    SkillExternalIdRepository,
)
from app.services.aliases import AliasService
from app.services.candidates import CandidateService
from app.services.core import CoreService
from app.services.embeddings import EmbeddingService
from app.services.normalization import NormalizationService
from app.services.relationships import (
    CandidateRelationshipService,
    DomainAssociationService,
    RelationshipService,
)
from app.services.sources import SourceService

_bearer = HTTPBearer(auto_error=False)

READ_ROLES = (ROLE_USER, ROLE_HR, ROLE_ADMIN, ROLE_SERVICE)
CANDIDATE_SUBMIT_ROLES = (ROLE_HR, ROLE_ADMIN, ROLE_SERVICE)
CANDIDATE_QUEUE_ROLES = (ROLE_HR, ROLE_ADMIN)
ADMIN_ROLES = (ROLE_ADMIN,)


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    """Authenticate caller from the Bearer JWT and return its verified principal."""
    if not credentials or credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await resolve_principal(credentials.credentials, settings)


def require_roles(*allowed_roles: str):
    """Build a FastAPI dependency enforcing that the caller holds one of allowed_roles."""
    allowed_set = frozenset(role.strip().upper() for role in allowed_roles)

    async def _require_role(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if principal.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions (required roles: {', '.join(sorted(allowed_set))})",
            )
        return principal

    return _require_role


async def require_service_access(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    """Restrict access to internal SERVICE or ADMIN principals."""
    if principal.role not in (ROLE_SERVICE, ROLE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service or admin authorization required",
        )
    return principal


async def require_reviewer(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    """Restrict candidate review operations to authenticated HR or ADMIN principals."""
    if principal.role not in (ROLE_HR, ROLE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer authorization required (HR or ADMIN role)",
        )
    return principal


def get_core_service(session: AsyncSession = Depends(get_session)) -> CoreService:
    return CoreService(
        DomainRepository(session),
        SkillRepository(session),
        RoleRepository(session),
    )


def get_candidate_service(session: AsyncSession = Depends(get_session)) -> CandidateService:
    return CandidateService(
        candidate_repo=CandidateRepository(session),
        skill_repo=SkillRepository(session),
        role_repo=RoleRepository(session),
        skill_alias_repo=SkillAliasRepository(session),
        role_alias_repo=RoleAliasRepository(session),
        source_repo=KnowledgeSourceRepository(session),
    )


def get_normalization_service(session: AsyncSession = Depends(get_session)) -> NormalizationService:
    return NormalizationService(
        skill_repo=SkillRepository(session),
        role_repo=RoleRepository(session),
        skill_alias_repo=SkillAliasRepository(session),
        role_alias_repo=RoleAliasRepository(session),
    )


def get_relationship_service(session: AsyncSession = Depends(get_session)) -> RelationshipService:
    return RelationshipService(
        rel_repo=SkillRelationshipRepository(session),
        skill_repo=SkillRepository(session),
        source_repo=KnowledgeSourceRepository(session),
    )


def get_candidate_relationship_service(
    session: AsyncSession = Depends(get_session),
) -> CandidateRelationshipService:
    return CandidateRelationshipService(
        candidate_repo=CandidateRelationshipRepository(session),
        rel_repo=SkillRelationshipRepository(session),
        skill_repo=SkillRepository(session),
        source_repo=KnowledgeSourceRepository(session),
    )


def get_domain_association_service(
    session: AsyncSession = Depends(get_session),
) -> DomainAssociationService:
    return DomainAssociationService(
        assoc_repo=DomainAssociationRepository(session),
        skill_repo=SkillRepository(session),
        role_repo=RoleRepository(session),
        domain_repo=DomainRepository(session),
    )


def get_alias_service(session: AsyncSession = Depends(get_session)) -> AliasService:
    return AliasService(
        skill_alias_repo=SkillAliasRepository(session),
        role_alias_repo=RoleAliasRepository(session),
        skill_repo=SkillRepository(session),
        role_repo=RoleRepository(session),
        source_repo=KnowledgeSourceRepository(session),
    )


def get_source_service(session: AsyncSession = Depends(get_session)) -> SourceService:
    return SourceService(
        source_repo=KnowledgeSourceRepository(session),
        skill_ext_repo=SkillExternalIdRepository(session),
        role_ext_repo=RoleExternalIdRepository(session),
        skill_repo=SkillRepository(session),
        role_repo=RoleRepository(session),
    )


def get_embedding_service(session: AsyncSession = Depends(get_session)) -> EmbeddingService:
    return EmbeddingService(
        embedding_repo=SkillEmbeddingRepository(session),
        skill_repo=SkillRepository(session),
    )
