from typing import Sequence
import uuid
from fastapi import HTTPException

from app.core.security import ROLE_ADMIN, ROLE_HR
from app.core.text import normalize_name
from app.repositories.aliases import RoleAliasRepository, SkillAliasRepository
from app.repositories.base import ConflictError
from app.repositories.core import RoleRepository, SkillRepository
from app.repositories.sources import KnowledgeSourceRepository
from app.schemas.aliases import AliasCreate, AliasUpdate, AliasVerifyRequest


class AliasService:
    def __init__(
        self,
        skill_alias_repo: SkillAliasRepository,
        role_alias_repo: RoleAliasRepository,
        skill_repo: SkillRepository,
        role_repo: RoleRepository,
        source_repo: KnowledgeSourceRepository,
    ):
        self.skill_alias_repo = skill_alias_repo
        self.role_alias_repo = role_alias_repo
        self.skill_repo = skill_repo
        self.role_repo = role_repo
        self.source_repo = source_repo

    def _resolve_repos(self, kind: str):
        if kind == "SKILL":
            return self.skill_alias_repo, self.skill_repo, "Skill", "skill_id"
        return self.role_alias_repo, self.role_repo, "Role", "role_id"

    async def _list(
        self,
        *,
        kind: str,
        caller_role: str,
        limit: int = 100,
        offset: int = 0,
        entity_id: str | None = None,
        verification_status: str | None = None,
        search: str | None = None,
    ) -> Sequence:
        alias_repo, entity_repo, label, _ = self._resolve_repos(kind)
        if entity_id is not None and not await entity_repo.get_by_id(entity_id):
            raise HTTPException(status_code=404, detail=f"{label} '{entity_id}' not found")

        effective_status = verification_status
        if caller_role not in (ROLE_HR, ROLE_ADMIN):
            if verification_status and verification_status != "VERIFIED":
                raise HTTPException(
                    status_code=403,
                    detail="Only HR or ADMIN users may access unverified aliases",
                )
            effective_status = "VERIFIED"

        return await alias_repo.get_all(
            limit=limit,
            offset=offset,
            entity_id=entity_id,
            verification_status=effective_status,
            search=search,
        )

    async def _get(self, kind: str, alias_id: uuid.UUID, *, caller_role: str | None = None):
        alias_repo, _, label, _ = self._resolve_repos(kind)
        alias = await alias_repo.get_by_id(alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail=f"{label} alias not found")
        if caller_role and caller_role not in (ROLE_HR, ROLE_ADMIN) and alias.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=403,
                detail="Only HR or ADMIN users may access unverified aliases",
            )
        return alias

    async def _create(self, kind: str, entity_id: str, data: AliasCreate):
        alias_repo, entity_repo, label, _ = self._resolve_repos(kind)
        if not await entity_repo.get_by_id(entity_id):
            raise HTTPException(status_code=404, detail=f"{label} '{entity_id}' not found")
        if data.source_id is not None and not await self.source_repo.get_by_id(data.source_id):
            raise HTTPException(status_code=404, detail=f"Knowledge source '{data.source_id}' not found")

        norm = normalize_name(data.alias_text)
        if await alias_repo.find_by_entity_and_normalized(entity_id, norm):
            raise HTTPException(
                status_code=409,
                detail=f"Alias '{data.alias_text}' already exists for {label.lower()} '{entity_id}'",
            )
        if data.verification_status == "VERIFIED":
            dup_verified = await alias_repo.find_verified_by_normalized(norm)
            if dup_verified:
                raise HTTPException(
                    status_code=409,
                    detail=f"A verified {label.lower()} alias for '{data.alias_text}' already exists",
                )

        try:
            return await alias_repo.create(
                entity_id=entity_id,
                alias_text=data.alias_text,
                normalized_alias=norm,
                source_id=data.source_id,
                verification_status=data.verification_status,
            )
        except ConflictError:
            raise HTTPException(status_code=409, detail=f"{label} alias conflicts with an existing record")

    async def _update(self, kind: str, alias_id: uuid.UUID, data: AliasUpdate):
        alias_repo, _, label, id_attr = self._resolve_repos(kind)
        alias = await self._get(kind, alias_id)
        entity_id = getattr(alias, id_attr)

        update_fields = data.model_dump(exclude_unset=True)
        if "source_id" in update_fields and data.source_id is not None:
            if not await self.source_repo.get_by_id(data.source_id):
                raise HTTPException(status_code=404, detail=f"Knowledge source '{data.source_id}' not found")

        new_text = data.alias_text if data.alias_text is not None else alias.alias_text
        new_norm = normalize_name(new_text)
        new_status = data.verification_status if data.verification_status is not None else alias.verification_status

        if data.alias_text is not None:
            dup_same = await alias_repo.find_by_entity_and_normalized(
                entity_id, new_norm, exclude_alias_id=alias_id
            )
            if dup_same:
                raise HTTPException(
                    status_code=409,
                    detail=f"Alias '{new_text}' already exists for {label.lower()} '{entity_id}'",
                )

        if new_status == "VERIFIED":
            dup_verified = await alias_repo.find_verified_by_normalized(
                new_norm, exclude_alias_id=alias_id
            )
            if dup_verified:
                raise HTTPException(
                    status_code=409,
                    detail=f"A verified {label.lower()} alias for '{new_text}' already exists",
                )

        try:
            return await alias_repo.update(
                alias,
                alias_text=data.alias_text,
                normalized_alias=new_norm if data.alias_text is not None else None,
                source_id=data.source_id,
                update_source_id="source_id" in update_fields,
                verification_status=data.verification_status,
            )
        except ConflictError:
            raise HTTPException(status_code=409, detail=f"{label} alias update conflicts with an existing record")

    async def _verify(self, kind: str, alias_id: uuid.UUID, data: AliasVerifyRequest):
        return await self._update(kind, alias_id, AliasUpdate(verification_status=data.verification_status))

    async def _delete(self, kind: str, alias_id: uuid.UUID) -> None:
        alias_repo, _, _, _ = self._resolve_repos(kind)
        alias = await self._get(kind, alias_id)
        await alias_repo.delete(alias)

    async def list_skill_aliases(self, **kwargs):
        return await self._list(kind="SKILL", **kwargs)

    async def get_skill_alias(self, alias_id: uuid.UUID, *, caller_role: str):
        return await self._get("SKILL", alias_id, caller_role=caller_role)

    async def create_skill_alias(self, skill_id: str, data: AliasCreate):
        return await self._create("SKILL", skill_id, data)

    async def update_skill_alias(self, alias_id: uuid.UUID, data: AliasUpdate):
        return await self._update("SKILL", alias_id, data)

    async def verify_skill_alias(self, alias_id: uuid.UUID, data: AliasVerifyRequest):
        return await self._verify("SKILL", alias_id, data)

    async def delete_skill_alias(self, alias_id: uuid.UUID) -> None:
        await self._delete("SKILL", alias_id)

    async def list_role_aliases(self, **kwargs):
        return await self._list(kind="ROLE", **kwargs)

    async def get_role_alias(self, alias_id: uuid.UUID, *, caller_role: str):
        return await self._get("ROLE", alias_id, caller_role=caller_role)

    async def create_role_alias(self, role_id: str, data: AliasCreate):
        return await self._create("ROLE", role_id, data)

    async def update_role_alias(self, alias_id: uuid.UUID, data: AliasUpdate):
        return await self._update("ROLE", alias_id, data)

    async def verify_role_alias(self, alias_id: uuid.UUID, data: AliasVerifyRequest):
        return await self._verify("ROLE", alias_id, data)

    async def delete_role_alias(self, alias_id: uuid.UUID) -> None:
        await self._delete("ROLE", alias_id)
