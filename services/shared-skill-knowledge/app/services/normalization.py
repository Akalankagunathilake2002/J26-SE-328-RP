from difflib import SequenceMatcher

from app.core.text import normalize_name
from app.repositories.aliases import RoleAliasRepository, SkillAliasRepository
from app.repositories.core import RoleRepository, SkillRepository
from app.schemas.normalization import (
    BulkNormalizeRequest,
    BulkNormalizeResponse,
    NormalizeResultItem,
    SuggestedMatch,
)


class NormalizationService:
    def __init__(
        self,
        skill_repo: SkillRepository,
        role_repo: RoleRepository,
        skill_alias_repo: SkillAliasRepository,
        role_alias_repo: RoleAliasRepository,
    ):
        self.skill_repo = skill_repo
        self.role_repo = role_repo
        self.skill_alias_repo = skill_alias_repo
        self.role_alias_repo = role_alias_repo

    async def normalize_skills(self, request: BulkNormalizeRequest) -> BulkNormalizeResponse:
        return await self._normalize_entities(
            items=request.items,
            entity_repo=self.skill_repo,
            alias_repo=self.skill_alias_repo,
            id_attr="skill_id",
        )

    async def normalize_roles(self, request: BulkNormalizeRequest) -> BulkNormalizeResponse:
        return await self._normalize_entities(
            items=request.items,
            entity_repo=self.role_repo,
            alias_repo=self.role_alias_repo,
            id_attr="role_id",
        )

    async def _normalize_entities(
        self,
        items: list[str],
        entity_repo,
        alias_repo,
        id_attr: str,
    ) -> BulkNormalizeResponse:
        id_name_pairs = await entity_repo.list_id_name_pairs(active_only=True)
        canonical_by_id = {cid: cname for cid, cname in id_name_pairs}
        canonical_by_norm = {normalize_name(cname): (cid, cname) for cid, cname in id_name_pairs}

        unique_inputs = list(dict.fromkeys(items))
        norm_map = {item: normalize_name(item) for item in unique_inputs}
        unmatched_norms = {norm for norm in norm_map.values() if norm not in canonical_by_norm}

        alias_by_norm: dict[str, tuple[str, str]] = {}
        if unmatched_norms:
            verified_aliases = await alias_repo.get_verified_by_normalized_aliases(unmatched_norms)
            for alias in verified_aliases:
                target_id = getattr(alias, id_attr)
                target_name = canonical_by_id.get(target_id)
                if target_name:
                    alias_by_norm[alias.normalized_alias] = (target_id, target_name)

        cached_results: dict[str, NormalizeResultItem] = {}
        canonical_norms = list(canonical_by_norm.items())

        for item in unique_inputs:
            norm = norm_map[item]
            if norm in canonical_by_norm:
                cid, cname = canonical_by_norm[norm]
                cached_results[item] = NormalizeResultItem(
                    input_name=item,
                    status="MATCHED",
                    canonical_id=cid,
                    preferred_name=cname,
                    matching_method="CANONICAL_NAME",
                    suggestions=[],
                )
            elif norm in alias_by_norm:
                cid, cname = alias_by_norm[norm]
                cached_results[item] = NormalizeResultItem(
                    input_name=item,
                    status="MATCHED",
                    canonical_id=cid,
                    preferred_name=cname,
                    matching_method="VERIFIED_ALIAS",
                    suggestions=[],
                )
            else:
                suggestions: list[SuggestedMatch] = []
                for c_norm, (cid, cname) in canonical_norms:
                    score = SequenceMatcher(None, norm, c_norm).ratio()
                    if score >= 0.80:
                        suggestions.append(
                            SuggestedMatch(
                                canonical_id=cid,
                                preferred_name=cname,
                                score=round(score, 4),
                            )
                        )
                suggestions.sort(key=lambda s: s.score, reverse=True)
                top_suggestions = suggestions[:3]

                if top_suggestions:
                    cached_results[item] = NormalizeResultItem(
                        input_name=item,
                        status="SUGGESTED",
                        canonical_id=None,
                        preferred_name=None,
                        matching_method="FUZZY_SUGGESTION",
                        suggestions=top_suggestions,
                    )
                else:
                    cached_results[item] = NormalizeResultItem(
                        input_name=item,
                        status="UNMATCHED",
                        canonical_id=None,
                        preferred_name=None,
                        matching_method=None,
                        suggestions=[],
                    )

        return BulkNormalizeResponse(results=[cached_results[item] for item in items])
