from typing import Sequence
from fastapi import HTTPException
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository, ConflictError
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
        # Ensure domain ID and domain code are unique before saving.
        if await self.domain_repo.get_by_id(data.domain_id):
            raise HTTPException(status_code=409, detail="Domain ID already exists")
        if await self.domain_repo.get_by_code(data.code):
            raise HTTPException(status_code=409, detail="Domain code already exists")
        try:
            return await self.domain_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Domain ID or code already exists")

    async def list_skills(self, **filters) -> Sequence[Skill]:
        return await self.skill_repo.get_all(**filters)
        
    async def get_skill(self, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        return skill

    async def create_skill(self, data: SkillCreate) -> Skill:
        # Check that the skill ID does not already exist.
        if await self.skill_repo.get_by_id(data.skill_id):
            raise HTTPException(status_code=409, detail="Skill ID already exists")
        try:
            return await self.skill_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Skill conflicts with an existing record")

    async def list_roles(self, **filters) -> Sequence[Role]:
        return await self.role_repo.get_all(**filters)
        
    async def get_role(self, role_id: str) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        # Check that the role ID does not already exist.
        if await self.role_repo.get_by_id(data.role_id):
            raise HTTPException(status_code=409, detail="Role ID already exists")
        try:
            return await self.role_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Role conflicts with an existing record")
