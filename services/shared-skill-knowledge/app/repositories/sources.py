from typing import Sequence
import uuid
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sources import KnowledgeSource, SkillExternalId, RoleExternalId


class KnowledgeSourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, source_id: uuid.UUID) -> KnowledgeSource | None:
        return await self.session.get(KnowledgeSource, source_id)

    async def get_by_code(self, source_code: str) -> KnowledgeSource | None:
        result = await self.session.execute(
            select(KnowledgeSource).where(KnowledgeSource.source_code == source_code)
        )
        return result.scalars().first()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
    ) -> Sequence[KnowledgeSource]:
        stmt = select(KnowledgeSource)
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(KnowledgeSource.source_code).like(term),
                    func.lower(KnowledgeSource.source_name).like(term),
                )
            )
        stmt = stmt.order_by(KnowledgeSource.source_code).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class _BaseExternalIdRepository:
    model_cls = None
    entity_attr: str = ""

    def __init__(self, session: AsyncSession):
        self.session = session

    @property
    def _entity_col(self):
        return getattr(self.model_cls, self.entity_attr)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        entity_id: str | None = None,
        source_id: uuid.UUID | None = None,
    ):
        stmt = select(self.model_cls)
        if entity_id:
            stmt = stmt.where(self._entity_col == entity_id)
        if source_id:
            stmt = stmt.where(self.model_cls.source_id == source_id)
        stmt = stmt.order_by(self._entity_col, self.model_cls.external_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SkillExternalIdRepository(_BaseExternalIdRepository):
    model_cls = SkillExternalId
    entity_attr = "skill_id"


class RoleExternalIdRepository(_BaseExternalIdRepository):
    model_cls = RoleExternalId
    entity_attr = "role_id"
