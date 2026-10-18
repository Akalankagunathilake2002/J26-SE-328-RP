from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Domain, Skill, Role
from app.models.relationships import SkillDomain, RoleDomain
from app.schemas.core import DomainCreate, SkillCreate, RoleCreate

class ConflictError(Exception):
    pass

async def _insert(session: AsyncSession, obj):
    # Commit changes and map database integrity errors to ConflictError.
    session.add(obj)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError from exc
    except Exception:
        await session.rollback()
        raise
    return obj

class DomainRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> Sequence[Domain]:
        stmt = select(Domain).order_by(Domain.domain_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, domain_id: str) -> Domain | None:
        return await self.session.get(Domain, domain_id)

    async def get_by_code(self, code: str) -> Domain | None:
        result = await self.session.execute(select(Domain).where(Domain.code == code))
        return result.scalars().first()

    async def create(self, data: DomainCreate) -> Domain:
        return await _insert(self.session, Domain(**data.model_dump()))

class SkillRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        skill_type: str | None = None,
        skill_nature: str | None = None,
        domain_id: str | None = None,
    ) -> Sequence[Skill]:
        stmt = select(Skill)
        if status:
            stmt = stmt.where(Skill.status == status)
        if skill_type:
            stmt = stmt.where(Skill.skill_type == skill_type)
        if skill_nature:
            stmt = stmt.where(Skill.skill_nature == skill_nature)
        if domain_id:
            # Filter skills belonging to the specified domain.
            stmt = stmt.where(
                Skill.skill_id.in_(select(SkillDomain.skill_id).where(SkillDomain.domain_id == domain_id))
            )
        stmt = stmt.order_by(Skill.skill_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_by_id(self, skill_id: str) -> Skill | None:
        stmt = select(Skill).where(Skill.skill_id == skill_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: SkillCreate) -> Skill:
        return await _insert(self.session, Skill(**data.model_dump()))

class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        domain_id: str | None = None,
    ) -> Sequence[Role]:
        stmt = select(Role)
        if status:
            stmt = stmt.where(Role.status == status)
        if domain_id:
            # Filter roles belonging to the specified domain.
            stmt = stmt.where(
                Role.role_id.in_(select(RoleDomain.role_id).where(RoleDomain.domain_id == domain_id))
            )
        stmt = stmt.order_by(Role.role_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_by_id(self, role_id: str) -> Role | None:
        stmt = select(Role).where(Role.role_id == role_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: RoleCreate) -> Role:
        return await _insert(self.session, Role(**data.model_dump()))
