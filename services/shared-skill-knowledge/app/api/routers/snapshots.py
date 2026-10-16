from fastapi import APIRouter, Depends, Query, status
from app.schemas.snapshots import (
    KnowledgeSnapshotExport,
    SnapshotMetadata,
    SnapshotValidationResult,
)
from app.services.snapshots import SnapshotService
from app.api.dependencies import get_snapshot_service

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get(
    "/export",
    response_model=KnowledgeSnapshotExport,
    status_code=status.HTTP_200_OK,
    summary="Export authoritative knowledge snapshot for consumer local cache",
)
async def export_snapshot(
    consumer: str = Query(
        "SkillGap",
        description="Target consumer component identifier, e.g. SkillGap (Skill Gap Analysis and Career Readiness Engine)",
    ),
    service: SnapshotService = Depends(get_snapshot_service),
):
    return await service.export_snapshot(consumer=consumer)


@router.post(
    "/export",
    response_model=KnowledgeSnapshotExport,
    status_code=status.HTTP_200_OK,
    summary="Request knowledge snapshot export (idempotent repeatable endpoint)",
)
async def request_snapshot_export(
    consumer: str = Query(
        "SkillGap",
        description="Target consumer component identifier, e.g. SkillGap (Skill Gap Analysis and Career Readiness Engine)",
    ),
    service: SnapshotService = Depends(get_snapshot_service),
):
    return await service.export_snapshot(consumer=consumer)


@router.get(
    "/metadata",
    response_model=SnapshotMetadata,
    status_code=status.HTTP_200_OK,
    summary="Get current snapshot metadata, version, and entity counts without downloading full payload",
)
async def get_snapshot_metadata(
    consumer: str = Query(
        "SkillGap",
        description="Consumer component identifier, e.g. SkillGap (Skill Gap Analysis and Career Readiness Engine)",
    ),
    service: SnapshotService = Depends(get_snapshot_service),
):
    return await service.get_metadata(consumer=consumer)


@router.get(
    "/validate",
    response_model=SnapshotValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate whether a local cache snapshot version is current or outdated",
)
async def validate_snapshot_version(
    version: str = Query(..., description="Local snapshot version string to validate"),
    consumer: str = Query(
        "SkillGap",
        description="Consumer component identifier, e.g. SkillGap (Skill Gap Analysis and Career Readiness Engine)",
    ),
    service: SnapshotService = Depends(get_snapshot_service),
):
    return await service.validate_version(version=version, consumer=consumer)
