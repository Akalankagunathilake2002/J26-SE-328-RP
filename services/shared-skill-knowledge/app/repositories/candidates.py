from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.candidates import CandidateEntity
from app.models.core import Skill, Role
from app.schemas.candidates import CandidateEntityCreate

class CandidateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, candidate_entity_id: str) -> CandidateEntity | None:
        return await self.session.get(CandidateEntity, candidate_entity_id)

    async def get_pending_by_normalized_name(
        self, entity_type: str, normalized_name: str
    ) -> CandidateEntity | None:
        stmt = (
            select(CandidateEntity)
            .where(
                CandidateEntity.entity_type == entity_type,
                CandidateEntity.normalized_name == normalized_name,
                CandidateEntity.review_status == "PENDING",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        entity_type: str | None = None,
        review_status: str | None = None,
    ) -> Sequence[CandidateEntity]:
        stmt = select(CandidateEntity)
        if entity_type:
            stmt = stmt.where(CandidateEntity.entity_type == entity_type)
        if review_status:
            stmt = stmt.where(CandidateEntity.review_status == review_status)
        stmt = stmt.order_by(CandidateEntity.created_at.desc(), CandidateEntity.candidate_entity_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _generate_next_candidate_id(self) -> str:
        # Find the highest existing CE sequence number and increment it.
        stmt = select(CandidateEntity.candidate_entity_id).where(CandidateEntity.candidate_entity_id.like("CE-%"))
        result = await self.session.execute(stmt)
        ids = result.scalars().all()
        max_num = 0
        for cid in ids:
            num_part = cid[3:]
            if num_part.isdigit():
                max_num = max(max_num, int(num_part))
        return f"CE-{max_num + 1:06d}"

    async def _generate_next_skill_id(self) -> str:
        # Find the highest existing SK sequence number and increment it.
        stmt = select(Skill.skill_id).where(Skill.skill_id.like("SK-%"))
        result = await self.session.execute(stmt)
        ids = result.scalars().all()
        max_num = 0
        for sid in ids:
            num_part = sid[3:]
            if num_part.isdigit():
                max_num = max(max_num, int(num_part))
        return f"SK-{max_num + 1:06d}"

    async def _generate_next_role_id(self) -> str:
        # Find the highest existing RL sequence number and increment it.
        stmt = select(Role.role_id).where(Role.role_id.like("RL-%"))
        result = await self.session.execute(stmt)
        ids = result.scalars().all()
        max_num = 0
        for rid in ids:
            num_part = rid[3:]
            if num_part.isdigit():
                max_num = max(max_num, int(num_part))
        return f"RL-{max_num + 1:06d}"

    async def create(self, data: CandidateEntityCreate, normalized_name: str) -> CandidateEntity:
        candidate_id = await self._generate_next_candidate_id()
        candidate = CandidateEntity(
            candidate_entity_id=candidate_id,
            entity_type=data.entity_type,
            submitted_name=data.submitted_name,
            normalized_name=normalized_name,
            description=data.description,
            proposed_skill_type=data.proposed_skill_type,
            proposed_skill_nature=data.proposed_skill_nature,
            source_component=data.source_component,
            source_reference=data.source_reference,
            review_status="PENDING",
        )
        self.session.add(candidate)
        try:
            await self.session.commit()
            await self.session.refresh(candidate)
            return candidate
        except Exception:
            await self.session.rollback()
            raise

    async def approve_skill(
        self, candidate: CandidateEntity, skill_type: str, skill_nature: str | None, review_note: str | None
    ) -> CandidateEntity:
        # Promote the candidate into an active canonical skill and link its new ID.
        skill_id = await self._generate_next_skill_id()
        skill = Skill(
            skill_id=skill_id,
            preferred_name=candidate.submitted_name,
            description=candidate.description,
            skill_type=skill_type,
            skill_nature=skill_nature,
            status="ACTIVE",
        )
        candidate.review_status = "APPROVED"
        candidate.matched_entity_id = skill_id
        candidate.review_note = review_note
        candidate.reviewed_at = datetime.now(timezone.utc)

        self.session.add(skill)
        self.session.add(candidate)
        try:
            await self.session.commit()
            await self.session.refresh(candidate)
            return candidate
        except Exception:
            await self.session.rollback()
            raise

    async def approve_role(
        self, candidate: CandidateEntity, review_note: str | None
    ) -> CandidateEntity:
        # Promote the candidate into an active canonical role and link its new ID.
        role_id = await self._generate_next_role_id()
        role = Role(
            role_id=role_id,
            preferred_name=candidate.submitted_name,
            description=candidate.description,
            status="ACTIVE",
        )
        candidate.review_status = "APPROVED"
        candidate.matched_entity_id = role_id
        candidate.review_note = review_note
        candidate.reviewed_at = datetime.now(timezone.utc)

        self.session.add(role)
        self.session.add(candidate)
        try:
            await self.session.commit()
            await self.session.refresh(candidate)
            return candidate
        except Exception:
            await self.session.rollback()
            raise

    async def reject(self, candidate: CandidateEntity, review_note: str | None) -> CandidateEntity:
        candidate.review_status = "REJECTED"
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
