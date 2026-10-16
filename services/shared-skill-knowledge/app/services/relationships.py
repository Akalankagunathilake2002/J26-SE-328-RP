from typing import Sequence
from fastapi import HTTPException
from app.models.core import Domain
from app.models.relationships import (
    SkillRelationship,
    CandidateSkillRelationship,
    SkillDomain,
    RoleDomain,
)
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository, ConflictError
from app.repositories.relationships import (
    SkillRelationshipRepository,
    CandidateRelationshipRepository,
    DomainAssociationRepository,
)
from app.schemas.relationships import (
    SkillRelationshipCreate,
    SkillRelationshipUpdate,
    CandidateRelationshipCreate,
    CandidateRelationshipReview,
)


class RelationshipService:
    def __init__(
        self,
        rel_repo: SkillRelationshipRepository,
        skill_repo: SkillRepository,
    ):
        self.rel_repo = rel_repo
        self.skill_repo = skill_repo

    async def list_relationships(
        self,
        limit: int = 100,
        offset: int = 0,
        source_skill_id: str | None = None,
        target_skill_id: str | None = None,
        relationship_type: str | None = None,
        verification_status: str | None = None,
    ) -> Sequence[SkillRelationship]:
        return await self.rel_repo.get_all(
            limit=limit,
            offset=offset,
            source_skill_id=source_skill_id,
            target_skill_id=target_skill_id,
            relationship_type=relationship_type,
            verification_status=verification_status,
        )

    async def get_relationship(self, relationship_id: str) -> SkillRelationship:
        rel = await self.rel_repo.get_by_id(relationship_id)
        if not rel:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return rel

    async def create_relationship(self, data: SkillRelationshipCreate) -> SkillRelationship:
        if data.source_skill_id == data.target_skill_id:
            raise HTTPException(status_code=422, detail="Source and target skills must be different")

        if not await self.skill_repo.get_by_id(data.source_skill_id):
            raise HTTPException(status_code=404, detail=f"Source skill '{data.source_skill_id}' not found")

        if not await self.skill_repo.get_by_id(data.target_skill_id):
            raise HTTPException(status_code=404, detail=f"Target skill '{data.target_skill_id}' not found")

        existing = await self.rel_repo.find_existing(
            data.source_skill_id, data.target_skill_id, data.relationship_type
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="A relationship with this source, target, and type already exists",
            )

        if data.relationship_id:
            if await self.rel_repo.get_by_id(data.relationship_id):
                raise HTTPException(
                    status_code=409,
                    detail=f"Relationship ID '{data.relationship_id}' already exists",
                )
            rel_id = data.relationship_id
        else:
            rel_id = await self.rel_repo.generate_next_relationship_id()

        try:
            return await self.rel_repo.create(data, relationship_id=rel_id)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Relationship conflicts with an existing record")

    async def update_relationship(
        self, relationship_id: str, data: SkillRelationshipUpdate
    ) -> SkillRelationship:
        rel = await self.get_relationship(relationship_id)

        if data.relationship_type is not None and data.relationship_type != rel.relationship_type:
            existing = await self.rel_repo.find_existing(
                rel.source_skill_id, rel.target_skill_id, data.relationship_type
            )
            if existing and existing.relationship_id != rel.relationship_id:
                raise HTTPException(
                    status_code=409,
                    detail="A relationship with this source, target, and type already exists",
                )

        try:
            return await self.rel_repo.update(rel, data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Relationship update conflicts with an existing record")

    async def delete_relationship(self, relationship_id: str) -> None:
        rel = await self.get_relationship(relationship_id)
        await self.rel_repo.delete(rel)


class CandidateRelationshipService:
    def __init__(
        self,
        candidate_repo: CandidateRelationshipRepository,
        rel_repo: SkillRelationshipRepository,
        skill_repo: SkillRepository,
    ):
        self.candidate_repo = candidate_repo
        self.rel_repo = rel_repo
        self.skill_repo = skill_repo

    async def list_candidates(
        self,
        limit: int = 100,
        offset: int = 0,
        source_skill_id: str | None = None,
        target_skill_id: str | None = None,
        proposed_relationship_type: str | None = None,
        review_status: str | None = None,
    ) -> Sequence[CandidateSkillRelationship]:
        return await self.candidate_repo.get_all(
            limit=limit,
            offset=offset,
            source_skill_id=source_skill_id,
            target_skill_id=target_skill_id,
            proposed_relationship_type=proposed_relationship_type,
            review_status=review_status,
        )

    async def get_candidate(self, candidate_relationship_id: str) -> CandidateSkillRelationship:
        cand = await self.candidate_repo.get_by_id(candidate_relationship_id)
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate relationship not found")
        return cand

    async def submit_candidate(
        self, data: CandidateRelationshipCreate
    ) -> CandidateSkillRelationship:
        if data.source_skill_id == data.target_skill_id:
            raise HTTPException(status_code=422, detail="Source and target skills must be different")

        if not await self.skill_repo.get_by_id(data.source_skill_id):
            raise HTTPException(status_code=404, detail=f"Source skill '{data.source_skill_id}' not found")

        if not await self.skill_repo.get_by_id(data.target_skill_id):
            raise HTTPException(status_code=404, detail=f"Target skill '{data.target_skill_id}' not found")

        existing_canonical = await self.rel_repo.find_existing(
            data.source_skill_id, data.target_skill_id, data.proposed_relationship_type
        )
        if existing_canonical:
            raise HTTPException(
                status_code=409,
                detail="A canonical relationship of this type between these skills already exists",
            )

        existing_pending = await self.candidate_repo.get_pending_duplicate(
            data.source_skill_id, data.target_skill_id, data.proposed_relationship_type
        )
        if existing_pending:
            raise HTTPException(
                status_code=409,
                detail=f"A pending candidate relationship already exists for this pair and relationship type (ID: {existing_pending.candidate_relationship_id})",
            )

        try:
            return await self.candidate_repo.create(data)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Candidate relationship conflicts with an existing record")

    async def review_candidate(
        self, candidate_relationship_id: str, review_data: CandidateRelationshipReview
    ) -> CandidateSkillRelationship:
        candidate = await self.get_candidate(candidate_relationship_id)

        if candidate.review_status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Candidate relationship has already been reviewed (current status: {candidate.review_status})",
            )

        norm_action = review_data.action.upper()
        if norm_action in ("REJECT", "REJECTED"):
            return await self.candidate_repo.reject(candidate, review_note=review_data.review_note)

        if norm_action in ("APPROVE", "APPROVED"):
            existing_canonical = await self.rel_repo.find_existing(
                candidate.source_skill_id,
                candidate.target_skill_id,
                candidate.proposed_relationship_type,
            )
            if existing_canonical:
                raise HTTPException(
                    status_code=409,
                    detail="A canonical relationship of this type between these skills already exists",
                )

            next_rel_id = await self.rel_repo.generate_next_relationship_id()
            try:
                cand, _ = await self.candidate_repo.approve_and_create_canonical(
                    candidate=candidate,
                    canonical_relationship_id=next_rel_id,
                    review_note=review_data.review_note,
                )
                return cand
            except ConflictError:
                raise HTTPException(
                    status_code=409,
                    detail="Failed to approve candidate: canonical relationship conflicts with an existing record",
                )

        raise HTTPException(
            status_code=422,
            detail=f"Invalid review action '{review_data.action}'. Allowed actions: 'APPROVED', 'REJECTED'",
        )


