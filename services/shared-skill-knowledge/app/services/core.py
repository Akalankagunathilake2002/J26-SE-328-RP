from typing import Sequence
from fastapi import HTTPException

from app.core.text import normalize_name
from app.models.core import Domain, Skill, Role
from app.repositories.base import ConflictError
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository
from app.schemas.core import (
    DomainCreate,
    DomainUpdate,
    SkillCreate,
    SkillUpdate,
    RoleCreate,
    RoleUpdate,
)


class CoreService:
    def __init__(self, domain_repo: DomainRepository, skill_repo: SkillRepository, role_repo: RoleRepository):
        self.domain_repo = domain_repo
        self.skill_repo = skill_repo
        self.role_repo = role_repo

    async def list_domains(self, status: str | None = None) -> Sequence[Domain]:
        return await self.domain_repo.get_all(status=status)

    async def get_domain(self, domain_id: str) -> Domain:
        domain = await self.domain_repo.get_by_id(domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain

    async def create_domain(self, data: DomainCreate) -> Domain:
        if data.domain_id and await self.domain_repo.get_by_id(data.domain_id):
            raise HTTPException(status_code=409, detail="Domain ID already exists")
        if await self.domain_repo.get_by_code(data.code):
            raise HTTPException(status_code=409, detail="Domain code already exists")
        try:
            return await self.domain_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Domain ID or code already exists")

    async def update_domain(self, domain_id: str, data: DomainUpdate) -> Domain:
        domain = await self.get_domain(domain_id)
        if data.code is not None and data.code != domain.code:
            existing_code = await self.domain_repo.get_by_code(data.code)
            if existing_code and existing_code.domain_id != domain.domain_id:
                raise HTTPException(status_code=409, detail="Domain code already exists")
        try:
            return await self.domain_repo.update(domain, data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Domain update conflicts with an existing record")

    async def retire_domain(self, domain_id: str) -> Domain:
        domain = await self.get_domain(domain_id)
        return await self.domain_repo.retire(domain)

    async def list_skills(self, **filters) -> Sequence[Skill]:
        return await self.skill_repo.get_all(**filters)

    async def get_skill(self, skill_id: str) -> Skill:
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        return skill

    async def create_skill(self, data: SkillCreate) -> Skill:
        if data.skill_id and await self.skill_repo.get_by_id(data.skill_id):
            raise HTTPException(status_code=409, detail="Skill ID already exists")
        norm = normalize_name(data.preferred_name)
        dup = await self.skill_repo.find_by_normalized_name(norm)
        if dup:
            raise HTTPException(
                status_code=409,
                detail=f"A canonical skill with normalized name '{data.preferred_name}' already exists (ID: {dup.skill_id})",
            )
        try:
            return await self.skill_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Skill conflicts with an existing record")

    async def update_skill(self, skill_id: str, data: SkillUpdate) -> Skill:
        skill = await self.get_skill(skill_id)
        if data.preferred_name is not None:
            norm = normalize_name(data.preferred_name)
            dup = await self.skill_repo.find_by_normalized_name(norm, exclude_skill_id=skill_id)
            if dup:
                raise HTTPException(
                    status_code=409,
                    detail=f"A canonical skill with normalized name '{data.preferred_name}' already exists (ID: {dup.skill_id})",
                )
        try:
            return await self.skill_repo.update(skill, data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Skill update conflicts with an existing record")

    async def retire_skill(self, skill_id: str) -> Skill:
        skill = await self.get_skill(skill_id)
        return await self.skill_repo.retire(skill)

    async def list_roles(self, **filters) -> Sequence[Role]:
        return await self.role_repo.get_all(**filters)

    async def get_role(self, role_id: str) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        if data.role_id and await self.role_repo.get_by_id(data.role_id):
            raise HTTPException(status_code=409, detail="Role ID already exists")
        norm = normalize_name(data.preferred_name)
        dup = await self.role_repo.find_by_normalized_name(norm)
        if dup:
            raise HTTPException(
                status_code=409,
                detail=f"A canonical role with normalized name '{data.preferred_name}' already exists (ID: {dup.role_id})",
            )
        try:
            return await self.role_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Role conflicts with an existing record")

    async def update_role(self, role_id: str, data: RoleUpdate) -> Role:
        role = await self.get_role(role_id)
        if data.preferred_name is not None:
            norm = normalize_name(data.preferred_name)
            dup = await self.role_repo.find_by_normalized_name(norm, exclude_role_id=role_id)
            if dup:
                raise HTTPException(
                    status_code=409,
                    detail=f"A canonical role with normalized name '{data.preferred_name}' already exists (ID: {dup.role_id})",
                )
        try:
            return await self.role_repo.update(role, data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Role update conflicts with an existing record")

    async def retire_role(self, role_id: str) -> Role:
        role = await self.get_role(role_id)
        return await self.role_repo.retire(role)
