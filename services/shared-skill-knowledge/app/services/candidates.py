from typing import Sequence
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Skill, Role
from app.models.aliases import SkillAlias, RoleAlias
from app.models.candidates import CandidateEntity
from app.repositories.candidates import CandidateRepository
from app.schemas.candidates import CandidateEntityCreate, CandidateEntityReview
from app.services.normalization import normalize_name

class CandidateService:
    def __init__(self, session: AsyncSession, candidate_repo: CandidateRepository):
        self.session = session
        self.candidate_repo = candidate_repo

    async def list_candidates(
        self,
        limit: int = 100,
        offset: int = 0,
        entity_type: str | None = None,
        review_status: str | None = None,
    ) -> Sequence[CandidateEntity]:
        return await self.candidate_repo.get_all(
            limit=limit,
            offset=offset,
            entity_type=entity_type,
            review_status=review_status,
        )

    async def get_candidate(self, candidate_entity_id: str) -> CandidateEntity:
        candidate = await self.candidate_repo.get_by_id(candidate_entity_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate entity not found")
        return candidate

    async def create_candidate(self, data: CandidateEntityCreate) -> CandidateEntity:
        norm = normalize_name(data.submitted_name)

        if data.entity_type == "SKILL":
            canonical_skills = (await self.session.execute(select(Skill))).scalars().all()
            for skill in canonical_skills:
                if normalize_name(skill.preferred_name) == norm:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A canonical skill already exists for '{data.submitted_name}' (ID: {skill.skill_id})"
                    )

            alias_result = await self.session.execute(
                select(SkillAlias).where(
                    SkillAlias.normalized_alias == norm,
                    SkillAlias.verification_status == "VERIFIED",
                )
            )
            existing_alias = alias_result.scalars().first()
            if existing_alias:
                raise HTTPException(
                    status_code=409,
                    detail=f"A verified skill alias already exists for '{data.submitted_name}' (Skill ID: {existing_alias.skill_id})"
                )

        elif data.entity_type == "ROLE":
            canonical_roles = (await self.session.execute(select(Role))).scalars().all()
            for role in canonical_roles:
                if normalize_name(role.preferred_name) == norm:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A canonical role already exists for '{data.submitted_name}' (ID: {role.role_id})"
                    )

            alias_result = await self.session.execute(
                select(RoleAlias).where(
                    RoleAlias.normalized_alias == norm,
                    RoleAlias.verification_status == "VERIFIED",
                )
            )
            existing_alias = alias_result.scalars().first()
            if existing_alias:
                raise HTTPException(
                    status_code=409,
                    detail=f"A verified role alias already exists for '{data.submitted_name}' (Role ID: {existing_alias.role_id})"
                )

        existing_pending = await self.candidate_repo.get_pending_by_normalized_name(
            entity_type=data.entity_type,
            normalized_name=norm,
        )
        if existing_pending:
            raise HTTPException(
                status_code=409,
                detail=f"A pending candidate already exists for '{data.submitted_name}' (Candidate ID: {existing_pending.candidate_entity_id})"
            )

        return await self.candidate_repo.create(data, normalized_name=norm)

    async def review_candidate(
        self, candidate_entity_id: str, review_data: CandidateEntityReview
    ) -> CandidateEntity:
        candidate = await self.get_candidate(candidate_entity_id)

        if candidate.review_status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Candidate has already been reviewed (current status: {candidate.review_status})"
            )

        if review_data.action == "REJECT":
            return await self.candidate_repo.reject(candidate, review_note=review_data.review_note)

        if review_data.action == "APPROVE":
            if candidate.entity_type == "SKILL":
                skill_type = review_data.skill_type or candidate.proposed_skill_type
                if not skill_type:
                    raise HTTPException(
                        status_code=422,
                        detail="skill_type is required to approve a skill candidate"
                    )
                skill_nature = review_data.skill_nature or candidate.proposed_skill_nature
                return await self.candidate_repo.approve_skill(
                    candidate=candidate,
                    skill_type=skill_type,
                    skill_nature=skill_nature,
                    review_note=review_data.review_note,
                )
            elif candidate.entity_type == "ROLE":
                return await self.candidate_repo.approve_role(
                    candidate=candidate,
                    review_note=review_data.review_note,
                )
            else:
                raise HTTPException(status_code=422, detail=f"Unsupported entity type: {candidate.entity_type}")
