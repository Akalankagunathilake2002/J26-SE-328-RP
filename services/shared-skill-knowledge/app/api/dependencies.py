from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository
from app.repositories.candidates import CandidateRepository
from app.repositories.relationships import (
    SkillRelationshipRepository,
    CandidateRelationshipRepository,
    DomainAssociationRepository,
)
from app.services.core import CoreService
from app.services.candidates import CandidateService
from app.services.normalization import NormalizationService
from app.services.relationships import (
    RelationshipService,
    CandidateRelationshipService,
    DomainAssociationService,
)

def get_core_service(session: AsyncSession = Depends(get_session)) -> CoreService:
    return CoreService(
        DomainRepository(session),
        SkillRepository(session),
        RoleRepository(session)
    )

def get_candidate_service(session: AsyncSession = Depends(get_session)) -> CandidateService:
    return CandidateService(
        session=session,
        candidate_repo=CandidateRepository(session)
    )

def get_normalization_service(session: AsyncSession = Depends(get_session)) -> NormalizationService:
    return NormalizationService(session=session)

def get_relationship_service(session: AsyncSession = Depends(get_session)) -> RelationshipService:
    return RelationshipService(
        rel_repo=SkillRelationshipRepository(session),
        skill_repo=SkillRepository(session),
    )

from app.repositories.snapshots import SnapshotRepository
from app.services.snapshots import SnapshotService

def get_candidate_relationship_service(session: AsyncSession = Depends(get_session)) -> CandidateRelationshipService:
    return CandidateRelationshipService(
        candidate_repo=CandidateRelationshipRepository(session),
        rel_repo=SkillRelationshipRepository(session),
        skill_repo=SkillRepository(session),
        snapshot_repo=SnapshotRepository(session),
    )

def get_domain_association_service(session: AsyncSession = Depends(get_session)) -> DomainAssociationService:
    return DomainAssociationService(
        assoc_repo=DomainAssociationRepository(session),
        skill_repo=SkillRepository(session),
        role_repo=RoleRepository(session),
        domain_repo=DomainRepository(session),
    )


def get_snapshot_service(session: AsyncSession = Depends(get_session)) -> SnapshotService:
    return SnapshotService(repo=SnapshotRepository(session))

def verify_reviewer(x_reviewer_id: str | None = Header(None, alias="X-Reviewer-Id")) -> str:
    # Temporary check requiring a reviewer ID header until central auth-service is integrated.
    if not x_reviewer_id or not x_reviewer_id.strip():
        raise HTTPException(
            status_code=403,
            detail="Reviewer authorization required (provide non-empty X-Reviewer-Id header). Note: this is a temporary development mechanism."
        )
    return x_reviewer_id.strip()
