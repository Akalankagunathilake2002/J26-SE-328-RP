from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.core.security import (
    ROLE_ADMIN,
    ROLE_HR,
    ROLE_USER,
    SUPPORTED_ROLES,
    Principal,
    resolve_principal,
    verify_internal_service_key,
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
_internal_service_key_primary = APIKeyHeader(name="X-Internal-Service-Key", auto_error=False)
_internal_service_key_alt = APIKeyHeader(name="X-Service-Key", auto_error=False)

_HR_OR_ADMIN_ROLES = frozenset({ROLE_HR, ROLE_ADMIN})


def get_internal_service_key(
    key1: Annotated[str | None, Depends(_internal_service_key_primary)],
    key2: Annotated[str | None, Depends(_internal_service_key_alt)],
) -> str | None:
    """Extract internal service credential from primary or alias header."""
    if key1 is not None:
        return key1
    return key2


async def _authenticate_bearer(
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
) -> Principal:
    if not credentials or credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await resolve_principal(credentials.credentials, settings)


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    service_key: Annotated[str | None, Depends(get_internal_service_key)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    """Authenticate human caller from Bearer JWT or reject internal service caller with 403."""
    if service_key is not None:
        verify_internal_service_key(service_key, settings)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal services are not authorized for this operation",
        )

    return await _authenticate_bearer(credentials, settings)


def _enforce_roles(principal: Principal, allowed_roles: frozenset[str], detail: str) -> Principal:
    if principal.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return principal


async def require_authenticated_user(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    """Allow any authenticated human role: user, hr, or admin."""
    return _enforce_roles(principal, SUPPORTED_ROLES, "Authenticated user role required")


async def require_hr_or_admin(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    """Allow hr or admin human roles for candidate queue and review operations."""
    return _enforce_roles(principal, _HR_OR_ADMIN_ROLES, "HR or admin authorization required")


async def require_admin(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Principal:
    """Allow admin human role only for canonical knowledge management."""
    return _enforce_roles(principal, frozenset({ROLE_ADMIN}), "Admin authorization required")


async def _authenticate_human_or_service(
    credentials: HTTPAuthorizationCredentials | None,
    service_key: str | None,
    settings: Settings,
    allowed_human_roles: frozenset[str],
    forbidden_detail: str,
) -> Principal | None:
    # Keep internal service credential validation isolated from human JWT auth.
    if service_key is not None:
        verify_internal_service_key(service_key, settings)
        return None

    principal = await _authenticate_bearer(credentials, settings)
    return _enforce_roles(principal, allowed_human_roles, forbidden_detail)


async def require_authenticated_user_or_service(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    service_key: Annotated[str | None, Depends(get_internal_service_key)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal | None:
    """Allow authenticated human callers or verified internal services for normalization."""
    return await _authenticate_human_or_service(
        credentials,
        service_key,
        settings,
        SUPPORTED_ROLES,
        "Authenticated user role required",
    )


async def require_hr_admin_or_service(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    service_key: Annotated[str | None, Depends(get_internal_service_key)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal | None:
    """Allow hr/admin callers or verified internal services to submit candidate entities."""
    return await _authenticate_human_or_service(
        credentials,
        service_key,
        settings,
        _HR_OR_ADMIN_ROLES,
        "HR or admin authorization required",
    )


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
