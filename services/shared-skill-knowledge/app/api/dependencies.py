from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository
from app.repositories.candidates import CandidateRepository
from app.services.core import CoreService
from app.services.candidates import CandidateService
from app.services.normalization import NormalizationService

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

def verify_reviewer(x_reviewer_id: str | None = Header(None, alias="X-Reviewer-Id")) -> str:
    # TEMPORARY DEVELOPMENT MECHANISM: Real authentication and authorization is pending integration
    # with central auth-service. This check requires the X-Reviewer-Id header to prevent unrestricted access.
    if not x_reviewer_id or not x_reviewer_id.strip():
        raise HTTPException(
            status_code=403,
            detail="Reviewer authorization required (provide non-empty X-Reviewer-Id header). Note: this is a temporary development mechanism."
        )
    return x_reviewer_id.strip()
