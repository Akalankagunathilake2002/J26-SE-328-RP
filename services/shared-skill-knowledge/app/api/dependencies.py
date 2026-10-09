from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository
from app.services.core import CoreService

def get_core_service(session: AsyncSession = Depends(get_session)) -> CoreService:
    return CoreService(
        DomainRepository(session),
        SkillRepository(session),
        RoleRepository(session)
    )