class DomainAssociationService:
    def __init__(
        self,
        assoc_repo: DomainAssociationRepository,
        skill_repo: SkillRepository,
        role_repo: RoleRepository,
        domain_repo: DomainRepository,
    ):
        self.assoc_repo = assoc_repo
        self.skill_repo = skill_repo
        self.role_repo = role_repo
        self.domain_repo = domain_repo

    async def list_skill_domains(self, skill_id: str) -> Sequence[Domain]:
        if not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        return await self.assoc_repo.get_skill_domains(skill_id)

    async def associate_skill_domain(self, skill_id: str, domain_id: str) -> SkillDomain:
        if not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        if not await self.domain_repo.get_by_id(domain_id):
            raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")
        return await self.assoc_repo.add_skill_domain(skill_id, domain_id)

    async def remove_skill_domain(self, skill_id: str, domain_id: str) -> None:
        if not await self.skill_repo.get_by_id(skill_id):
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        assoc = await self.assoc_repo.get_skill_domain(skill_id, domain_id)
        if not assoc:
            raise HTTPException(
                status_code=404,
                detail=f"Association between skill '{skill_id}' and domain '{domain_id}' not found",
            )
        await self.assoc_repo.delete_skill_domain(assoc)

    async def list_role_domains(self, role_id: str) -> Sequence[Domain]:
        if not await self.role_repo.get_by_id(role_id):
            raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
        return await self.assoc_repo.get_role_domains(role_id)

    async def associate_role_domain(self, role_id: str, domain_id: str) -> RoleDomain:
        if not await self.role_repo.get_by_id(role_id):
            raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
        if not await self.domain_repo.get_by_id(domain_id):
            raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")
        return await self.assoc_repo.add_role_domain(role_id, domain_id)

    async def remove_role_domain(self, role_id: str, domain_id: str) -> None:
        if not await self.role_repo.get_by_id(role_id):
            raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
        assoc = await self.assoc_repo.get_role_domain(role_id, domain_id)
        if not assoc:
            raise HTTPException(
                status_code=404,
                detail=f"Association between role '{role_id}' and domain '{domain_id}' not found",
            )
        await self.assoc_repo.delete_role_domain(assoc)
