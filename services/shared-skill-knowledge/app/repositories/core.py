from typing import Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Domain, Skill, Role
from app.models.relationships import SkillDomain, RoleDomain
from app.schemas.core import DomainCreate, SkillCreate, RoleCreate

class ConflictError(Exception):
    pass

async def _insert(session: AsyncSession, obj):
    # Commit changes and map database integrity errors to ConflictError.
    session.add(obj)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError from exc
    except Exception:
        await session.rollback()
        raise
    return obj

class DomainRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> Sequence[Domain]:
        stmt = select(Domain).order_by(Domain.domain_id)
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
        return await _insert(self.session, Domain(**domain_dict))

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
            # Filter skills belonging to the specified domain.
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
        
    async def get_by_id(self, skill_id: str) -> Skill | None:
        stmt = select(Skill).where(Skill.skill_id == skill_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: SkillCreate) -> Skill:
        if data.skill_id and data.skill_id.strip():
            return await _insert(self.session, Skill(**data.model_dump()))

        # Safe concurrent ID generation with collision retries
        for attempt in range(10):
            stmt = select(Skill.skill_id).where(Skill.skill_id.like("SK-%"))
            result = await self.session.execute(stmt)
            ids = result.scalars().all()
            max_num = 0
            for sid in ids:
                num_part = sid[3:]
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
            candidate_id = f"SK-{max_num + 1 + attempt:06d}"

            skill_dict = data.model_dump()
            skill_dict["skill_id"] = candidate_id
            self.session.add(Skill(**skill_dict))
            try:
                await self.session.commit()
                return await self.session.get(Skill, candidate_id)
            except IntegrityError:
                await self.session.rollback()
                continue
        raise ConflictError("Could not safely generate unique skill ID after retries")

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
            # Filter roles belonging to the specified domain.
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
        
    async def get_by_id(self, role_id: str) -> Role | None:
        stmt = select(Role).where(Role.role_id == role_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: RoleCreate) -> Role:
        if data.role_id and data.role_id.strip():
            return await _insert(self.session, Role(**data.model_dump()))

        # Safe concurrent ID generation with collision retries
        for attempt in range(10):
            stmt = select(Role.role_id).where(Role.role_id.like("RL-%"))
            result = await self.session.execute(stmt)
            ids = result.scalars().all()
            max_num = 0
            for rid in ids:
                num_part = rid[3:]
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
            candidate_id = f"RL-{max_num + 1 + attempt:06d}"

            role_dict = data.model_dump()
            role_dict["role_id"] = candidate_id
            self.session.add(Role(**role_dict))
            try:
                await self.session.commit()
                return await self.session.get(Role, candidate_id)
            except IntegrityError:
                await self.session.rollback()
                continue
        raise ConflictError("Could not safely generate unique role ID after retries")
