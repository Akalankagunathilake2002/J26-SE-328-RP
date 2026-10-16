import unicodedata
from difflib import SequenceMatcher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Skill, Role
from app.models.aliases import SkillAlias, RoleAlias
from app.schemas.normalization import (
    BulkNormalizeRequest,
    BulkNormalizeResponse,
    NormalizeResultItem,
    SuggestedMatch,
)

def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

class NormalizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def normalize_skills(self, request: BulkNormalizeRequest) -> BulkNormalizeResponse:
        return await self._normalize_entities(
            items=request.items,
            model_cls=Skill,
            alias_cls=SkillAlias,
            id_attr="skill_id",
            name_attr="preferred_name",
        )

    async def normalize_roles(self, request: BulkNormalizeRequest) -> BulkNormalizeResponse:
        return await self._normalize_entities(
            items=request.items,
            model_cls=Role,
            alias_cls=RoleAlias,
            id_attr="role_id",
            name_attr="preferred_name",
        )

    async def _normalize_entities(
        self,
        items: list[str],
        model_cls,
        alias_cls,
        id_attr: str,
        name_attr: str,
    ) -> BulkNormalizeResponse:
        canonical_result = await self.session.execute(select(model_cls))
        canonicals = canonical_result.scalars().all()

        canonical_by_id = {getattr(c, id_attr): getattr(c, name_attr) for c in canonicals}
        canonical_by_norm = {
            normalize_name(getattr(c, name_attr)): (getattr(c, id_attr), getattr(c, name_attr))
            for c in canonicals
        }

        unique_inputs = list(dict.fromkeys(items))
        norm_map = {item: normalize_name(item) for item in unique_inputs}

        unmatched_norms = {
            norm for norm in norm_map.values() if norm not in canonical_by_norm
        }

        alias_by_norm = {}
        if unmatched_norms:
            alias_result = await self.session.execute(
                select(alias_cls).where(
                    alias_cls.normalized_alias.in_(unmatched_norms),
                    alias_cls.verification_status == "VERIFIED",
                )
            )
            for alias in alias_result.scalars().all():
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

        ordered_results = [cached_results[item] for item in items]
        return BulkNormalizeResponse(results=ordered_results)
