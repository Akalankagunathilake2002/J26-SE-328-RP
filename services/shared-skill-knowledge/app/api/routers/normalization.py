from fastapi import APIRouter, Depends

from app.api.dependencies import get_normalization_service, require_authenticated_user_or_service
from app.schemas.normalization import BulkNormalizeRequest, BulkNormalizeResponse
from app.services.normalization import NormalizationService

router = APIRouter(prefix="/normalize", tags=["normalization"])


@router.post(
    "/skills",
    response_model=BulkNormalizeResponse,
    summary="Bulk normalize skills",
)
async def normalize_skills(
    request: BulkNormalizeRequest,
    service: NormalizationService = Depends(get_normalization_service),
    _=Depends(require_authenticated_user_or_service),
):
    return await service.normalize_skills(request)


@router.post(
    "/roles",
    response_model=BulkNormalizeResponse,
    summary="Bulk normalize roles",
)
async def normalize_roles(
    request: BulkNormalizeRequest,
    service: NormalizationService = Depends(get_normalization_service),
    _=Depends(require_authenticated_user_or_service),
):
    return await service.normalize_roles(request)
