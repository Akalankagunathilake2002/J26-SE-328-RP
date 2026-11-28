from typing import Sequence
from fastapi import HTTPException

from app.models.embeddings import SkillEmbedding
from app.repositories.base import ConflictError
from app.repositories.core import SkillRepository
from app.repositories.embeddings import SkillEmbeddingRepository
from app.schemas.embeddings import SkillEmbeddingUpsert


class EmbeddingService:
    def __init__(self, embedding_repo: SkillEmbeddingRepository, skill_repo: SkillRepository):
        self.embedding_repo = embedding_repo
        self.skill_repo = skill_repo

    async def list_embeddings(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        skill_id: str | None = None,
        embedding_model: str | None = None,
    ) -> Sequence[SkillEmbedding]:
        if skill_id is not None and not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        return await self.embedding_repo.get_all(
            limit=limit, offset=offset, skill_id=skill_id, embedding_model=embedding_model
        )

    async def get_skill_embeddings(
        self, skill_id: str, embedding_model: str | None = None
    ) -> Sequence[SkillEmbedding]:
        if not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        rows = await self.embedding_repo.get_by_skill_id(skill_id, embedding_model=embedding_model)
        if not rows:
            raise HTTPException(status_code=404, detail=f"No embeddings found for skill '{skill_id}'")
        return rows

    async def upsert_skill_embedding(
        self, skill_id: str, data: SkillEmbeddingUpsert
    ) -> SkillEmbedding:
        if not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        try:
            return await self.embedding_repo.upsert(
                skill_id=skill_id,
                embedding_model=data.embedding_model,
                embedding_text_hash=data.embedding_text_hash,
                embedding=data.embedding,
            )
        except ConflictError:
            raise HTTPException(status_code=409, detail="Embedding upsert conflicts with an existing record")

    async def delete_skill_embeddings(
        self, skill_id: str, embedding_model: str | None = None
    ) -> None:
        if not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        deleted = await self.embedding_repo.delete_by_skill_id(skill_id, embedding_model=embedding_model)
        if deleted == 0:
            raise HTTPException(status_code=404, detail=f"No embeddings found for skill '{skill_id}'")
