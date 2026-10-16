import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Skill, Domain
from app.models.sources import KnowledgeSource, SkillExternalId
from app.models.aliases import SkillAlias
from app.models.relationships import SkillDomain, SkillRelationship
from app.schemas.snapshots import (
    SnapshotCounts,
    SnapshotSourceItem,
    SnapshotMetadata,
    SnapshotSkillItem,
    SnapshotAliasItem,
    SnapshotRelationshipItem,
    SnapshotExternalIdItem,
    SnapshotDomainItem,
    KnowledgeSnapshotExport,
)


class SnapshotRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _compute_version(
        self,
        skill_ids: list[str],
        alias_ids: list[str],
        rel_ids: list[str],
    ) -> str:
        hasher = hashlib.sha256()
        content = f"skills:{','.join(skill_ids)}|aliases:{','.join(alias_ids)}|rels:{','.join(rel_ids)}"
        hasher.update(content.encode("utf-8"))
        digest = hasher.hexdigest()[:12]
        date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"v{date_prefix}-{digest}"

    async def get_snapshot_data(self, consumer: str = "SkillGap") -> KnowledgeSnapshotExport:
        now = datetime.now(timezone.utc)

        # 1. Fetch active skills
        skills_stmt = select(Skill).where(Skill.status == "ACTIVE").order_by(Skill.skill_id)
        skills_res = await self.session.execute(skills_stmt)
        skills_raw = skills_res.scalars().all()
        active_skill_ids = {s.skill_id for s in skills_raw}

        # 2. Fetch skill-domain mappings
        sd_stmt = (
            select(SkillDomain.skill_id, Domain.domain_id, Domain.code)
            .join(Domain, SkillDomain.domain_id == Domain.domain_id)
            .where(Domain.status == "ACTIVE")
        )
        sd_res = await self.session.execute(sd_stmt)
        skill_domain_codes = defaultdict(list)
        skill_domain_ids = defaultdict(list)
        for sid, did, code in sd_res.all():
            if sid in active_skill_ids:
                skill_domain_codes[sid].append(code)
                skill_domain_ids[sid].append(did)

        snapshot_skills: list[SnapshotSkillItem] = []
        for s in skills_raw:
            snapshot_skills.append(
                SnapshotSkillItem(
                    skill_id=s.skill_id,
                    preferred_name=s.preferred_name,
                    skill_type=s.skill_type,
                    skill_nature=s.skill_nature,
                    domain_codes=skill_domain_codes.get(s.skill_id, []),
                    domain_ids=skill_domain_ids.get(s.skill_id, []),
                )
            )

        # 3. Fetch verified aliases for active skills only
        aliases_stmt = (
            select(SkillAlias)
            .where(
                SkillAlias.verification_status == "VERIFIED",
                SkillAlias.skill_id.in_(active_skill_ids) if active_skill_ids else False,
            )
            .order_by(SkillAlias.alias_id)
        )
        aliases_res = await self.session.execute(aliases_stmt)
        aliases_raw = aliases_res.scalars().all() if active_skill_ids else []
        snapshot_aliases = [
            SnapshotAliasItem(
                alias_id=a.alias_id,
                skill_id=a.skill_id,
                alias_text=a.alias_text,
                normalized_alias=a.normalized_alias,
            )
            for a in aliases_raw
        ]

        # 4. Fetch verified relationships where both skills are active
        rels_stmt = (
            select(SkillRelationship)
            .where(
                SkillRelationship.verification_status == "VERIFIED",
                SkillRelationship.source_skill_id.in_(active_skill_ids) if active_skill_ids else False,
                SkillRelationship.target_skill_id.in_(active_skill_ids) if active_skill_ids else False,
            )
            .order_by(SkillRelationship.relationship_id)
        )
        rels_res = await self.session.execute(rels_stmt)
        rels_raw = rels_res.scalars().all() if active_skill_ids else []
        snapshot_rels = [
            SnapshotRelationshipItem(
                relationship_id=r.relationship_id,
                source_skill_id=r.source_skill_id,
                target_skill_id=r.target_skill_id,
                relationship_type=r.relationship_type,
                verification_status=r.verification_status,
                evidence_note=r.evidence_note,
                source_id=r.source_id,
            )
            for r in rels_raw
        ]

        # 5. Fetch external identifiers for active skills
        ext_stmt = (
            select(SkillExternalId, KnowledgeSource.source_code)
            .outerjoin(KnowledgeSource, SkillExternalId.source_id == KnowledgeSource.source_id)
            .where(SkillExternalId.skill_id.in_(active_skill_ids) if active_skill_ids else False)
            .order_by(SkillExternalId.external_id_id)
        )
        ext_res = await self.session.execute(ext_stmt)
        snapshot_ext_ids: list[SnapshotExternalIdItem] = []
        if active_skill_ids:
            for ext, source_code in ext_res.all():
                snapshot_ext_ids.append(
                    SnapshotExternalIdItem(
                        external_id_id=ext.external_id_id,
                        skill_id=ext.skill_id,
                        source_id=ext.source_id,
                        source_code=source_code,
                        external_identifier=ext.external_identifier,
                    )
                )

        # 6. Fetch active domains
        dom_stmt = select(Domain).where(Domain.status == "ACTIVE").order_by(Domain.domain_id)
        dom_res = await self.session.execute(dom_stmt)
        snapshot_domains = [
            SnapshotDomainItem(
                domain_id=d.domain_id,
                code=d.code,
                name=d.name,
                description=d.description,
            )
            for d in dom_res.scalars().all()
        ]

        # 7. Fetch knowledge sources
        ks_stmt = select(KnowledgeSource).order_by(KnowledgeSource.source_id)
        ks_res = await self.session.execute(ks_stmt)
        snapshot_sources = [
            SnapshotSourceItem(
                source_id=k.source_id,
                source_code=k.source_code,
                source_name=k.source_name,
                source_version=k.source_version,
                last_synced_at=k.last_synced_at,
            )
            for k in ks_res.scalars().all()
        ]

        # 8. Compute version and metadata
        version = self._compute_version(
            skill_ids=[s.skill_id for s in snapshot_skills],
            alias_ids=[a.alias_id for a in snapshot_aliases],
            rel_ids=[r.relationship_id for r in snapshot_rels],
        )

        counts = SnapshotCounts(
            skills=len(snapshot_skills),
            aliases=len(snapshot_aliases),
            relationships=len(snapshot_rels),
            domains=len(snapshot_domains),
            external_ids=len(snapshot_ext_ids),
            sources=len(snapshot_sources),
        )

        metadata = SnapshotMetadata(
            snapshot_id=f"SNAP-{consumer}-{version}",
            consumer=consumer,
            version=version,
            generated_at=now,
            status="ACTIVE",
            counts=counts,
            source_metadata=snapshot_sources,
        )

        return KnowledgeSnapshotExport(
            metadata=metadata,
            skills=snapshot_skills,
            aliases=snapshot_aliases,
            relationships=snapshot_rels,
            external_ids=snapshot_ext_ids,
            domains=snapshot_domains,
            sources=snapshot_sources,
        )

    async def get_metadata_only(self, consumer: str = "SkillGap") -> SnapshotMetadata:
        export_data = await self.get_snapshot_data(consumer=consumer)
        return export_data.metadata
