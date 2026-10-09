from typing import Sequence
from fastapi import HTTPException
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository
from app.schemas.core import DomainCreate, SkillCreate, RoleCreate
from app.models.core import Domain, Skill, Role

class CoreService:
    def __init__(self, domain_repo: DomainRepository, skill_repo: SkillRepository, role_repo: RoleRepository):
        self.domain_repo = domain_repo
        self.skill_repo = skill_repo
        self.role_repo = role_repo
        
    async def list_domains(self) -> Sequence[Domain]:
        return await self.domain_repo.get_all()
        
    async def create_domain(self, data: DomainCreate) -> Domain:
        return await self.domain_repo.create(data)

    async def list_skills(self) -> Sequence[Skill]:
        return await self.skill_repo.get_all()
        
    async def get_skill(self, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        return skill

    async def create_skill(self, data: SkillCreate) -> Skill:
        return await self.skill_repo.create(data)

    async def list_roles(self) -> Sequence[Role]:
        return await self.role_repo.get_all()
        
    async def get_role(self, role_id: str) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        return await self.role_repo.create(data)
