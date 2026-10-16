from app.repositories.snapshots import SnapshotRepository
from app.schemas.snapshots import (
    KnowledgeSnapshotExport,
    SnapshotMetadata,
    SnapshotValidationResult,
)


class SnapshotService:
    def __init__(self, repo: SnapshotRepository):
        self.repo = repo

    async def export_snapshot(self, consumer: str = "SkillGap") -> KnowledgeSnapshotExport:
        return await self.repo.get_snapshot_data(consumer=consumer)

    async def get_metadata(self, consumer: str = "SkillGap") -> SnapshotMetadata:
        return await self.repo.get_metadata_only(consumer=consumer)

    async def validate_version(
        self, version: str, consumer: str = "SkillGap"
    ) -> SnapshotValidationResult:
        metadata = await self.get_metadata(consumer=consumer)
        is_current = metadata.version == version
        message = (
            "Snapshot version is up to date with authoritative SSKS knowledge graph"
            if is_current
            else f"Snapshot version is outdated (current authoritative version is {metadata.version})"
        )
        return SnapshotValidationResult(
            consumer=consumer,
            requested_version=version,
            current_version=metadata.version,
            is_current=is_current,
            generated_at=metadata.generated_at,
            counts=metadata.counts,
            message=message,
        )
