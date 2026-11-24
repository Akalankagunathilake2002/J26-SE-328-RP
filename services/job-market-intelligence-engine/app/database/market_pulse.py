"""The Market Pulse profile built from the database instead of data/processed/skill_profile.json.

The loader (app/database/loader.py) stores every ad, its sectors and every skill mention. This module
reads them back and hands them to the same ``build_profile`` that writes skill_profile.json, so the
page shows the same numbers whichever source it comes from.

What the database doesn't hold, and how it is filled in:
- ``last_checked`` of a site: the time of its newest sync run (the file uses the listing-page log).
- SSKS IDs of lexicon skills: only the IDs set by hand in the lexicon. IDs that a sync found by
  asking SSKS are not stored, so with SSKS linking switched on they can be missing here.
- NER suggestions for unverified skills: not stored (None).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.engine import Engine

from app.collectors.config import load_sectors
from app.collectors.models import ACTIVE, JobAd
from app.database.schema import job_ad_sectors, job_ad_skills, job_ads, sync_runs
from app.integrations.ssks import COUNTED, SSKSMatch, normalize_key
from app.processing.roles import RoleMatch
from app.processing.skills import (
    MATCH_TYPES,
    VERIFIED_CATEGORY,
    AnalysedAd,
    DemandSkill,
    FoundSkill,
    SkillLexicon,
    build_profile,
)


def _iso(value: datetime | str | None) -> str | None:
    """Timestamps as the files write them: ISO 8601 in UTC."""
    if value is None or isinstance(value, str):
        return value
    if value.tzinfo is None:  # SQLite returns naive datetimes; the loader stored UTC
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def profile_from_database(
    engine: Engine,
    sites: Sequence[str],
    include_inactive: bool = False,
    lexicon: SkillLexicon | None = None,
) -> dict | None:
    """The skill profile of the ads in the database, or None when there are no ads yet."""
    lexicon = lexicon or SkillLexicon.load()
    loaded = load_analysed(engine, sites, include_inactive, lexicon)
    if loaded is None:
        return None
    analysed, last_sync, loaded_at = loaded
    sources = [_source(site, analysed, last_sync.get(site)) for site in sites]
    generated_at = max((t for t in last_sync.values() if t), default=None) or loaded_at
    return build_profile(
        analysed, sources, generated_at, include_inactive, load_sectors(), _extraction(analysed, lexicon)
    )


def load_analysed(
    engine: Engine, sites: Sequence[str], include_inactive: bool, lexicon: SkillLexicon
) -> tuple[list[AnalysedAd], dict[str, str | None], str | None] | None:
    """The ads in the database as ``analyse`` leaves them, the newest sync per site, and the newest
    load time. None when there are no ads."""
    by_name = {skill.name: skill for skill in lexicon.skills}

    a, k, s = job_ads.c, job_ad_skills.c, job_ad_sectors.c
    wanted = a.site.in_(list(sites)) if include_inactive else (a.site.in_(list(sites)) & (a.status == ACTIVE))
    joined = (a.site == k.site) & (a.job_id == k.job_id)
    with engine.connect() as conn:
        # Only the columns the profile needs: the ad texts are large and not used here.
        ad_rows = conn.execute(
            select(a.site, a.job_id, a.url, a.job_title, a.company, a.experience_level, a.status, a.collected_at,
                   a.loaded_at, a.role, a.role_mapped, a.seniority, a.flags)
            .where(wanted).order_by(a.site, a.job_id)
        ).mappings().all()
        if not ad_rows:
            return None
        sectors: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in conn.execute(select(s.site, s.job_id, s.sector).order_by(s.sector)).mappings():
            sectors[(row["site"], row["job_id"])].append(row["sector"])
        mentions: dict[tuple[str, str], list] = defaultdict(list)
        mention_query = (
            select(k.site, k.job_id, k.extractor, k.raw_text, k.start_char, k.end_char, k.label, k.lexicon_skill,
                   k.ssk_id, k.ssks_name, k.match_type)
            .select_from(job_ad_skills.join(job_ads, joined)).where(wanted).order_by(k.id)
        )
        for row in conn.execute(mention_query).mappings():
            mentions[(row["site"], row["job_id"])].append(row)
        last_sync = {
            site: _iso(synced)
            for site, synced in conn.execute(
                select(sync_runs.c.site, sync_runs.c.synced_at).order_by(sync_runs.c.synced_at)
            ).all()
        }

    analysed = []
    for row in ad_rows:
        key = (row["site"], row["job_id"])
        ad = JobAd(
            site=row["site"], job_id=row["job_id"], url=row["url"], sectors=sectors.get(key, []),
            job_title=row["job_title"], company=row["company"], experience_level=row["experience_level"],
            status=row["status"], collected_at=_iso(row["collected_at"]),
        )
        role = RoleMatch(row["role"] or "", bool(row["role_mapped"]), row["seniority"] or "")
        flags = [flag for flag in (row["flags"] or "").split(",") if flag]
        analysed.append(_analysed(ad, role, flags, mentions.get(key, []), by_name))

    return analysed, last_sync, max(_iso(row["loaded_at"]) for row in ad_rows)


def _analysed(ad: JobAd, role: RoleMatch, flags: list[str], rows: list, by_name: dict) -> AnalysedAd:
    """One ad as ``analyse`` leaves it: its counted skills and its unverified NER mentions."""
    found = [
        FoundSkill(
            extractor=r["extractor"], text=r["raw_text"], start=r["start_char"], end=r["end_char"],
            label=r["label"] or "", lexicon_skill=r["lexicon_skill"],
            ssks=SSKSMatch(r["match_type"], r["ssk_id"], r["ssks_name"]),
        )
        for r in rows
    ]
    lexicon_found = [f for f in found if f.extractor == "lexicon"]
    skills = []
    for name in dict.fromkeys(f.lexicon_skill for f in lexicon_found if f.lexicon_skill):
        skill = by_name.get(name)
        category = skill.category if skill else next(f.label for f in lexicon_found if f.lexicon_skill == name)
        skills.append(DemandSkill(name, category, (skill.ssk_id,) if skill and skill.ssk_id else ()))
    covered = {ssk_id for skill in skills for ssk_id in skill.ssk_ids}
    unverified: dict[str, FoundSkill] = {}
    for f in (f for f in found if f.extractor == "ner"):
        if f.ssks.match_type in COUNTED:
            if f.ssks.ssk_id not in covered:
                skills.append(DemandSkill(f.ssks.preferred_name or f.text, VERIFIED_CATEGORY, (f.ssks.ssk_id,), "ner"))
                covered.add(f.ssks.ssk_id)
        elif not any(f.start < l.end and l.start < f.end for l in lexicon_found):
            unverified.setdefault(normalize_key(f.text), f)
    return AnalysedAd(ad, role, skills, flags, found, list(unverified.values()))


def _source(site: str, analysed: list[AnalysedAd], last_checked: str | None) -> dict:
    collected = [item.ad.collected_at for item in analysed if item.ad.site == site and item.ad.collected_at]
    return {
        "site": site,
        "ads": sum(item.ad.site == site for item in analysed),
        "last_collected": max(collected, default=None),
        "last_checked": last_checked,
    }


def _extraction(analysed: list[AnalysedAd], lexicon: SkillLexicon) -> dict:
    """How the skills were found, worked out from the stored mentions."""
    found = [f for item in analysed for f in item.found]
    extractors = {f.extractor for f in found}
    mode = "both" if extractors == {"lexicon", "ner"} else "ner" if extractors == {"ner"} else "lexicon"
    types = defaultdict(int)
    for f in found:
        types[f.ssks.match_type] += 1
    checked = any(t != "pending" for t in types)
    return {
        "extractor": mode,
        "ssks_checked": checked,
        "ssks_reachable": True if checked else None,
        "mentions": len(found),
        "mention_match_types": {t: types[t] for t in MATCH_TYPES} if checked else None,
        "mention_match_rate": (round(sum(types[t] for t in COUNTED) / len(found), 3) if checked and found else None),
    }
