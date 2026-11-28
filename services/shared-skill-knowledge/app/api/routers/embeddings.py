from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_embedding_service,
    require_admin,
)
from app.schemas.embeddings import SkillEmbeddingOut, SkillEmbeddingSummaryOut, SkillEmbeddingUpsert
from app.services.embeddings import EmbeddingService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.get(
    "/skills",
    response_model=list[SkillEmbeddingOut] | list[SkillEmbeddingSummaryOut],
    summary="List stored skill embeddings (admin only)",
)
async def list_skill_embeddings(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    skill_id: str | None = None,
    embedding_model: str | None = None,
    include_vector: bool = False,
    service: EmbeddingService = Depends(get_embedding_service),
    _=Depends(require_admin),
):
    rows = await service.list_embeddings(
        limit=limit,
        offset=offset,
        skill_id=skill_id,
        embedding_model=embedding_model,
    )
    if include_vector:
        return [SkillEmbeddingOut.model_validate(row) for row in rows]
    return [SkillEmbeddingSummaryOut.model_validate(row) for row in rows]


@router.get(
    "/skills/{skill_id}",
    response_model=list[SkillEmbeddingOut],
    summary="Get stored embeddings for a skill (admin only)",
)
async def get_skill_embeddings(
    skill_id: str,
    embedding_model: str | None = None,
    service: EmbeddingService = Depends(get_embedding_service),
    _=Depends(require_admin),
):
    return await service.get_skill_embeddings(skill_id, embedding_model=embedding_model)


@router.put(
    "/skills/{skill_id}",
    response_model=SkillEmbeddingOut,
    summary="Upsert a precomputed 384-dim embedding for a skill (admin only)",
)
async def upsert_skill_embedding(
    skill_id: str,
    data: SkillEmbeddingUpsert,
    service: EmbeddingService = Depends(get_embedding_service),
    _=Depends(require_admin),
):
    return await service.upsert_skill_embedding(skill_id, data)


@router.delete(
    "/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete stored embeddings for a skill (admin only)",
)
async def delete_skill_embeddings(
    skill_id: str,
    embedding_model: str | None = None,
    service: EmbeddingService = Depends(get_embedding_service),
    _=Depends(require_admin),
):
    await service.delete_skill_embeddings(skill_id, embedding_model=embedding_model)
