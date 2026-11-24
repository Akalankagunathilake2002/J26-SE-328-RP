"""Role profiles for C03 (the Readiness Engine): what each job role needs, per career level.

    python -m app.database.role_profiles      # needs SKILLBRIDGE_DATABASE_URL (and SKILLBRIDGE_SSKS_URL for skill ids)

Reads the active ads from the database (the loader fills it) and writes the C01 → C03 contract tables of
Skillaro_DB_Contract_v2: role_profiles, role_profile_requirements, role_profile_education,
role_profile_experience, role_profile_certifications and requirement_evidence. Every sync run does this
after loading the ads.

Rules (agreed in the contract unless marked "C01 choice"):
- One ROLE profile per role and career level. Only roles with an SSKS role id (`ssks_role_id` in
  config/role_taxonomy.yaml) are published: the contract needs a canonical or candidate role id.
- Career level from the title's seniority (C01 choice): Trainee / Intern → INTERN, Assistant / Junior →
  JUNIOR, Executive / Officer → MID_LEVEL, Senior / Lead → SENIOR, Manager / Head → LEAD.
- A skill's demand_weight = demand_frequency = ads asking for it ÷ ads with readable text, for that
  role and level. Required proficiency stays NULL: the ads don't state it reliably.
- Skill ids: the lexicon's own id, or the SSKS match of the skill's name or verified alias (exact or
  alias only). No match: UNMAPPED, which C03 never treats as a canonical skill.
- Qualifications are not skills: degrees go to role_profile_education (SLQF levels, C01 choice of codes
  SLQF_1…SLQF_12), professional qualifications and licences to role_profile_certifications.
- Experience: the minimum years each ad states ("2–3 years" → 2); the profile keeps their median.
- Profiles from fewer than MIN_ADS_WITH_TEXT readable ads are DRAFT, so C03 can ignore them.
- Versions never change once written (profile_version = the date of the newest sync). A new version is
  only written when the profile's content changed; the previous published version is then ARCHIVED.
"""

from __future__ import annotations

import argparse
import logging
import re
import statistics
import sys
import uuid
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.engine import Connection, Engine

from app.collectors.base import utc_now
from app.collectors.config import load_settings, load_sites
from app.database.contract import (
    metadata,
    requirement_evidence,
    role_profile_certifications,
    role_profile_education,
    role_profile_experience,
    role_profile_requirements,
    role_profiles,
)
from app.database.market_pulse import load_analysed
from app.processing.roles import RoleTaxonomy
from app.processing.skills import VERIFIED_CATEGORY, AnalysedAd, SkillLexicon, _lexicon_ids

log = logging.getLogger(__name__)

MIN_ADS_WITH_TEXT = 3  # fewer readable ads: the profile is DRAFT
EVIDENCE_PER_REQUIREMENT = 5  # ads kept as evidence for each requirement

CAREER_LEVEL = {
    "Trainee / Intern": "INTERN",
    "Assistant / Junior": "JUNIOR",
    "Executive / Officer": "MID_LEVEL",
    "Senior / Lead": "SENIOR",
    "Manager / Head": "LEAD",
}
SKILL_TYPE = {
    "Technical": "TECHNICAL", "Tool": "TECHNICAL", "Domain knowledge": "TECHNICAL",
    VERIFIED_CATEGORY: "TECHNICAL", "Soft skill": "BEHAVIOURAL", "Language": "BEHAVIOURAL",
}
QUALIFICATION = "Qualification"
# Lexicon qualification → (SLQF level, completion requirement)
EDUCATION = {
    "G.C.E. O/L": ("SLQF_1", "COMPLETED"),
    "G.C.E. A/L": ("SLQF_2", "COMPLETED"),
    "Diploma / HND": ("SLQF_3", "COMPLETED"),
    "Bachelor's degree": ("SLQF_5", "COMPLETED"),
    "Undergraduate (studying)": ("SLQF_5", "IN_PROGRESS"),
    "Master's degree": ("SLQF_9", "COMPLETED"),
}
ISSUERS = {"Driving licence": "Department of Motor Traffic"}
YEARS = re.compile(r"(\d+)")


