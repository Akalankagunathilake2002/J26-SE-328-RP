from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.text import normalize_name
from app.models.core import Domain, Skill, Role
from app.models.relationships import SkillDomain, RoleDomain
from app.repositories.base import ConflictError, commit_or_conflict, generate_prefixed_sequence_id
from app.schemas.core import DomainCreate, DomainUpdate, SkillCreate, SkillUpdate, RoleCreate, RoleUpdate


class DomainRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, status: str | None = None) -> Sequence[Domain]:
        stmt = select(Domain)
        if status:
            stmt = stmt.where(Domain.status == status)
        stmt = stmt.order_by(Domain.domain_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, domain_id: str) -> Domain | None:
        return await self.session.get(Domain, domain_id)

    async def get_by_code(self, code: str) -> Domain | None:
        result = await self.session.execute(select(Domain).where(Domain.code == code))
        return result.scalars().first()

    async def create(self, data: DomainCreate) -> Domain:
        domain_dict = data.model_dump()
        if not domain_dict.get("domain_id"):
            code_clean = data.code.strip().upper().replace(" ", "-")
            domain_dict["domain_id"] = f"DOM-{code_clean}"
        return await commit_or_conflict(self.session, Domain(**domain_dict))

    async def update(self, domain: Domain, data: DomainUpdate) -> Domain:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(domain, field, value)
        return await commit_or_conflict(self.session, domain, refresh_targets=(domain,))

    async def retire(self, domain: Domain) -> Domain:
        domain.status = "RETIRED"
        return await commit_or_conflict(self.session, domain, refresh_targets=(domain,))


class SkillRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        skill_type: str | None = None,
        skill_nature: str | None = None,
        domain_id: str | None = None,
        search: str | None = None,
    ) -> Sequence[Skill]:
        stmt = select(Skill)
        if status:
            stmt = stmt.where(Skill.status == status)
        if skill_type:
            stmt = stmt.where(Skill.skill_type == skill_type)
        if skill_nature:
            stmt = stmt.where(Skill.skill_nature == skill_nature)
        if domain_id:
            stmt = stmt.where(
                Skill.skill_id.in_(select(SkillDomain.skill_id).where(SkillDomain.domain_id == domain_id))
            )
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Skill.preferred_name).like(term),
                    func.lower(Skill.skill_id).like(term),
                )
            )
        stmt = stmt.order_by(Skill.skill_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_id_name_pairs(self, *, active_only: bool = False) -> list[tuple[str, str]]:
        stmt = select(Skill.skill_id, Skill.preferred_name)
        if active_only:
            stmt = stmt.where(Skill.status == "ACTIVE")
        result = await self.session.execute(stmt)
        return [(sid, name) for sid, name in result.all()]

    async def find_by_normalized_name(
        self, normalized_target: str, exclude_skill_id: str | None = None
    ) -> Skill | None:
        for sid, preferred_name in await self.list_id_name_pairs():
            if exclude_skill_id and sid == exclude_skill_id:
                continue
            if normalize_name(preferred_name) == normalized_target:
                return await self.get_by_id(sid)
        return None

    async def get_by_id(self, skill_id: str) -> Skill | None:
        return await self.session.get(Skill, skill_id)

    async def create(self, data: SkillCreate) -> Skill:
        if data.skill_id and data.skill_id.strip():
            return await commit_or_conflict(self.session, Skill(**data.model_dump()))

        for attempt in range(10):
            candidate_id = await generate_prefixed_sequence_id(
                self.session, Skill.skill_id, "SK-", offset=attempt
            )
            skill_dict = data.model_dump()
            skill_dict["skill_id"] = candidate_id
            try:
                return await commit_or_conflict(self.session, Skill(**skill_dict))
            except ConflictError:
                if attempt == 9:
                    raise ConflictError("Could not safely generate unique skill ID after retries")
                continue
        raise ConflictError("Could not safely generate unique skill ID after retries")

    async def update(self, skill: Skill, data: SkillUpdate) -> Skill:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(skill, field, value)
        skill.updated_at = datetime.now(timezone.utc)
        return await commit_or_conflict(self.session, skill, refresh_targets=(skill,))

    async def retire(self, skill: Skill) -> Skill:
        skill.status = "RETIRED"
        skill.updated_at = datetime.now(timezone.utc)
        return await commit_or_conflict(self.session, skill, refresh_targets=(skill,))


class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        domain_id: str | None = None,
        search: str | None = None,
    ) -> Sequence[Role]:
        stmt = select(Role)
        if status:
            stmt = stmt.where(Role.status == status)
        if domain_id:
            stmt = stmt.where(
                Role.role_id.in_(select(RoleDomain.role_id).where(RoleDomain.domain_id == domain_id))
            )
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Role.preferred_name).like(term),
                    func.lower(Role.role_id).like(term),
                )
            )
        stmt = stmt.order_by(Role.role_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_id_name_pairs(self, *, active_only: bool = False) -> list[tuple[str, str]]:
        stmt = select(Role.role_id, Role.preferred_name)
        if active_only:
            stmt = stmt.where(Role.status == "ACTIVE")
        result = await self.session.execute(stmt)
        return [(rid, name) for rid, name in result.all()]

    async def find_by_normalized_name(
        self, normalized_target: str, exclude_role_id: str | None = None
    ) -> Role | None:
        for rid, preferred_name in await self.list_id_name_pairs():
            if exclude_role_id and rid == exclude_role_id:
                continue
            if normalize_name(preferred_name) == normalized_target:
                return await self.get_by_id(rid)
        return None

    async def get_by_id(self, role_id: str) -> Role | None:
        return await self.session.get(Role, role_id)

    async def create(self, data: RoleCreate) -> Role:
        if data.role_id and data.role_id.strip():
            return await commit_or_conflict(self.session, Role(**data.model_dump()))

        for attempt in range(10):
            candidate_id = await generate_prefixed_sequence_id(
                self.session, Role.role_id, "RL-", offset=attempt
            )
            role_dict = data.model_dump()
            role_dict["role_id"] = candidate_id
            try:
                return await commit_or_conflict(self.session, Role(**role_dict))
            except ConflictError:
                if attempt == 9:
                    raise ConflictError("Could not safely generate unique role ID after retries")
                continue
        raise ConflictError("Could not safely generate unique role ID after retries")

    async def update(self, role: Role, data: RoleUpdate) -> Role:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        role.updated_at = datetime.now(timezone.utc)
        return await commit_or_conflict(self.session, role, refresh_targets=(role,))

    async def retire(self, role: Role) -> Role:
        role.status = "RETIRED"
        role.updated_at = datetime.now(timezone.utc)
        return await commit_or_conflict(self.session, role, refresh_targets=(role,))
