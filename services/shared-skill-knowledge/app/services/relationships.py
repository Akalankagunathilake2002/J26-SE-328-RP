from typing import Sequence
import uuid
from fastapi import HTTPException

from app.core.security import ROLE_ADMIN, ROLE_HR
from app.models.core import Domain
from app.models.relationships import (
    SkillRelationship,
    CandidateSkillRelationship,
    SkillDomain,
    RoleDomain,
)
from app.repositories.base import ConflictError
from app.repositories.core import DomainRepository, SkillRepository, RoleRepository
from app.repositories.relationships import (
    SkillRelationshipRepository,
    CandidateRelationshipRepository,
    DomainAssociationRepository,
)
from app.repositories.sources import KnowledgeSourceRepository
from app.schemas.relationships import (
    SkillRelationshipCreate,
    SkillRelationshipUpdate,
    CandidateRelationshipCreate,
    CandidateRelationshipReview,
)

_ALLOWED_REL_TYPES = frozenset(
    {
        "EQUIVALENT_TO",
        "BROADER_THAN",
        "NARROWER_THAN",
        "PART_OF",
        "PREREQUISITE_OF",
        "RELATED_TO",
    }
)


class RelationshipService:
    def __init__(
        self,
        rel_repo: SkillRelationshipRepository,
        skill_repo: SkillRepository,
        source_repo: KnowledgeSourceRepository,
    ):
        self.rel_repo = rel_repo
        self.skill_repo = skill_repo
        self.source_repo = source_repo

    async def list_relationships(
        self,
        *,
        caller_role: str,
        limit: int = 100,
        offset: int = 0,
        source_skill_id: str | None = None,
        target_skill_id: str | None = None,
        relationship_type: str | None = None,
        verification_status: str | None = None,
        search: str | None = None,
    ) -> Sequence[SkillRelationship]:
        effective_status = verification_status
        if caller_role not in (ROLE_HR, ROLE_ADMIN):
            if verification_status and verification_status != "VERIFIED":
                raise HTTPException(
                    status_code=403,
                    detail="Only HR or ADMIN users may access unverified relationships",
                )
            effective_status = "VERIFIED"

        return await self.rel_repo.get_all(
            limit=limit,
            offset=offset,
            source_skill_id=source_skill_id,
            target_skill_id=target_skill_id,
            relationship_type=relationship_type,
            verification_status=effective_status,
            search=search,
        )

    async def get_relationship(
        self, relationship_id: uuid.UUID, *, caller_role: str | None = None
    ) -> SkillRelationship:
        rel = await self.rel_repo.get_by_id(relationship_id)
        if not rel:
            raise HTTPException(status_code=404, detail="Relationship not found")
        if caller_role and caller_role not in (ROLE_HR, ROLE_ADMIN) and rel.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=403,
                detail="Only HR or ADMIN users may access unverified relationships",
            )
        return rel

    async def create_relationship(
        self, data: SkillRelationshipCreate, *, reviewer_id: uuid.UUID
    ) -> SkillRelationship:
        if data.source_skill_id == data.target_skill_id:
            raise HTTPException(status_code=422, detail="Source and target skills must be different")

        if not await self.skill_repo.get_by_id(data.source_skill_id):
            raise HTTPException(status_code=404, detail=f"Source skill '{data.source_skill_id}' not found")

        if not await self.skill_repo.get_by_id(data.target_skill_id):
            raise HTTPException(status_code=404, detail=f"Target skill '{data.target_skill_id}' not found")

        if data.source_id is not None and not await self.source_repo.get_by_id(data.source_id):
            raise HTTPException(status_code=404, detail=f"Knowledge source '{data.source_id}' not found")

        existing = await self.rel_repo.find_existing(
            data.source_skill_id, data.target_skill_id, data.relationship_type
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="A relationship with this source, target, and type already exists",
            )

        if data.relationship_id and await self.rel_repo.get_by_id(data.relationship_id):
            raise HTTPException(
                status_code=409,
                detail=f"Relationship ID '{data.relationship_id}' already exists",
            )

        try:
            return await self.rel_repo.create(
                data,
                reviewed_by=reviewer_id,
                relationship_id=data.relationship_id,
            )
        except ConflictError:
            raise HTTPException(status_code=409, detail="Relationship conflicts with an existing record")

    async def update_relationship(
        self, relationship_id: uuid.UUID, data: SkillRelationshipUpdate, *, reviewer_id: uuid.UUID
    ) -> SkillRelationship:
        rel = await self.get_relationship(relationship_id)

        if data.source_id is not None and not await self.source_repo.get_by_id(data.source_id):
            raise HTTPException(status_code=404, detail=f"Knowledge source '{data.source_id}' not found")

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
            return await self.rel_repo.update(rel, data, reviewed_by=reviewer_id)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Relationship update conflicts with an existing record")

    async def delete_relationship(self, relationship_id: uuid.UUID) -> None:
        rel = await self.get_relationship(relationship_id)
        await self.rel_repo.delete(rel)