@dataclass
class PublishResult:
    published: int = 0  # new PUBLISHED versions
    drafts: int = 0  # new DRAFT versions
    unchanged: int = 0  # same content as the latest version: nothing written
    archived: int = 0
    requirements: int = 0
    unmapped_roles: Counter = field(default_factory=Counter)  # role → ads, roles without an SSKS id
    skills_without_id: int = 0  # requirements written as UNMAPPED


@dataclass
class Profile:
    role: str
    role_id: str
    career_level: str
    items: list[AnalysedAd]
    version: str
    lexicon_ids: dict[str, tuple[str, ...]]

    @property
    def with_text(self) -> list[AnalysedAd]:
        return [item for item in self.items if item.has_text]

    def requirements(self) -> list[dict]:
        counts: Counter = Counter()
        terms: dict[str, Counter] = defaultdict(Counter)
        ads: dict[str, list] = defaultdict(list)
        categories: dict[str, str] = {}
        for item in self.with_text:
            for skill in item.skills:
                if skill.category == QUALIFICATION:
                    continue
                counts[skill.name] += 1
                categories[skill.name] = skill.category
                found = [f for f in item.found if (f.lexicon_skill or f.ssks.preferred_name) == skill.name]
                for f in found:
                    terms[skill.name][f.text] += 1
                ads[skill.name].append((item.ad.site, item.ad.job_id, found[0].text if found else None))
        n = len(self.with_text)
        rows = []
        for name, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
            ids = self.lexicon_ids.get(name, ())
            share = round(count / n, 4)
            rows.append({
                "standard_name": name,
                "skill_id": sorted(ids)[0] if ids else None,
                "mapping_status": "VERIFIED" if ids else "UNMAPPED",
                "skill_type": SKILL_TYPE.get(categories[name], "TECHNICAL"),
                "primary_observed_term": terms[name].most_common(1)[0][0] if terms[name] else None,
                "observed_terms": [t for t, _ in terms[name].most_common(10)],
                "demand_frequency": share,
                "demand_weight": share,
                "job_ads_containing_skill": count,
                "evidence": ads[name][:EVIDENCE_PER_REQUIREMENT],
            })
        return rows

    def qualifications(self) -> tuple[list[dict], list[dict]]:
        counts: Counter = Counter(
            skill.name for item in self.with_text for skill in item.skills if skill.category == QUALIFICATION
        )
        education = [
            {"qualification_level": EDUCATION[name][0], "completion_requirement": EDUCATION[name][1],
             "job_ads_count": count}
            for name, count in sorted(counts.items()) if name in EDUCATION
        ]
        certifications = [
            {"certification_name": name, "issuing_organization": ISSUERS.get(name), "job_ads_count": count}
            for name, count in sorted(counts.items()) if name not in EDUCATION
        ]
        return education, certifications

    def experience(self) -> dict | None:
        years = [int(m.group(1)) for item in self.items
                 if item.ad.experience_level and (m := YEARS.search(item.ad.experience_level))]
        if not years:
            return None
        return {"minimum_years": statistics.median(years), "job_ads_count": len(years)}

    def fingerprint(self) -> tuple:
        """What makes two versions the same: the counts and the requirements."""
        reqs = tuple((r["standard_name"], r["job_ads_containing_skill"], r["skill_id"]) for r in self.requirements())
        education, certifications = self.qualifications()
        return (len(self.items), len(self.with_text), reqs,
                tuple(sorted((e["qualification_level"], e["job_ads_count"]) for e in education)),
                tuple(sorted((c["certification_name"], c["job_ads_count"]) for c in certifications)),
                tuple(sorted((self.experience() or {}).items())))


def build_profiles(
    analysed: list[AnalysedAd], taxonomy: RoleTaxonomy, version: str, lexicon_ids: dict[str, tuple[str, ...]],
) -> tuple[list[Profile], Counter]:
    """One profile per (role with an SSKS id, career level). Also the ads of roles without an id."""
    ids = {role.name: role.ssks_role_id for role in taxonomy.roles if role.ssks_role_id}
    groups: dict[tuple[str, str], list[AnalysedAd]] = defaultdict(list)
    unmapped: Counter = Counter()
    for item in analysed:
        if item.role.role not in ids:
            unmapped[item.role.role] += 1
            continue
        groups[(item.role.role, CAREER_LEVEL.get(item.role.seniority, "MID_LEVEL"))].append(item)
    profiles = [Profile(role, ids[role], level, items, version, lexicon_ids)
                for (role, level), items in sorted(groups.items())]
    return profiles, unmapped


