"""Skill demand per job role: which skills the ads for each role ask for.

    python -m app.processing.skills                      # writes data/processed/skill_profile.md and .json
    python -m app.processing.skills --include-inactive   # also expired and removed ads (history)

Works offline from the processed ads (already cleaned and deduplicated). Each job title is mapped
to a role (config/role_taxonomy.yaml), and skills (config/skills_lexicon.yaml) are searched for in
the part of the ad about the job and the person wanted. "About us", benefits, salary and
how-to-apply sections are left out, and so are URLs ("applyhere.php" is not PHP) and the company
name. A skill counts once per ad, however often the ad mentions it.

Banner-only flyers (too little text to read any requirement from) count as ads but are left out of
the shares, because nothing is known about what they ask for.

skill_profile.json is what the Market Pulse page reads; skill_profile.md is the same profile to
read. ``run`` refreshes both after every run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from app.collectors.base import utc_now
from app.collectors.config import (
    SERVICE_ROOT,
    load_agriculture_keywords,
    load_sectors,
    load_settings,
    load_sites,
)
from app.collectors.models import ACTIVE, STATUSES, JobAd
from app.collectors.storage import Storage
from app.collectors.text_utils import BULLET, REQUIREMENT_HEADING
from app.processing.roles import RoleMatch, RoleTaxonomy

DEFAULT_LEXICON = SERVICE_ROOT / "config" / "skills_lexicon.yaml"
CATEGORIES = ("Technical", "Tool", "Domain knowledge", "Soft skill", "Language", "Qualification")

# Flags on an ad.
BANNER_ONLY = "banner_only"  # too little text to read requirements from (a logo, "We're hiring")
NO_REQUIREMENTS_SECTION = "no_requirements_section"  # no requirements heading: the whole ad was searched
NOT_AGRICULTURE = "not_agriculture"  # in an Agriculture category, but no agriculture keyword anywhere
FLAG_TEXT = {
    BANNER_ONLY: "banner only, no requirements readable",
    NO_REQUIREMENTS_SECTION: "no requirements heading, whole ad searched",
    NOT_AGRICULTURE: "possibly not agriculture",
}

MIN_WORDS = 15  # an ad with fewer words than this (after the skipped sections) is banner-only
NOT_STATED = "Not stated"
SKILLS_IN_REPORT = 20  # rows per skill table in the Markdown file; the JSON has every skill

URL = re.compile(
    r"https?://\S+|www\.\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|lk|org|io|php|jsp|aspx?|html?)\b\S*",
    re.IGNORECASE,
)
# Sections that say nothing about the job. Skipping stops at the next heading.
SKIPPED_SECTION = re.compile(
    r"^(?:about[ \t]+(?:us|the[ \t]+company)|who[ \t]+we[ \t]+are|benefits|perks|(?:what[ \t]+)?we[ \t]+offer"
    r"|how[ \t]+to[ \t]+apply|to[ \t]+apply|apply[ \t]+(?:now|before|via|online|to)|interested[ \t]+candidates"
    r"|candidates[ \t]+meeting|send[ \t]+(?:us[ \t]+)?(?:your[ \t]+)?cvs?|privacy|disclaimer|salary"
    r"|remuneration|package|closing[ \t]+date)\b",
    re.IGNORECASE,
)
JOB_SECTION = re.compile(
    r"^(?:(?:key|job|main|your)[ \t]+)?(?:respon\w*|duties|job[ \t]+description|the[ \t]+role"
    r"|role[ \t]+overview|what[ \t]+you(?:'ll|[ \t]+will)?[ \t]+do)\b",
    re.IGNORECASE,
)
SHORT_HEADING = re.compile(r"^[^:\n]{2,40}:$")  # any other heading, e.g. "Technical Advantage:"
WORD = re.compile(r"[A-Za-z]{2,}")


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    pattern: re.Pattern[str]
    sectors: frozenset[str] = field(default_factory=frozenset)  # empty: ads from any sector
    ssk_id: str | None = None  # the skill's ID in the Shared Skill Knowledge service (step 7)

    def found_in(self, text: str, sectors: Iterable[str]) -> bool:
        if self.sectors and not self.sectors.intersection(sectors):
            return False
        return self.pattern.search(text) is not None


class SkillLexicon:
    def __init__(self, skills: list[Skill]) -> None:
        self.skills = skills

    @classmethod
    def load(cls, path: Path = DEFAULT_LEXICON) -> SkillLexicon:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        skills = []
        for item in data["skills"]:
            alternatives = [alias_pattern(alias) for alias in item.get("aliases") or ()]
            alternatives += item.get("patterns") or []
            skills.append(
                Skill(
                    name=item["skill"],
                    category=item["category"],
                    pattern=re.compile("|".join(f"(?:{a})" for a in alternatives), re.IGNORECASE),
                    sectors=frozenset(item.get("sectors") or ()),
                    ssk_id=item.get("ssk_id"),
                )
            )
        return cls(skills)

    def find(self, text: str, sectors: Iterable[str]) -> list[Skill]:
        sectors = list(sectors)
        return [skill for skill in self.skills if skill.found_in(text, sectors)]


def alias_pattern(alias: str) -> str:
    """A plain phrase as a whole-word pattern. A space also matches a hyphen or a line break."""
    body = r"[\s\-]+".join(re.escape(word) for word in alias.split())
    return rf"(?<!\w){body}(?!\w)"


# --- one ad -------------------------------------------------------------------------------------


@dataclass
class AnalysedAd:
    ad: JobAd
    role: RoleMatch
    skills: list[Skill]
    flags: list[str]

    @property
    def has_text(self) -> bool:
        return BANNER_ONLY not in self.flags


def skill_text(ad: JobAd) -> str:
    """The part of the ad about the job and the person wanted."""
    text = (ad.description_text or ad.requirements_text or "").replace("’", "'").replace("‘", "'")
    text = URL.sub(" ", text)
    if ad.company:
        text = re.sub(re.escape(ad.company), " ", text, flags=re.IGNORECASE)
    kept: list[str] = []
    skipping = False
    for line in text.splitlines():
        line = BULLET.sub("", line).strip()
        if SKIPPED_SECTION.match(line):
            skipping = True
        elif skipping and _is_heading(line):
            skipping = False
        if not skipping and line:
            kept.append(line)
    return "\n".join(kept)


def analyse(
    ads: Iterable[JobAd], taxonomy: RoleTaxonomy, lexicon: SkillLexicon, agriculture_keywords: Iterable[str]
) -> list[AnalysedAd]:
    agriculture = re.compile(
        r"\b(?:" + "|".join(re.escape(word) for word in agriculture_keywords) + ")", re.IGNORECASE
    )
    return [_analyse_ad(ad, taxonomy, lexicon, agriculture) for ad in ads]


def _analyse_ad(
    ad: JobAd, taxonomy: RoleTaxonomy, lexicon: SkillLexicon, agriculture: re.Pattern[str]
) -> AnalysedAd:
    text = skill_text(ad)
    flags = []
    if len(WORD.findall(text)) < MIN_WORDS:
        flags.append(BANNER_ONLY)
        skills = []
    else:
        skills = lexicon.find(text, ad.sectors)
        if not ad.requirements_text:
            flags.append(NO_REQUIREMENTS_SECTION)
    whole_ad = "\n".join(filter(None, [ad.job_title, ad.company, ad.description_text]))
    if "Agriculture" in ad.sectors and not agriculture.search(whole_ad):
        flags.append(NOT_AGRICULTURE)
    return AnalysedAd(ad, taxonomy.classify(ad.job_title, ad.sectors), skills, flags)


def _is_heading(line: str) -> bool:
    return bool(REQUIREMENT_HEADING.match(line) or JOB_SECTION.match(line) or SHORT_HEADING.match(line))


# --- the profile ----------------------------------------------------------------------------------


def build_profile(
    analysed: list[AnalysedAd],
    sources: list[dict],
    generated_at: str,
    include_inactive: bool = False,
    sectors: Sequence[str] = (),
) -> dict:
    """The profile. ``sectors`` are listed first and in that order, even with no ads yet."""
    by_role: dict[str, list[AnalysedAd]] = defaultdict(list)
    for item in analysed:
        by_role[item.role.role].append(item)
    roles = sorted(
        (_role_summary(name, items) for name, items in by_role.items()), key=lambda r: (-r["ads"], r["role"])
    )
    found = sorted({sector for item in analysed for sector in item.ad.sectors} - set(sectors))
    return {
        "generated_at": generated_at,
        "ad_statuses": list(STATUSES) if include_inactive else [ACTIVE],
        "sources": sources,
        "totals": {
            "ads": len(analysed),
            "ads_with_text": sum(item.has_text for item in analysed),
            "roles": len(roles),
            "unmapped_roles": sum(not role["mapped"] for role in roles),
            "unique_skills": len({skill.name for item in analysed for skill in item.skills}),
        },
        "sectors": [
            _sector_summary(sector, [item for item in analysed if sector in item.ad.sectors])
            for sector in [*sectors, *found]
        ],
        "skills": skill_demand(analysed),
        "roles": roles,
    }


def skill_demand(items: list[AnalysedAd]) -> list[dict]:
    """Each skill with the number of ads asking for it, and its share of the ads with readable text."""
    with_text = sum(item.has_text for item in items)
    counts = Counter(skill for item in items for skill in item.skills)
    return [
        {
            "skill": skill.name,
            "category": skill.category,
            "ssk_id": skill.ssk_id,
            "ads": count,
            "share": round(count / with_text, 3),
        }
        for skill, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].name))
    ]


def source_summary(storage: Storage, site: str, ads: list[JobAd]) -> dict:
    collected = [ad.collected_at for ad in ads if ad.site == site and ad.collected_at]
    checked = [entry["checked_at"] for entry in storage.listing_counts().get(site, {}).values()]
    return {
        "site": site,
        "ads": sum(ad.site == site for ad in ads),
        "last_collected": max(collected, default=None),  # newest ad downloaded
        "last_checked": max(checked, default=None),  # listing pages last read
    }


def _sector_summary(sector: str, items: list[AnalysedAd]) -> dict:
    return {
        "sector": sector,
        "ads": len(items),
        "ads_with_text": sum(item.has_text for item in items),
        "skills": skill_demand(items),
    }


def _role_summary(name: str, items: list[AnalysedAd]) -> dict:
    flags = Counter(flag for item in items for flag in item.flags)
    return {
        "role": name,
        "mapped": items[0].role.mapped,
        "sectors": sorted({sector for item in items for sector in item.ad.sectors}),
        "ads": len(items),
        "ads_with_text": sum(item.has_text for item in items),
        "titles": sorted({item.ad.job_title for item in items if item.ad.job_title}),
        "seniority": dict(Counter(item.role.seniority for item in items).most_common()),
        "experience": dict(Counter(item.ad.experience_level or NOT_STATED for item in items).most_common()),
        "skills": skill_demand(items),
        "flags": {flag: flags[flag] for flag in FLAG_TEXT if flags[flag]},
    }


# --- output ---------------------------------------------------------------------------------------


def render(profile: dict) -> str:
    totals = profile["totals"]
    scope = "Active ads only" if profile["ad_statuses"] == [ACTIVE] else "All ads: active, expired and removed"
    sources = ", ".join(
        f"**{s['site']}** ({_plural(s['ads'], 'ad')}, last collected {_when(s['last_collected'])})"
        for s in profile["sources"]
    )
    lines = [
        "# Skill demand profile",
        "",
        f"{scope} · generated {_when(profile['generated_at'])}",
        "",
        f"Sources: {sources or '–'}",
        "",
        f"**{_plural(totals['ads'], 'ad')} · {_plural(totals['roles'], 'role')} · "
        f"{_plural(totals['unique_skills'], 'different skill')}.** "
        f"{totals['ads_with_text']} of the ads have readable text; shares are out of those.",
        "",
        "## Roles",
        "",
        "| Role | Sectors | Ads | Most requested skills |",
        "|---|---|--:|---|",
    ]
    for role in profile["roles"]:
        top = ", ".join(skill["skill"] for skill in role["skills"][:5]) or "–"
        lines.append(f"| {_role_name(role)} | {', '.join(role['sectors'])} | {role['ads']} | {top} |")
    lines += ["", "## Most requested skills, all roles", "", *_skill_table(profile["skills"][:SKILLS_IN_REPORT], totals["ads_with_text"])]

    for role in profile["roles"]:
        lines += [
            "",
            f"## {_role_name(role)}: {_plural(role['ads'], 'ad')}",
            "",
            f"Sectors: {', '.join(role['sectors'])}. Seniority: {_counts(role['seniority'])}. "
            f"Experience asked: {_counts(role['experience'])}.",
        ]
        if role["titles"]:
            lines += ["", "Titles: " + "; ".join(role["titles"])]
        if role["flags"]:
            lines += ["", "Flags: " + ", ".join(f"{FLAG_TEXT[f]} ({n})" for f, n in role["flags"].items())]
        lines += ["", *_skill_table(role["skills"][:SKILLS_IN_REPORT], role["ads_with_text"])]

    lines += [
        "",
        "## Notes",
        "",
        "- A skill counts once per ad. Shares are out of the ads with readable text "
        "(banner-only flyers are left out).",
        "- Roles marked *unmapped* are job titles that match no role in config/role_taxonomy.yaml yet.",
        "- Skills come from config/skills_lexicon.yaml; a skill missing from it is not counted.",
        "",
    ]
    return "\n".join(lines)


def write_profile(
    storage: Storage,
    sites: Sequence[str],
    include_inactive: bool = False,
    *,
    taxonomy: RoleTaxonomy | None = None,
    lexicon: SkillLexicon | None = None,
) -> tuple[Path, Path]:
    """Write processed/skill_profile.md and processed/skill_profile.json."""
    ads = [ad for site in sites for ad in storage.read_jsonl(site)]
    if not include_inactive:
        ads = [ad for ad in ads if ad.status == ACTIVE]
    analysed = analyse(
        ads, taxonomy or RoleTaxonomy.load(), lexicon or SkillLexicon.load(), load_agriculture_keywords()
    )
    sources = [source_summary(storage, site, ads) for site in sites]
    profile = build_profile(analysed, sources, utc_now(), include_inactive, load_sectors())

    storage.processed_dir.mkdir(parents=True, exist_ok=True)
    json_path = storage.processed_dir / "skill_profile.json"
    json_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path = storage.processed_dir / "skill_profile.md"
    md_path.write_text(render(profile), encoding="utf-8")
    return md_path, json_path


def _skill_table(skills: list[dict], ads_with_text: int) -> list[str]:
    if not skills:
        return ["No skills found (no ad with readable requirements)."]
    lines = ["| Skill | Category | Ads requesting it |", "|---|---|--:|"]
    for skill in skills:
        lines.append(f"| {skill['skill']} | {skill['category']} | {skill['ads']} of {ads_with_text} ({skill['share']:.0%}) |")
    return lines


def _role_name(role: dict) -> str:
    return role["role"] if role["mapped"] else f"{role['role']} *(unmapped)*"


def _counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{label} ({count})" for label, count in counts.items()) or "–"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("" if count == 1 else "s")


def _when(iso: str | None) -> str:
    return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M UTC") if iso else "–"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the skill demand profile per job role (offline).")
    parser.add_argument("--site", default="all", help="a collected site, or 'all' (default)")
    parser.add_argument("--include-inactive", action="store_true", help="also count expired and removed ads")
    args = parser.parse_args(argv)
    sites = [name for name, site in load_sites().items() if site.enabled] if args.site == "all" else [args.site]
    paths = write_profile(Storage(load_settings().data_dir), sites, args.include_inactive)
    print("Wrote " + " and ".join(str(path) for path in paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
