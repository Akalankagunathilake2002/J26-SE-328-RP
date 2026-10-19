from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Domain
from app.models.relationships import (
    SkillRelationship,
    CandidateSkillRelationship,
    SkillDomain,
    RoleDomain,
)
from app.repositories.core import ConflictError
from app.schemas.relationships import (
    SkillRelationshipCreate,
    SkillRelationshipUpdate,
    CandidateRelationshipCreate,
)


class SkillRelationshipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, relationship_id: str) -> SkillRelationship | None:
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
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                (SkillRelationship.relationship_id.ilike(term))
                | (SkillRelationship.source_skill_id.ilike(term))
                | (SkillRelationship.target_skill_id.ilike(term))
                | (SkillRelationship.relationship_type.ilike(term))
            )
        stmt = stmt.order_by(SkillRelationship.created_at.desc(), SkillRelationship.relationship_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def generate_next_relationship_id(self) -> str:
        # Find highest existing REL sequence number and increment.
        stmt = select(SkillRelationship.relationship_id).where(SkillRelationship.relationship_id.like("REL-%"))
        result = await self.session.execute(stmt)
        ids = result.scalars().all()
        max_num = 0
        for rid in ids:
            num_part = rid[4:]
            if num_part.isdigit():
                max_num = max(max_num, int(num_part))
        return f"REL-{max_num + 1:06d}"

    async def create(self, data: SkillRelationshipCreate, relationship_id: str | None = None) -> SkillRelationship:
        # Create with given ID or generate with retry loop against concurrent inserts.
        if relationship_id:
            rel = SkillRelationship(
                relationship_id=relationship_id,
                source_skill_id=data.source_skill_id,
                target_skill_id=data.target_skill_id,
                relationship_type=data.relationship_type,
                verification_status=data.verification_status,
                source_id=data.source_id,
                evidence_note=data.evidence_note,
            )
            self.session.add(rel)
            try:
                await self.session.commit()
                await self.session.refresh(rel)
                return rel
            except IntegrityError as exc:
                await self.session.rollback()
                raise ConflictError from exc
            except Exception:
                await self.session.rollback()
                raise

        max_attempts = 10
        for attempt in range(max_attempts):
            candidate_id = await self.generate_next_relationship_id()
            rel = SkillRelationship(
                relationship_id=candidate_id,
                source_skill_id=data.source_skill_id,
                target_skill_id=data.target_skill_id,
                relationship_type=data.relationship_type,
                verification_status=data.verification_status,
                source_id=data.source_id,
                evidence_note=data.evidence_note,
            )
            self.session.add(rel)
            try:
                await self.session.commit()
                await self.session.refresh(rel)
                return rel
            except IntegrityError as exc:
                await self.session.rollback()
                if attempt == max_attempts - 1:
                    raise ConflictError from exc
                continue
            except Exception:
                await self.session.rollback()
                raise

    async def update(self, rel: SkillRelationship, data: SkillRelationshipUpdate) -> SkillRelationship:
        if data.relationship_type is not None:
            rel.relationship_type = data.relationship_type
        if data.verification_status is not None:
            rel.verification_status = data.verification_status
        if data.source_id is not None:
            rel.source_id = data.source_id
        if data.evidence_note is not None:
            rel.evidence_note = data.evidence_note
        rel.updated_at = datetime.now(timezone.utc)

        self.session.add(rel)
        try:
            await self.session.commit()
            await self.session.refresh(rel)
            return rel
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError from exc
        except Exception:
            await self.session.rollback()
            raise

    async def delete(self, rel: SkillRelationship) -> None:
        try:
            await self.session.delete(rel)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise


class CandidateRelationshipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, candidate_relationship_id: str) -> CandidateSkillRelationship | None:
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
        stmt = stmt.order_by(CandidateSkillRelationship.created_at.desc(), CandidateSkillRelationship.candidate_relationship_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def generate_next_candidate_relationship_id(self) -> str:
        # Find the highest existing CR sequence number and increment it.
        stmt = select(CandidateSkillRelationship.candidate_relationship_id).where(
            CandidateSkillRelationship.candidate_relationship_id.like("CR-%")
        )
        result = await self.session.execute(stmt)
        ids = result.scalars().all()
        max_num = 0
        for cid in ids:
            num_part = cid[3:]
            if num_part.isdigit():
                max_num = max(max_num, int(num_part))
        return f"CR-{max_num + 1:06d}"

    async def create(self, data: CandidateRelationshipCreate) -> CandidateSkillRelationship:
        candidate_id = await self.generate_next_candidate_relationship_id()
        candidate = CandidateSkillRelationship(
            candidate_relationship_id=candidate_id,
            source_skill_id=data.source_skill_id,
            target_skill_id=data.target_skill_id,
            proposed_relationship_type=data.proposed_relationship_type,
            confidence_score=data.confidence_score,
            review_status="PENDING",
            source_id=data.source_id,
            review_note=data.review_note,
        )
        self.session.add(candidate)
        try:
            await self.session.commit()
            await self.session.refresh(candidate)
            return candidate
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError from exc
        except Exception:
            await self.session.rollback()
            raise

    async def reject(
        self, candidate: CandidateSkillRelationship, review_note: str | None
    ) -> CandidateSkillRelationship:
        candidate.review_status = "REJECTED"
        if review_note is not None:
            candidate.review_note = review_note
        candidate.reviewed_at = datetime.now(timezone.utc)
        self.session.add(candidate)
        try:
            await self.session.commit()
            await self.session.refresh(candidate)
            return candidate
        except Exception:
            await self.session.rollback()
            raise

    async def approve_and_create_canonical(
        self,
        candidate: CandidateSkillRelationship,
        canonical_relationship_id: str,
        review_note: str | None,
    ) -> tuple[CandidateSkillRelationship, SkillRelationship]:
        # Atomically promote the candidate relationship to canonical and mark it approved.
        canonical_rel = SkillRelationship(
            relationship_id=canonical_relationship_id,
            source_skill_id=candidate.source_skill_id,
            target_skill_id=candidate.target_skill_id,
            relationship_type=candidate.proposed_relationship_type,
            verification_status="VERIFIED",
            source_id=candidate.source_id,
            evidence_note=review_note or candidate.review_note,
        )
        candidate.review_status = "APPROVED"
        if review_note is not None:
            candidate.review_note = review_note
        candidate.reviewed_at = datetime.now(timezone.utc)

        self.session.add(canonical_rel)
        self.session.add(candidate)
        try:
            await self.session.commit()
            await self.session.refresh(candidate)
            await self.session.refresh(canonical_rel)
            return candidate, canonical_rel
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError from exc
        except Exception:
            await self.session.rollback()
            raise


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
        # Return existing association if present, otherwise create a new one.
        existing = await self.get_skill_domain(skill_id, domain_id)
        if existing:
            return existing
        assoc = SkillDomain(skill_id=skill_id, domain_id=domain_id)
        self.session.add(assoc)
        try:
            await self.session.commit()
            return assoc
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError from exc
        except Exception:
            await self.session.rollback()
            raise

    async def delete_skill_domain(self, assoc: SkillDomain) -> None:
        try:
            await self.session.delete(assoc)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

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
        # Return existing association if present, otherwise create a new one.
        existing = await self.get_role_domain(role_id, domain_id)
        if existing:
            return existing
        assoc = RoleDomain(role_id=role_id, domain_id=domain_id)
        self.session.add(assoc)
        try:
            await self.session.commit()
            return assoc
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError from exc
        except Exception:
            await self.session.rollback()
            raise

    async def delete_role_domain(self, assoc: RoleDomain) -> None:
        try:
            await self.session.delete(assoc)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