class CandidateRelationshipService:
    def __init__(
        self,
        candidate_repo: CandidateRelationshipRepository,
        rel_repo: SkillRelationshipRepository,
        skill_repo: SkillRepository,
        source_repo: KnowledgeSourceRepository,
    ):
        self.candidate_repo = candidate_repo
        self.rel_repo = rel_repo
        self.skill_repo = skill_repo
        self.source_repo = source_repo

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

    async def get_candidate(self, candidate_relationship_id: uuid.UUID) -> CandidateSkillRelationship:
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

        if data.source_id is not None and not await self.source_repo.get_by_id(data.source_id):
            raise HTTPException(status_code=404, detail=f"Knowledge source '{data.source_id}' not found")

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
        self,
        candidate_relationship_id: uuid.UUID,
        review_data: CandidateRelationshipReview,
        reviewer_id: uuid.UUID,
    ) -> CandidateSkillRelationship:
        candidate = await self.get_candidate(candidate_relationship_id)

        if candidate.review_status != "PENDING":
            raise HTTPException(
                status_code=409,
                detail=f"Candidate relationship has already been reviewed (current status: {candidate.review_status})",
            )

        norm_action = review_data.action.upper()
        if norm_action in ("REJECT", "REJECTED"):
            return await self.candidate_repo.reject(
                candidate,
                review_note=review_data.review_note,
                reviewed_by=reviewer_id,
            )

        if norm_action in ("APPROVE", "APPROVED"):
            effective_source_id = (review_data.source_skill_id or candidate.source_skill_id).strip()
            effective_target_id = (review_data.target_skill_id or candidate.target_skill_id).strip()
            effective_rel_type = (review_data.relationship_type or candidate.proposed_relationship_type).strip()

            if effective_source_id == effective_target_id:
                raise HTTPException(status_code=422, detail="Source and target skills must be different")

            if effective_rel_type not in _ALLOWED_REL_TYPES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid relationship type '{effective_rel_type}'. Allowed types: {', '.join(sorted(_ALLOWED_REL_TYPES))}",
                )

            if not await self.skill_repo.get_by_id(effective_source_id):
                raise HTTPException(status_code=404, detail=f"Source skill '{effective_source_id}' not found")

            if not await self.skill_repo.get_by_id(effective_target_id):
                raise HTTPException(status_code=404, detail=f"Target skill '{effective_target_id}' not found")

            existing_canonical = await self.rel_repo.find_existing(
                effective_source_id,
                effective_target_id,
                effective_rel_type,
            )
            if existing_canonical:
                raise HTTPException(
                    status_code=409,
                    detail="A canonical relationship of this type between these skills already exists",
                )

            effective_evidence_desc = (
                review_data.evidence_description
                if review_data.evidence_description is not None
                else candidate.evidence_description
            )
            effective_evidence_url = (
                review_data.evidence_url
                if review_data.evidence_url is not None
                else candidate.evidence_url
            )

            try:
                cand, canonical_rel = await self.candidate_repo.approve_and_create_canonical(
                    candidate=candidate,
                    source_skill_id=effective_source_id,
                    target_skill_id=effective_target_id,
                    relationship_type=effective_rel_type,
                    review_note=review_data.review_note,
                    evidence_description=effective_evidence_desc,
                    evidence_url=effective_evidence_url,
                    reviewed_by=reviewer_id,
                )
                setattr(cand, "canonical_relationship", canonical_rel)
                return cand
            except ConflictError:
                raise HTTPException(
                    status_code=409,
                    detail="Failed to approve candidate: canonical relationship conflicts with an existing record",
                )

        raise HTTPException(
            status_code=422,
            detail=f"Invalid review action '{review_data.action}'. Allowed actions: 'APPROVE', 'REJECT'",
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
        try:
            return await self.assoc_repo.add_skill_domain(skill_id, domain_id)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Skill-domain association conflict")

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
        try:
            return await self.assoc_repo.add_role_domain(role_id, domain_id)
        except ConflictError:
            raise HTTPException(status_code=409, detail="Role-domain association conflict")

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
