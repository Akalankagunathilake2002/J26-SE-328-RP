from typing import Sequence
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aliases import SkillAlias, RoleAlias
from app.repositories.base import commit_or_conflict, delete_and_commit


class _BaseAliasRepository:
    model_cls = None
    entity_attr: str = ""

    def __init__(self, session: AsyncSession):
        self.session = session

    @property
    def _entity_col(self):
        return getattr(self.model_cls, self.entity_attr)

    async def get_by_id(self, alias_id: uuid.UUID):
        return await self.session.get(self.model_cls, alias_id)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        entity_id: str | None = None,
        verification_status: str | None = None,
        search: str | None = None,
    ) -> Sequence:
        stmt = select(self.model_cls)
        if entity_id:
            stmt = stmt.where(self._entity_col == entity_id)
        if verification_status:
            stmt = stmt.where(self.model_cls.verification_status == verification_status)
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(self.model_cls.alias_text).like(term))
        stmt = stmt.order_by(self._entity_col, self.model_cls.alias_text).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_verified_by_normalized_aliases(self, normalized_aliases: set[str]) -> Sequence:
        if not normalized_aliases:
            return []
        stmt = select(self.model_cls).where(
            self.model_cls.normalized_alias.in_(normalized_aliases),
            self.model_cls.verification_status == "VERIFIED",
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_entity_and_normalized(
        self,
        entity_id: str,
        normalized_alias: str,
        exclude_alias_id: uuid.UUID | None = None,
    ):
        stmt = select(self.model_cls).where(
            self._entity_col == entity_id,
            self.model_cls.normalized_alias == normalized_alias,
        )
        if exclude_alias_id is not None:
            stmt = stmt.where(self.model_cls.alias_id != exclude_alias_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_verified_by_normalized(
        self,
        normalized_alias: str,
        exclude_alias_id: uuid.UUID | None = None,
    ):
        stmt = select(self.model_cls).where(
            self.model_cls.normalized_alias == normalized_alias,
            self.model_cls.verification_status == "VERIFIED",
        )
        if exclude_alias_id is not None:
            stmt = stmt.where(self.model_cls.alias_id != exclude_alias_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        entity_id: str,
        alias_text: str,
        normalized_alias: str,
        source_id: uuid.UUID | None = None,
        verification_status: str = "UNVERIFIED",
    ):
        kwargs = {
            "alias_id": uuid.uuid4(),
            self.entity_attr: entity_id,
            "alias_text": alias_text,
            "normalized_alias": normalized_alias,
            "source_id": source_id,
            "verification_status": verification_status,
        }
        return await commit_or_conflict(self.session, self.model_cls(**kwargs))

    async def update(
        self,
        alias,
        *,
        alias_text: str | None = None,
        normalized_alias: str | None = None,
        source_id: uuid.UUID | None = None,
        update_source_id: bool = False,
        verification_status: str | None = None,
    ):
        if alias_text is not None:
            alias.alias_text = alias_text
        if normalized_alias is not None:
            alias.normalized_alias = normalized_alias
        if update_source_id:
            alias.source_id = source_id
        if verification_status is not None:
            alias.verification_status = verification_status
        return await commit_or_conflict(self.session, alias, refresh_targets=(alias,))

    async def delete(self, alias) -> None:
        await delete_and_commit(self.session, alias)


class SkillAliasRepository(_BaseAliasRepository):
    model_cls = SkillAlias
    entity_attr = "skill_id"


class RoleAliasRepository(_BaseAliasRepository):
    model_cls = RoleAlias
    entity_attr = "role_id"
