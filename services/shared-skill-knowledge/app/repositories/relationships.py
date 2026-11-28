from datetime import datetime, timezone
from typing import Sequence
import uuid
from sqlalchemy import String, cast, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Domain
from app.models.relationships import (
    SkillRelationship,
    CandidateSkillRelationship,
    SkillDomain,
    RoleDomain,
)
from app.repositories.base import ConflictError, commit_or_conflict, delete_and_commit
from app.schemas.relationships import (
    SkillRelationshipCreate,
    SkillRelationshipUpdate,
    CandidateRelationshipCreate,
)


class SkillRelationshipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, relationship_id: uuid.UUID) -> SkillRelationship | None:
        return await self.session.get(SkillRelationship, relationship_id)

    async def find_existing(
        self, source_skill_id: str, target_skill_id: str, relationship_type: str
    ) -> SkillRelationship | None:
        stmt = select(SkillRelationship).where(
            SkillRelationship.source_skill_id == source_skill_id,
            SkillRelationship.target_skill_id == target_skill_id,
            SkillRelationship.relationship_type == relationship_type,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        source_skill_id: str | None = None,
        target_skill_id: str | None = None,
        relationship_type: str | None = None,
        verification_status: str | None = None,
        search: str | None = None,
    ) -> Sequence[SkillRelationship]:
        stmt = select(SkillRelationship)
        if source_skill_id:
            stmt = stmt.where(SkillRelationship.source_skill_id == source_skill_id)
        if target_skill_id:
            stmt = stmt.where(SkillRelationship.target_skill_id == target_skill_id)
        if relationship_type:
            stmt = stmt.where(SkillRelationship.relationship_type == relationship_type)
        if verification_status:
            stmt = stmt.where(SkillRelationship.verification_status == verification_status)
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                cast(SkillRelationship.relationship_id, String).ilike(term)
                | SkillRelationship.source_skill_id.ilike(term)
                | SkillRelationship.target_skill_id.ilike(term)
                | SkillRelationship.relationship_type.ilike(term)
            )
        stmt = (
            stmt.order_by(SkillRelationship.created_at.desc(), SkillRelationship.relationship_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        data: SkillRelationshipCreate,
        reviewed_by: uuid.UUID | None = None,
        relationship_id: uuid.UUID | None = None,
    ) -> SkillRelationship:
        rel = SkillRelationship(
            relationship_id=relationship_id or uuid.uuid4(),
            source_skill_id=data.source_skill_id,
            target_skill_id=data.target_skill_id,
            relationship_type=data.relationship_type,
            verification_status=data.verification_status,
            source_id=data.source_id,
            evidence_note=data.evidence_note,
            evidence_description=data.evidence_description,
            evidence_url=data.evidence_url,
            reviewed_by=reviewed_by,
        )
        return await commit_or_conflict(self.session, rel, refresh_targets=(rel,))

    async def update(
        self,
        rel: SkillRelationship,
        data: SkillRelationshipUpdate,
        reviewed_by: uuid.UUID | None = None,
    ) -> SkillRelationship:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rel, field, value)
        if reviewed_by is not None:
            rel.reviewed_by = reviewed_by
        rel.updated_at = datetime.now(timezone.utc)
        return await commit_or_conflict(self.session, rel, refresh_targets=(rel,))

    async def delete(self, rel: SkillRelationship) -> None:
        await delete_and_commit(self.session, rel)


class CandidateRelationshipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, candidate_relationship_id: uuid.UUID) -> CandidateSkillRelationship | None:
        return await self.session.get(CandidateSkillRelationship, candidate_relationship_id)

    async def get_pending_duplicate(
        self, source_skill_id: str, target_skill_id: str, proposed_relationship_type: str
    ) -> CandidateSkillRelationship | None:
        stmt = select(CandidateSkillRelationship).where(
            CandidateSkillRelationship.source_skill_id == source_skill_id,
            CandidateSkillRelationship.target_skill_id == target_skill_id,
            CandidateSkillRelationship.proposed_relationship_type == proposed_relationship_type,
            CandidateSkillRelationship.review_status == "PENDING",
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        source_skill_id: str | None = None,
        target_skill_id: str | None = None,
        proposed_relationship_type: str | None = None,
        review_status: str | None = None,
    ) -> Sequence[CandidateSkillRelationship]:
        stmt = select(CandidateSkillRelationship)
        if source_skill_id:
            stmt = stmt.where(CandidateSkillRelationship.source_skill_id == source_skill_id)
        if target_skill_id:
            stmt = stmt.where(CandidateSkillRelationship.target_skill_id == target_skill_id)
        if proposed_relationship_type:
            stmt = stmt.where(CandidateSkillRelationship.proposed_relationship_type == proposed_relationship_type)
        if review_status:
            stmt = stmt.where(CandidateSkillRelationship.review_status == review_status)
        stmt = (
            stmt.order_by(
                CandidateSkillRelationship.created_at.desc(),
                CandidateSkillRelationship.candidate_relationship_id,
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: CandidateRelationshipCreate) -> CandidateSkillRelationship:
        candidate = CandidateSkillRelationship(
            candidate_relationship_id=uuid.uuid4(),
            source_skill_id=data.source_skill_id,
            target_skill_id=data.target_skill_id,
            proposed_relationship_type=data.proposed_relationship_type,
            confidence_score=data.confidence_score,
            review_status="PENDING",
            source_id=data.source_id,
            review_note=data.review_note,
            evidence_description=data.evidence_description,
            evidence_url=data.evidence_url,
        )
        return await commit_or_conflict(self.session, candidate, refresh_targets=(candidate,))

    async def reject(
        self,
        candidate: CandidateSkillRelationship,
        review_note: str | None = None,
        reviewed_by: uuid.UUID | None = None,
    ) -> CandidateSkillRelationship:
        candidate.review_status = "REJECTED"
        if review_note is not None:
            candidate.review_note = review_note
        if reviewed_by is not None:
            candidate.reviewed_by = str(reviewed_by)
        candidate.reviewed_at = datetime.now(timezone.utc)
        return await commit_or_conflict(self.session, candidate, refresh_targets=(candidate,))

    async def approve_and_create_canonical(
        self,
        candidate: CandidateSkillRelationship,
        source_skill_id: str,
        target_skill_id: str,
        relationship_type: str,
        review_note: str | None = None,
        evidence_description: str | None = None,
        evidence_url: str | None = None,
        reviewed_by: uuid.UUID | None = None,
    ) -> tuple[CandidateSkillRelationship, SkillRelationship]:
        canonical_id = uuid.uuid4()
        canonical_rel = SkillRelationship(
            relationship_id=canonical_id,
            source_skill_id=source_skill_id,
            target_skill_id=target_skill_id,
            relationship_type=relationship_type,
            verification_status="VERIFIED",
            source_id=candidate.source_id,
            evidence_note=evidence_description or review_note or candidate.review_note,
            evidence_description=evidence_description,
            evidence_url=evidence_url,
            reviewed_by=reviewed_by,
        )
        self.session.add(canonical_rel)
        try:
            # Flush parent canonical relationship before mutating candidate FK so SQLite/Postgres FK checks pass.
            await self.session.flush()
            candidate.source_skill_id = source_skill_id
            candidate.target_skill_id = target_skill_id
            candidate.proposed_relationship_type = relationship_type
            candidate.review_status = "APPROVED"
            if review_note is not None:
                candidate.review_note = review_note
            candidate.evidence_description = evidence_description
            candidate.evidence_url = evidence_url
            candidate.reviewed_by = str(reviewed_by) if reviewed_by is not None else None
            candidate.canonical_relationship_id = canonical_id
            candidate.reviewed_at = datetime.now(timezone.utc)
            self.session.add(candidate)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError from exc
        except Exception:
            await self.session.rollback()
            raise

        await self.session.refresh(candidate)
        await self.session.refresh(canonical_rel)
        return candidate, canonical_rel


class DomainAssociationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_skill_domains(self, skill_id: str) -> Sequence[Domain]:
        stmt = (
            select(Domain)
            .join(SkillDomain, Domain.domain_id == SkillDomain.domain_id)
            .where(SkillDomain.skill_id == skill_id)
            .order_by(Domain.domain_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_skill_domain(self, skill_id: str, domain_id: str) -> SkillDomain | None:
        stmt = select(SkillDomain).where(
            SkillDomain.skill_id == skill_id,
            SkillDomain.domain_id == domain_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_skill_domain(self, skill_id: str, domain_id: str) -> SkillDomain:
        existing = await self.get_skill_domain(skill_id, domain_id)
        if existing:
            return existing
        return await commit_or_conflict(self.session, SkillDomain(skill_id=skill_id, domain_id=domain_id))

    async def delete_skill_domain(self, assoc: SkillDomain) -> None:
        await delete_and_commit(self.session, assoc)

    async def get_role_domains(self, role_id: str) -> Sequence[Domain]:
        stmt = (
            select(Domain)
            .join(RoleDomain, Domain.domain_id == RoleDomain.domain_id)
            .where(RoleDomain.role_id == role_id)
            .order_by(Domain.domain_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_role_domain(self, role_id: str, domain_id: str) -> RoleDomain | None:
        stmt = select(RoleDomain).where(
            RoleDomain.role_id == role_id,
            RoleDomain.domain_id == domain_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_role_domain(self, role_id: str, domain_id: str) -> RoleDomain:
        existing = await self.get_role_domain(role_id, domain_id)
        if existing:
            return existing
        return await commit_or_conflict(self.session, RoleDomain(role_id=role_id, domain_id=domain_id))

    async def delete_role_domain(self, assoc: RoleDomain) -> None:
        await delete_and_commit(self.session, assoc)