def publish(conn: Connection, profiles: list[Profile], now: datetime) -> PublishResult:
    result = PublishResult()
    for profile in profiles:
        latest = conn.execute(
            select(role_profiles.c.profile_id, role_profiles.c.profile_version)
            .where(role_profiles.c.profile_type == "ROLE", role_profiles.c.role_id == profile.role_id,
                   role_profiles.c.career_level == profile.career_level)
            .order_by(role_profiles.c.created_at.desc()).limit(1)
        ).first()
        if latest is not None and _stored_fingerprint(conn, latest.profile_id) == profile.fingerprint():
            result.unchanged += 1
            continue
        version = _free_version(conn, profile)
        status = "PUBLISHED" if len(profile.with_text) >= MIN_ADS_WITH_TEXT else "DRAFT"
        if status == "PUBLISHED":
            result.archived += conn.execute(
                update(role_profiles)
                .where(role_profiles.c.profile_type == "ROLE", role_profiles.c.role_id == profile.role_id,
                       role_profiles.c.career_level == profile.career_level,
                       role_profiles.c.profile_status == "PUBLISHED")
                .values(profile_status="ARCHIVED")
            ).rowcount
        _insert(conn, profile, version, status, now, result)
        if status == "PUBLISHED":
            result.published += 1
        else:
            result.drafts += 1
    return result


def _insert(conn: Connection, profile: Profile, version: str, status: str, now: datetime, result: PublishResult):
    items = profile.items
    sectors = Counter(s for item in items for s in item.ad.sectors)
    dates = sorted(d for item in items if (d := _date(item.ad.collected_at)))
    profile_id = uuid.uuid4()
    conn.execute(role_profiles.insert().values(
        profile_id=profile_id, profile_type="ROLE", vacancy_id=None, role_id=profile.role_id,
        candidate_role_id=None, primary_observed_title=profile.role,
        observed_titles=sorted({item.ad.job_title for item in items if item.ad.job_title})[:50],
        mapping_status="VERIFIED", profile_status=status, profile_version=version,
        career_level=profile.career_level, domain_id=None,
        sector=sectors.most_common(1)[0][0] if sectors else None,
        job_posting_count=len(items), ads_with_text=len(profile.with_text),
        observation_period_from=dates[0] if dates else None, observation_period_to=dates[-1] if dates else None,
        published_at=now if status == "PUBLISHED" else None, created_at=now,
    ))
    for req in profile.requirements():
        requirement_id = uuid.uuid4()
        evidence = req.pop("evidence")
        conn.execute(role_profile_requirements.insert().values(
            requirement_id=requirement_id, profile_id=profile_id, candidate_skill_id=None, importance=None,
            required_proficiency_level=None, required_proficiency_score=None, **req,
        ))
        result.requirements += 1
        result.skills_without_id += req["skill_id"] is None
        if evidence:
            conn.execute(requirement_evidence.insert(), [
                {"requirement_id": requirement_id, "site": site, "job_id": job_id, "text_excerpt": text}
                for site, job_id, text in dict.fromkeys(evidence)
            ])
    education, certifications = profile.qualifications()
    for row in education:
        conn.execute(role_profile_education.insert().values(
            education_req_id=uuid.uuid4(), profile_id=profile_id, accepted_fields=None, is_mandatory=None, **row))
    for row in certifications:
        conn.execute(role_profile_certifications.insert().values(
            certification_req_id=uuid.uuid4(), profile_id=profile_id, is_mandatory=None, created_at=now, **row))
    experience = profile.experience()
    if experience:
        conn.execute(role_profile_experience.insert().values(
            experience_req_id=uuid.uuid4(), profile_id=profile_id, relevant_experience_required=None,
            accepted_experience_types=None, **experience))


