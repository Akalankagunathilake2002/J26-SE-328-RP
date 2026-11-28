from datetime import datetime, timezone
from typing import Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidates import CandidateEntity
from app.models.core import Skill, Role
from app.repositories.base import ConflictError, commit_or_conflict, generate_prefixed_sequence_id
from app.schemas.candidates import CandidateEntityCreate


class CandidateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, candidate_entity_id: uuid.UUID) -> CandidateEntity | None:
        return await self.session.get(CandidateEntity, candidate_entity_id)

    async def get_pending_by_normalized_name(
        self, entity_type: str, normalized_name: str
    ) -> CandidateEntity | None:
        stmt = select(CandidateEntity).where(
            CandidateEntity.entity_type == entity_type,
            CandidateEntity.normalized_name == normalized_name,
            CandidateEntity.review_status == "PENDING",
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
        stmt = (
            stmt.order_by(CandidateEntity.created_at.desc(), CandidateEntity.candidate_entity_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: CandidateEntityCreate, normalized_name: str) -> CandidateEntity:
        candidate = CandidateEntity(
            candidate_entity_id=uuid.uuid4(),
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
        return await commit_or_conflict(self.session, candidate, refresh_targets=(candidate,))

    async def approve_skill(
        self,
        candidate: CandidateEntity,
        skill_type: str,
        skill_nature: str | None,
        review_note: str | None,
        reviewed_by: uuid.UUID,
    ) -> CandidateEntity:
        # Promote the candidate into an active canonical skill with collision retries.
        now = datetime.now(timezone.utc)
        for attempt in range(10):
            skill_id = await generate_prefixed_sequence_id(
                self.session, Skill.skill_id, "SK-", offset=attempt
            )
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
            candidate.reviewed_at = now
            candidate.reviewed_by = reviewed_by
            try:
                await commit_or_conflict(self.session, skill, candidate, refresh_targets=(candidate,))
                return candidate
            except ConflictError:
                if attempt == 9:
                    raise ConflictError("Could not safely generate unique skill ID after retries")
                continue
        raise ConflictError("Could not safely generate unique skill ID after retries")

    async def approve_role(
        self,
        candidate: CandidateEntity,
        review_note: str | None,
        reviewed_by: uuid.UUID,
    ) -> CandidateEntity:
        # Promote the candidate into an active canonical role with collision retries.
        now = datetime.now(timezone.utc)
        for attempt in range(10):
            role_id = await generate_prefixed_sequence_id(
                self.session, Role.role_id, "RL-", offset=attempt
            )
            role = Role(
                role_id=role_id,
                preferred_name=candidate.submitted_name,
                description=candidate.description,
                status="ACTIVE",
            )
            candidate.review_status = "APPROVED"
            candidate.matched_entity_id = role_id
            candidate.review_note = review_note
            candidate.reviewed_at = now
            candidate.reviewed_by = reviewed_by
            try:
                await commit_or_conflict(self.session, role, candidate, refresh_targets=(candidate,))
                return candidate
            except ConflictError:
                if attempt == 9:
                    raise ConflictError("Could not safely generate unique role ID after retries")
                continue
        raise ConflictError("Could not safely generate unique role ID after retries")

    async def reject(
        self,
        candidate: CandidateEntity,
        review_note: str | None,
        reviewed_by: uuid.UUID,
    ) -> CandidateEntity:
        candidate.review_status = "REJECTED"
        candidate.review_note = review_note
        candidate.reviewed_at = datetime.now(timezone.utc)
        candidate.reviewed_by = reviewed_by
        return await commit_or_conflict(self.session, candidate, refresh_targets=(candidate,))

    async def merge_as_alias(
        self,
        candidate: CandidateEntity,
        alias_obj,
        target_entity_id: str,
        review_note: str | None,
        reviewed_by: uuid.UUID,
        retire_entity: Skill | Role | None = None,
    ):
        now = datetime.now(timezone.utc)
        candidate.review_status = "APPROVED"
        candidate.matched_entity_id = target_entity_id
        if review_note is not None:
            candidate.review_note = review_note
        candidate.reviewed_at = now
        candidate.reviewed_by = reviewed_by

        objs = [alias_obj, candidate]
        if retire_entity is not None:
            retire_entity.status = "RETIRED"
            retire_entity.updated_at = now
            objs.append(retire_entity)

        await commit_or_conflict(
            self.session,
            *objs,
            refresh_targets=(candidate, alias_obj),
        )
        return candidate, alias_obj
