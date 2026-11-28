from typing import Sequence
import uuid
from fastapi import HTTPException

from app.core.text import normalize_name
from app.models.aliases import RoleAlias, SkillAlias
from app.models.candidates import CandidateEntity
from app.repositories.aliases import RoleAliasRepository, SkillAliasRepository
from app.repositories.base import ConflictError
from app.repositories.candidates import CandidateRepository
from app.repositories.core import RoleRepository, SkillRepository
from app.repositories.sources import KnowledgeSourceRepository
from app.schemas.candidates import (
    CandidateEntityCreate,
    CandidateEntityReview,
    CandidateMergeAsAliasRequest,
    CandidateMergeAsAliasResponse,
)


class CandidateService:
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        skill_repo: SkillRepository,
        role_repo: RoleRepository,
        skill_alias_repo: SkillAliasRepository,
        role_alias_repo: RoleAliasRepository,
        source_repo: KnowledgeSourceRepository,
    ):
        self.candidate_repo = candidate_repo
        self.skill_repo = skill_repo
        self.role_repo = role_repo
        self.skill_alias_repo = skill_alias_repo
        self.role_alias_repo = role_alias_repo
        self.source_repo = source_repo

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

    async def get_candidate(self, candidate_entity_id: uuid.UUID) -> CandidateEntity:
        candidate = await self.candidate_repo.get_by_id(candidate_entity_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate entity not found")
        return candidate

    async def create_candidate(self, data: CandidateEntityCreate) -> CandidateEntity:
        norm = normalize_name(data.submitted_name)

        if data.entity_type == "SKILL":
            existing_skill = await self.skill_repo.find_by_normalized_name(norm)
            if existing_skill:
                raise HTTPException(
                    status_code=409,
                    detail=f"A canonical skill already exists for '{data.submitted_name}' (ID: {existing_skill.skill_id})",
                )
            existing_alias = await self.skill_alias_repo.find_verified_by_normalized(norm)
            if existing_alias:
                raise HTTPException(
                    status_code=409,
                    detail=f"A verified skill alias already exists for '{data.submitted_name}' (Skill ID: {existing_alias.skill_id})",
                )
        elif data.entity_type == "ROLE":
            existing_role = await self.role_repo.find_by_normalized_name(norm)
            if existing_role:
                raise HTTPException(
                    status_code=409,
                    detail=f"A canonical role already exists for '{data.submitted_name}' (ID: {existing_role.role_id})",
                )
            existing_alias = await self.role_alias_repo.find_verified_by_normalized(norm)
            if existing_alias:
                raise HTTPException(
                    status_code=409,
                    detail=f"A verified role alias already exists for '{data.submitted_name}' (Role ID: {existing_alias.role_id})",
                )

        existing_pending = await self.candidate_repo.get_pending_by_normalized_name(
            entity_type=data.entity_type,
            normalized_name=norm,
        )
        if existing_pending:
            raise HTTPException(
                status_code=409,
                detail=f"A pending candidate already exists for '{data.submitted_name}' (Candidate ID: {existing_pending.candidate_entity_id})",
            )

        try:
            return await self.candidate_repo.create(data, normalized_name=norm)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Candidate conflicts with an existing record")

    async def review_candidate(
        self,
        candidate_entity_id: uuid.UUID,
        review_data: CandidateEntityReview,
        reviewer_id: uuid.UUID,
    ) -> CandidateEntity:
        candidate = await self.get_candidate(candidate_entity_id)

        if candidate.review_status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Candidate has already been reviewed (current status: {candidate.review_status})",
            )

        if review_data.action == "REJECT":
            return await self.candidate_repo.reject(
                candidate,
                review_note=review_data.review_note,
                reviewed_by=reviewer_id,
            )

        if review_data.action == "APPROVE":
            if candidate.entity_type == "SKILL":
                existing_skill = await self.skill_repo.find_by_normalized_name(candidate.normalized_name)
                if existing_skill:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A canonical skill already exists for '{candidate.submitted_name}' (ID: {existing_skill.skill_id})",
                    )
                skill_type = review_data.skill_type or candidate.proposed_skill_type
                if not skill_type:
                    raise HTTPException(
                        status_code=422,
                        detail="skill_type is required to approve a skill candidate",
                    )
                skill_nature = review_data.skill_nature or candidate.proposed_skill_nature
                try:
                    return await self.candidate_repo.approve_skill(
                        candidate=candidate,
                        skill_type=skill_type,
                        skill_nature=skill_nature,
                        review_note=review_data.review_note,
                        reviewed_by=reviewer_id,
                    )
                except ConflictError:
                    raise HTTPException(status_code=409, detail="Candidate approval conflicts with an existing skill")

            elif candidate.entity_type == "ROLE":
                existing_role = await self.role_repo.find_by_normalized_name(candidate.normalized_name)
                if existing_role:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A canonical role already exists for '{candidate.submitted_name}' (ID: {existing_role.role_id})",
                    )
                try:
                    return await self.candidate_repo.approve_role(
                        candidate=candidate,
                        review_note=review_data.review_note,
                        reviewed_by=reviewer_id,
                    )
                except ConflictError:
                    raise HTTPException(status_code=409, detail="Candidate approval conflicts with an existing role")

        raise HTTPException(status_code=422, detail=f"Unsupported entity type: {candidate.entity_type}")

    async def merge_candidate_as_alias(
        self,
        candidate_entity_id: uuid.UUID,
        data: CandidateMergeAsAliasRequest,
        reviewer_id: uuid.UUID,
    ) -> CandidateMergeAsAliasResponse:
        candidate = await self.get_candidate(candidate_entity_id)

        if candidate.review_status == "REJECTED":
            raise HTTPException(
                status_code=409,
                detail="Rejected candidate cannot be merged as an alias",
            )

        if data.source_id is not None and not await self.source_repo.get_by_id(data.source_id):
            raise HTTPException(status_code=404, detail=f"Knowledge source '{data.source_id}' not found")

        alias_text = (data.alias_text or candidate.submitted_name).strip()
        norm_alias = normalize_name(alias_text)

        if candidate.entity_type == "SKILL":
            target = await self.skill_repo.get_by_id(data.target_entity_id)
            if not target:
                raise HTTPException(status_code=404, detail=f"Target skill '{data.target_entity_id}' not found")
            dup_same = await self.skill_alias_repo.find_by_entity_and_normalized(
                data.target_entity_id, norm_alias
            )
            if dup_same:
                raise HTTPException(
                    status_code=409,
                    detail=f"Alias '{alias_text}' already exists for skill '{data.target_entity_id}'",
                )
            if data.verification_status == "VERIFIED":
                dup_verified = await self.skill_alias_repo.find_verified_by_normalized(norm_alias)
                if dup_verified:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A verified skill alias for '{alias_text}' already maps to '{dup_verified.skill_id}'",
                    )

            retire_entity = None
            if (
                data.retire_previous_canonical
                and candidate.matched_entity_id
                and candidate.matched_entity_id != data.target_entity_id
            ):
                retire_entity = await self.skill_repo.get_by_id(candidate.matched_entity_id)

            alias_obj = SkillAlias(
                alias_id=uuid.uuid4(),
                skill_id=data.target_entity_id,
                alias_text=alias_text,
                normalized_alias=norm_alias,
                source_id=data.source_id,
                verification_status=data.verification_status,
            )
        else:
            target = await self.role_repo.get_by_id(data.target_entity_id)
            if not target:
                raise HTTPException(status_code=404, detail=f"Target role '{data.target_entity_id}' not found")
            dup_same = await self.role_alias_repo.find_by_entity_and_normalized(
                data.target_entity_id, norm_alias
            )
            if dup_same:
                raise HTTPException(
                    status_code=409,
                    detail=f"Alias '{alias_text}' already exists for role '{data.target_entity_id}'",
                )
            if data.verification_status == "VERIFIED":
                dup_verified = await self.role_alias_repo.find_verified_by_normalized(norm_alias)
                if dup_verified:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A verified role alias for '{alias_text}' already maps to '{dup_verified.role_id}'",
                    )

            retire_entity = None
            if (
                data.retire_previous_canonical
                and candidate.matched_entity_id
                and candidate.matched_entity_id != data.target_entity_id
            ):
                retire_entity = await self.role_repo.get_by_id(candidate.matched_entity_id)

            alias_obj = RoleAlias(
                alias_id=uuid.uuid4(),
                role_id=data.target_entity_id,
                alias_text=alias_text,
                normalized_alias=norm_alias,
                source_id=data.source_id,
                verification_status=data.verification_status,
            )

        try:
            updated_candidate, created_alias = await self.candidate_repo.merge_as_alias(
                candidate=candidate,
                alias_obj=alias_obj,
                target_entity_id=data.target_entity_id,
                review_note=data.review_note,
                reviewed_by=reviewer_id,
                retire_entity=retire_entity,
            )
        except ConflictError:
            raise HTTPException(status_code=409, detail="Merge as alias conflicts with an existing record")

        retired_id = None
        if retire_entity is not None:
            retired_id = getattr(retire_entity, "skill_id", None) or getattr(retire_entity, "role_id", None)

        return CandidateMergeAsAliasResponse(
            candidate=updated_candidate,
            alias_id=created_alias.alias_id,
            target_entity_id=data.target_entity_id,
            alias_text=created_alias.alias_text,
            normalized_alias=created_alias.normalized_alias,
            verification_status=created_alias.verification_status,
            retired_entity_id=retired_id,
        )
