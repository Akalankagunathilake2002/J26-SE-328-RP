from typing import Sequence
import uuid
from fastapi import HTTPException

from app.models.sources import KnowledgeSource, RoleExternalId, SkillExternalId
from app.repositories.core import RoleRepository, SkillRepository
from app.repositories.sources import (
    KnowledgeSourceRepository,
    RoleExternalIdRepository,
    SkillExternalIdRepository,
)


class SourceService:
    def __init__(
        self,
        source_repo: KnowledgeSourceRepository,
        skill_ext_repo: SkillExternalIdRepository,
        role_ext_repo: RoleExternalIdRepository,
        skill_repo: SkillRepository,
        role_repo: RoleRepository,
    ):
        self.source_repo = source_repo
        self.skill_ext_repo = skill_ext_repo
        self.role_ext_repo = role_ext_repo
        self.skill_repo = skill_repo
        self.role_repo = role_repo

    async def list_sources(
        self, limit: int = 100, offset: int = 0, search: str | None = None
    ) -> Sequence[KnowledgeSource]:
        return await self.source_repo.get_all(limit=limit, offset=offset, search=search)

    async def get_source(self, source_id: uuid.UUID) -> KnowledgeSource:
        source = await self.source_repo.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Knowledge source not found")
        return source

    async def list_skill_external_ids(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        skill_id: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> Sequence[SkillExternalId]:
        if skill_id is not None and not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        if source_id is not None:
            await self.get_source(source_id)
        return await self.skill_ext_repo.get_all(
            limit=limit, offset=offset, entity_id=skill_id, source_id=source_id
        )

    async def list_role_external_ids(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        role_id: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> Sequence[RoleExternalId]:
        if role_id is not None and not await self.role_repo.get_by_id(role_id):
            raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
        if source_id is not None:
            await self.get_source(source_id)
        return await self.role_ext_repo.get_all(
            limit=limit, offset=offset, entity_id=role_id, source_id=source_id
        )
