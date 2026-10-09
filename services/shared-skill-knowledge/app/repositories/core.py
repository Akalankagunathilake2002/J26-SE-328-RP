from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Domain, Skill, Role
from app.schemas.core import DomainCreate, SkillCreate, RoleCreate

class DomainRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> Sequence[Domain]:
        stmt = select(Domain)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: DomainCreate) -> Domain:
        domain = Domain(**data.model_dump())
        self.session.add(domain)
        await self.session.commit()
        return domain

class SkillRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> Sequence[Skill]:
        stmt = select(Skill)
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_by_id(self, skill_id: str) -> Skill | None:
        stmt = select(Skill).where(Skill.skill_id == skill_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: SkillCreate) -> Skill:
        skill = Skill(**data.model_dump())
        self.session.add(skill)
        await self.session.commit()
        return skill

class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> Sequence[Role]:
        stmt = select(Role)
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_by_id(self, role_id: str) -> Role | None:
        stmt = select(Role).where(Role.role_id == role_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: RoleCreate) -> Role:
        role = Role(**data.model_dump())
        self.session.add(role)
        await self.session.commit()
        return role
