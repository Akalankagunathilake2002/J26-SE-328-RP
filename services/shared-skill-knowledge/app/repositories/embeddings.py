from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embeddings import SkillEmbedding
from app.repositories.base import commit_or_conflict, delete_and_commit


class SkillEmbeddingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        skill_id: str | None = None,
        embedding_model: str | None = None,
    ) -> Sequence[SkillEmbedding]:
        stmt = select(SkillEmbedding)
        if skill_id:
            stmt = stmt.where(SkillEmbedding.skill_id == skill_id)
        if embedding_model:
            stmt = stmt.where(SkillEmbedding.embedding_model == embedding_model)
        stmt = stmt.order_by(SkillEmbedding.skill_id, SkillEmbedding.embedding_model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_skill_id(
        self, skill_id: str, embedding_model: str | None = None
    ) -> Sequence[SkillEmbedding]:
        stmt = select(SkillEmbedding).where(SkillEmbedding.skill_id == skill_id)
        if embedding_model:
            stmt = stmt.where(SkillEmbedding.embedding_model == embedding_model)
        stmt = stmt.order_by(SkillEmbedding.embedding_model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_one(self, skill_id: str, embedding_model: str) -> SkillEmbedding | None:
        return await self.session.get(SkillEmbedding, (skill_id, embedding_model))

    async def upsert(
        self,
        skill_id: str,
        embedding_model: str,
        embedding_text_hash: str,
        embedding: list[float],
    ) -> SkillEmbedding:
        now = datetime.now(timezone.utc)
        existing = await self.get_one(skill_id, embedding_model)
        if existing:
            existing.embedding_dimension = 384
            existing.embedding_text_hash = embedding_text_hash
            existing.embedding = embedding
            existing.generated_at = now
            return await commit_or_conflict(self.session, existing, refresh_targets=(existing,))

        record = SkillEmbedding(
            skill_id=skill_id,
            embedding_model=embedding_model,
            embedding_dimension=384,
            embedding_text_hash=embedding_text_hash,
            embedding=embedding,
            generated_at=now,
        )
        return await commit_or_conflict(self.session, record, refresh_targets=(record,))

    async def delete_by_skill_id(self, skill_id: str, embedding_model: str | None = None) -> int:
        rows = await self.get_by_skill_id(skill_id, embedding_model=embedding_model)
        count = 0
        for row in rows:
            await delete_and_commit(self.session, row)
            count += 1
        return count