def _stored_fingerprint(conn: Connection, profile_id) -> tuple:
    p = conn.execute(select(role_profiles.c.job_posting_count, role_profiles.c.ads_with_text)
                     .where(role_profiles.c.profile_id == profile_id)).one()
    r = role_profile_requirements.c
    reqs = conn.execute(select(r.standard_name, r.job_ads_containing_skill, r.skill_id)
                        .where(r.profile_id == profile_id)).all()
    reqs = tuple(sorted(((n, c, s) for n, c, s in reqs), key=lambda x: (-x[1], x[0])))
    e = role_profile_education.c
    education = tuple(sorted(conn.execute(select(e.qualification_level, e.job_ads_count)
                                          .where(e.profile_id == profile_id)).all()))
    c = role_profile_certifications.c
    certifications = tuple(sorted(conn.execute(select(c.certification_name, c.job_ads_count)
                                               .where(c.profile_id == profile_id)).all()))
    x = role_profile_experience.c
    exp = conn.execute(select(x.job_ads_count, x.minimum_years).where(x.profile_id == profile_id)).first()
    experience = tuple(sorted({"job_ads_count": exp.job_ads_count, "minimum_years": float(exp.minimum_years)}.items())) if exp else ()
    return (p.job_posting_count, p.ads_with_text, reqs, tuple(map(tuple, education)),
            tuple(map(tuple, certifications)), experience)


def _free_version(conn: Connection, profile: Profile) -> str:
    """The sync date, or date.2, date.3 … if that version of this role and level exists already."""
    taken = set(conn.execute(
        select(role_profiles.c.profile_version)
        .where(role_profiles.c.profile_type == "ROLE", role_profiles.c.role_id == profile.role_id,
               role_profiles.c.career_level == profile.career_level)
    ).scalars())
    version, n = profile.version, 1
    while version in taken:
        n += 1
        version = f"{profile.version}.{n}"
    return version


def _date(value: str | None) -> date | None:
    return datetime.fromisoformat(value).date() if value else None


def lexicon_skill_ids(lexicon: SkillLexicon, ssks_url: str | None, cache_dir=None) -> dict[str, tuple[str, ...]]:
    """SSKS ids of each lexicon skill: set by hand in the lexicon, or the SSKS match of its name or a
    verified alias. Without SSKS only the hand-set ids."""
    matches = {}
    if ssks_url:
        from app.integrations.ssks import SSKSClient

        client = SSKSClient(ssks_url, cache_path=(cache_dir / "ssks_cache.json") if cache_dir else None)
        matches = client.lookup([n for skill in lexicon.skills for n in (skill.name, *skill.aliases)])
        if client.reachable is False:
            log.warning("SSKS not reachable: skills without a hand-set id are published as UNMAPPED")
    return {skill.name: _lexicon_ids(skill, matches) for skill in lexicon.skills}


def publish_role_profiles(
    engine: Engine,
    sites: Sequence[str],
    ssks_url: str | None = None,
    cache_dir=None,
    taxonomy: RoleTaxonomy | None = None,
    lexicon: SkillLexicon | None = None,
    now: datetime | None = None,
) -> PublishResult:
    lexicon = lexicon or SkillLexicon.load()
    loaded = load_analysed(engine, sites, False, lexicon)
    if loaded is None:
        return PublishResult()
    analysed, last_sync, loaded_at = loaded
    newest = max((t for t in last_sync.values() if t), default=None) or loaded_at or utc_now()
    profiles, unmapped = build_profiles(analysed, taxonomy or RoleTaxonomy.load(), newest[:10],
                                        lexicon_skill_ids(lexicon, ssks_url, cache_dir))
    with engine.begin() as conn:
        result = publish(conn, profiles, now or datetime.now(timezone.utc))
    result.unmapped_roles = unmapped
    return result


def summary(result: PublishResult) -> str:
    skipped = sum(result.unmapped_roles.values())
    return (f"role profiles: {result.published} published, {result.drafts} draft, {result.unchanged} unchanged, "
            f"{result.archived} archived; {result.requirements} requirements written "
            f"({result.skills_without_id} without an SSKS skill id); {skipped} ads of "
            f"{len(result.unmapped_roles)} roles skipped (no SSKS role id)")


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Publish the role profiles C03 reads (see module docs).")
    parser.parse_args(argv)
    settings = load_settings()
    if not settings.database_url:
        log.error("SKILLBRIDGE_DATABASE_URL is not set")
        return 2
    from app.database.loader import connect

    sites = [name for name, site in load_sites().items() if site.enabled]
    result = publish_role_profiles(connect(settings.database_url), sites, settings.ssks_url,
                                   settings.data_dir / "processed")
    print(summary(result))
    top = ", ".join(f"{role} ({n})" for role, n in result.unmapped_roles.most_common(8))
    if top:
        print(f"biggest roles without an SSKS role id: {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
