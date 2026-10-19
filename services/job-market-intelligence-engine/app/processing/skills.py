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
import logging
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field, replace
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
from app.collectors.config import Settings
from app.collectors.storage import Storage
from app.collectors.text_utils import BULLET, REQUIREMENT_HEADING
from app.integrations.ssks import COUNTED, PENDING, SSKSClient, SSKSMatch, normalize_key
from app.processing.ner_extractor import NerExtractor, load_ner
from app.processing.roles import RoleMatch, RoleTaxonomy

DEFAULT_LEXICON = SERVICE_ROOT / "config" / "skills_lexicon.yaml"

log = logging.getLogger(__name__)
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
VERIFIED_CATEGORY = "Verified in SSKS"  # category of skills counted from NER mentions
MATCH_TYPES = ("exact", "alias", "fuzzy", "unmatched", "pending")
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
    ssk_id: str | None = None  # set by hand in the lexicon; otherwise found through SSKS
    aliases: tuple[str, ...] = ()

    def found_in(self, text: str, sectors: Iterable[str]) -> bool:
        return self.allowed_in(sectors) and self.pattern.search(text) is not None

    def allowed_in(self, sectors: Iterable[str]) -> bool:
        return not self.sectors or bool(self.sectors.intersection(sectors))


@dataclass(frozen=True)
class LexiconMention:
    skill: Skill
    text: str  # as written in the ad
    start: int
    end: int


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
                    aliases=tuple(item.get("aliases") or ()),
                )
            )
        return cls(skills)

    def find(self, text: str, sectors: Iterable[str]) -> list[Skill]:
        sectors = list(sectors)
        return [skill for skill in self.skills if skill.found_in(text, sectors)]

    def find_mentions(self, text: str, sectors: Iterable[str]) -> list[LexiconMention]:
        """Every place a skill is mentioned, with its character offsets (for evaluation and SSKS)."""
        sectors = list(sectors)
        return [
            LexiconMention(skill, match.group(0), match.start(), match.end())
            for skill in self.skills
            if skill.allowed_in(sectors)
            for match in skill.pattern.finditer(text)
            if match.end() > match.start()
        ]


def alias_pattern(alias: str) -> str:
    """A plain phrase as a whole-word pattern. A space also matches a hyphen or a line break."""
    body = r"[\s\-]+".join(re.escape(word) for word in alias.split())
    return rf"(?<!\w){body}(?!\w)"


# --- one ad -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DemandSkill:
    """A skill as counted in demand: a lexicon skill, or (ner mode) a skill that SSKS verified."""

    name: str
    category: str
    ssk_ids: tuple[str, ...] = ()
    source: str = "lexicon"  # lexicon | ner


@dataclass(frozen=True)
class FoundSkill:
    """One skill mention in one ad, with its SSKS match (written to processed/ad_skills.jsonl)."""

    extractor: str  # lexicon | ner
    text: str  # as written in the ad
    start: int
    end: int
    label: str  # the lexicon category, or the NER label (SKILL / KNOWLEDGE)
    lexicon_skill: str | None
    ssks: SSKSMatch = PENDING


@dataclass
class Extraction:
    """How skills are found: SKILLBRIDGE_SKILL_EXTRACTOR, the NER model and the SSKS client."""

    mode: str = "lexicon"  # lexicon | ner | both
    ner: NerExtractor | None = None
    ssks: SSKSClient | None = None
    lexicon_ids: dict[str, tuple[str, ...]] = field(default_factory=dict)  # set while linking
    lexicon_name_match: dict[str, str] = field(default_factory=dict)  # lexicon name → SSKS match type


@dataclass
class AnalysedAd:
    ad: JobAd
    role: RoleMatch
    skills: list[DemandSkill]  # counted in demand
    flags: list[str]
    found: list[FoundSkill] = field(default_factory=list)  # every mention, counted or not
    unverified: list[FoundSkill] = field(default_factory=list)  # NER mentions SSKS didn't verify

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
    ads: Iterable[JobAd],
    taxonomy: RoleTaxonomy,
    lexicon: SkillLexicon,
    agriculture_keywords: Iterable[str],
    extraction: Extraction | None = None,
) -> list[AnalysedAd]:
    extraction = extraction or Extraction()
    agriculture = re.compile(
        r"\b(?:" + "|".join(re.escape(word) for word in agriculture_keywords) + ")", re.IGNORECASE
    )
    items = [_analyse_ad(ad, taxonomy, lexicon, agriculture, extraction) for ad in ads]
    _link(items, lexicon, extraction)
    return items


def _analyse_ad(
    ad: JobAd, taxonomy: RoleTaxonomy, lexicon: SkillLexicon, agriculture: re.Pattern[str], extraction: Extraction
) -> AnalysedAd:
    text = skill_text(ad)
    flags, found = [], []
    if len(WORD.findall(text)) < MIN_WORDS:
        flags.append(BANNER_ONLY)
    else:
        if extraction.mode in ("lexicon", "both"):
            found += [
                FoundSkill("lexicon", m.text, m.start, m.end, m.skill.category, m.skill.name)
                for m in lexicon.find_mentions(text, ad.sectors)
            ]
        if extraction.mode in ("ner", "both") and extraction.ner is not None:
            found += [FoundSkill("ner", m.text, m.start, m.end, m.label, None) for m in extraction.ner.extract(text)]
        if not ad.requirements_text:
            flags.append(NO_REQUIREMENTS_SECTION)
    whole_ad = "\n".join(filter(None, [ad.job_title, ad.company, ad.description_text]))
    if "Agriculture" in ad.sectors and not agriculture.search(whole_ad):
        flags.append(NOT_AGRICULTURE)
    return AnalysedAd(ad, taxonomy.classify(ad.job_title, ad.sectors), [], flags, found)


def _link(items: list[AnalysedAd], lexicon: SkillLexicon, extraction: Extraction) -> None:
    """Look every mention up in SSKS (one batch for all ads, cached), then decide what counts.

    lexicon: every lexicon skill counts, with the SSKS IDs of its name and aliases.
    ner:     only mentions SSKS matched exactly or through a verified alias count, under the SSKS
             name; the others are "unverified" (shown, never counted).
    both:    lexicon skills, plus verified NER skills the lexicon didn't already give that ad.
    """
    names = {f.text for item in items for f in item.found}
    if extraction.mode != "ner":
        names.update(n for skill in lexicon.skills for n in (skill.name, *skill.aliases))
    matches = extraction.ssks.lookup(names) if extraction.ssks else {}
    lexicon_ids = {skill.name: _lexicon_ids(skill, matches) for skill in lexicon.skills}
    extraction.lexicon_ids = lexicon_ids
    extraction.lexicon_name_match = {s.name: matches.get(s.name, PENDING).match_type for s in lexicon.skills}
    by_name = {skill.name: skill for skill in lexicon.skills}

    for item in items:
        item.found = [replace(f, ssks=matches.get(f.text, PENDING)) for f in item.found]
        lexicon_found = [f for f in item.found if f.extractor == "lexicon"]
        skills = [
            DemandSkill(name, by_name[name].category, lexicon_ids[name])
            for name in dict.fromkeys(f.lexicon_skill for f in lexicon_found)
        ]
        covered = {ssk_id for skill in skills for ssk_id in skill.ssk_ids}
        unverified: dict[str, FoundSkill] = {}
        for f in (f for f in item.found if f.extractor == "ner"):
            if f.ssks.counted:
                if f.ssks.ssk_id not in covered:
                    skills.append(DemandSkill(f.ssks.preferred_name, VERIFIED_CATEGORY, (f.ssks.ssk_id,), "ner"))
                    covered.add(f.ssks.ssk_id)
            elif not any(f.start < l.end and l.start < f.end for l in lexicon_found):
                unverified.setdefault(normalize_key(f.text), f)
        item.skills = skills
        item.unverified = list(unverified.values())


def _lexicon_ids(skill: Skill, matches: dict[str, SSKSMatch]) -> tuple[str, ...]:
    """SSKS IDs of a lexicon skill: set by hand in the lexicon, or matched by its name or aliases."""
    if skill.ssk_id:
        return (skill.ssk_id,)
    ids = {m.ssk_id for n in (skill.name, *skill.aliases) if (m := matches.get(n)) and m.counted}
    return tuple(sorted(ids))


def _is_heading(line: str) -> bool:
    return bool(REQUIREMENT_HEADING.match(line) or JOB_SECTION.match(line) or SHORT_HEADING.match(line))


# --- the profile ----------------------------------------------------------------------------------


def build_profile(
    analysed: list[AnalysedAd],
    sources: list[dict],
    generated_at: str,
    include_inactive: bool = False,
    sectors: Sequence[str] = (),
    extraction: dict | None = None,
) -> dict:
    """The profile. ``sectors`` are listed first and in that order, even with no ads yet.
    ``extraction`` describes how skills were found (see ``extraction_summary``)."""
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
        "extraction": extraction or extraction_summary(analysed, Extraction(), None),
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
        "unverified": unverified_skills(analysed),
        "roles": roles,
    }


def skill_demand(items: list[AnalysedAd]) -> list[dict]:
    """Each skill with the number of ads asking for it, and its share of the ads with readable text.

    ``ssk_id`` is set when the skill has exactly one SSKS ID; ``ssk_ids`` lists all of them (a
    lexicon skill such as "Docker & Kubernetes" can match several SSKS skills)."""
    with_text = sum(item.has_text for item in items)
    counts = Counter(skill for item in items for skill in item.skills)
    return [
        {
            "skill": skill.name,
            "category": skill.category,
            "ssk_id": skill.ssk_ids[0] if len(skill.ssk_ids) == 1 else None,
            "ssk_ids": list(skill.ssk_ids),
            "source": skill.source,
            "ads": count,
            "share": round(count / with_text, 3),
        }
        for skill, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].name))
    ]


def unverified_skills(items: list[AnalysedAd]) -> list[dict]:
    """NER mentions SSKS didn't verify: shown with their ad counts, but not part of demand."""
    ads: Counter[str] = Counter()
    seen: dict[str, list[FoundSkill]] = defaultdict(list)
    for item in items:
        for found in item.unverified:
            key = normalize_key(found.text)
            ads[key] += 1
            seen[key].append(found)
    return [
        {
            "text": Counter(f.text for f in seen[key]).most_common(1)[0][0],
            "ads": count,
            "match_type": Counter(f.ssks.match_type for f in seen[key]).most_common(1)[0][0],
            "suggestion": next((f.ssks.suggestion for f in seen[key] if f.ssks.suggestion), None),
        }
        for key, count in sorted(ads.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


def extraction_summary(items: list[AnalysedAd], extraction: Extraction, lexicon: SkillLexicon | None) -> dict:
    """How skills were found, and how many of the mentions SSKS matched (measured on this run)."""
    found = [f for item in items for f in item.found]
    by_type = Counter(f.ssks.match_type for f in found)
    checked = extraction.ssks is not None
    summary = {
        "extractor": extraction.mode,
        "ssks_checked": checked,
        "ssks_reachable": extraction.ssks.reachable if checked else None,
        "mentions": len(found),
        "mention_match_types": {t: by_type[t] for t in MATCH_TYPES} if checked else None,
        "mention_match_rate": round(sum(by_type[t] for t in COUNTED) / len(found), 3) if checked and found else None,
    }
    if checked and lexicon is not None and extraction.mode != "ner":
        # Lexicon skills with at least one SSKS ID (by name or verified alias), out of all of them.
        summary["lexicon_skills"] = len(lexicon.skills)
        summary["lexicon_skills_linked"] = sum(1 for ids in extraction.lexicon_ids.values() if ids)
    return summary


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
        "unverified": unverified_skills(items),
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
        "unverified": unverified_skills(items),
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
        _extraction_line(profile.get("extraction") or {}),
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
        if role.get("unverified"):
            lines += ["", "Unverified (found by NER, not in SSKS; not counted): " + ", ".join(
                f"{u['text']} ({u['ads']})" for u in role["unverified"][:SKILLS_IN_REPORT]
            )]

    lines += [
        "",
        "## Notes",
        "",
        "- A skill counts once per ad. Shares are out of the ads with readable text "
        "(banner-only flyers are left out).",
        "- Roles marked *unmapped* are job titles that match no role in config/role_taxonomy.yaml yet.",
        "- lexicon: skills come from config/skills_lexicon.yaml; a skill missing from it is not counted. "
        "ner: only skills the Shared Skill Knowledge Service matches exactly or through a verified "
        "alias are counted; the rest are listed as unverified.",
        "",
    ]
    return "\n".join(lines)


def _extraction_line(extraction: dict) -> str:
    line = f"Skills found by: **{extraction.get('extractor', 'lexicon')}**."
    if not extraction.get("ssks_checked"):
        return line + " Not linked to the Shared Skill Knowledge Service (SKILLBRIDGE_SSKS_URL not set)."
    if extraction.get("ssks_reachable") is False:
        line += " SSKS was not reachable: unmatched mentions stay pending until the next run."
    rate = extraction.get("mention_match_rate")
    if rate is not None:
        line += f" SSKS matched {rate:.0%} of the {extraction['mentions']} skill mentions exactly or by alias."
    if "lexicon_skills" in extraction:
        line += (f" {extraction['lexicon_skills_linked']} of the {extraction['lexicon_skills']} lexicon skills "
                 f"have an SSKS ID.")
    return line


def write_profile(
    storage: Storage,
    sites: Sequence[str],
    include_inactive: bool = False,
    *,
    taxonomy: RoleTaxonomy | None = None,
    lexicon: SkillLexicon | None = None,
    extraction: Extraction | None = None,
) -> tuple[Path, Path]:
    """Write processed/skill_profile.md and .json (active ads, unless ``include_inactive``), and, for
    every stored ad including expired and removed ones (their history), processed/ad_skills.jsonl
    (every skill mention) and processed/ad_analysis.jsonl (role, seniority, flags)."""
    all_ads = [ad for site in sites for ad in storage.read_jsonl(site)]
    lexicon = lexicon or SkillLexicon.load()
    extraction = extraction or Extraction()
    analysed_all = analyse(all_ads, taxonomy or RoleTaxonomy.load(), lexicon, load_agriculture_keywords(), extraction)
    analysed = analysed_all if include_inactive else [item for item in analysed_all if item.ad.status == ACTIVE]
    ads = [item.ad for item in analysed]
    sources = [source_summary(storage, site, ads) for site in sites]
    profile = build_profile(
        analysed, sources, utc_now(), include_inactive, load_sectors(),
        extraction_summary(analysed, extraction, lexicon),
    )

    storage.processed_dir.mkdir(parents=True, exist_ok=True)
    write_ad_skills(storage.processed_dir / "ad_skills.jsonl", analysed_all, extraction)
    write_ad_analysis(storage.processed_dir / "ad_analysis.jsonl", analysed_all)
    json_path = storage.processed_dir / "skill_profile.json"
    json_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path = storage.processed_dir / "skill_profile.md"
    md_path.write_text(render(profile), encoding="utf-8")
    return md_path, json_path


def write_ad_skills(path: Path, analysed: list[AnalysedAd], extraction: Extraction) -> None:
    """One row per skill mention: the raw text, where it is, and its SSKS ID and match type.
    Lexicon mentions also carry their lexicon skill's SSKS IDs and the match type of its name.
    ``counted_as`` is the skill the mention counts as in demand (None: not counted)."""
    with path.open("w", encoding="utf-8") as out:
        for item in analysed:
            counted_by_id = {ssk_id: skill.name for skill in item.skills for ssk_id in skill.ssk_ids}
            for found in item.found:
                row = {"site": item.ad.site, "job_id": item.ad.job_id, **asdict(found)}
                row["counted_as"] = (
                    found.lexicon_skill if found.extractor == "lexicon"
                    else counted_by_id.get(found.ssks.ssk_id) if found.ssks.counted else None
                )
                row.update(row.pop("ssks"))  # match_type, ssk_id, preferred_name, suggestion
                if found.lexicon_skill:
                    row["lexicon_ssk_ids"] = list(extraction.lexicon_ids.get(found.lexicon_skill, ()))
                    row["lexicon_name_match_type"] = extraction.lexicon_name_match.get(found.lexicon_skill, "pending")
                out.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_ad_analysis(path: Path, analysed: list[AnalysedAd]) -> None:
    """One row per ad: its role, seniority and flags (for the database loader)."""
    with path.open("w", encoding="utf-8") as out:
        for item in analysed:
            out.write(json.dumps({
                "site": item.ad.site,
                "job_id": item.ad.job_id,
                "role": item.role.role,
                "role_mapped": item.role.mapped,
                "seniority": item.role.seniority,
                "has_text": item.has_text,
                "flags": item.flags,
            }, ensure_ascii=False) + "\n")


def extraction_from_settings(settings: Settings, storage: Storage) -> Extraction:
    """The extractor chosen in the settings. A NER mode without a usable model falls back to the
    lexicon (logged), so a profile is always written."""
    ssks = (
        SSKSClient(settings.ssks_url, cache_path=storage.processed_dir / "ssks_cache.json")
        if settings.ssks_url else None
    )
    if settings.skill_extractor == "lexicon":
        return Extraction("lexicon", ssks=ssks)
    if settings.ner_model is None:
        log.error("SKILLBRIDGE_SKILL_EXTRACTOR=%s needs SKILLBRIDGE_NER_MODEL; using the lexicon", settings.skill_extractor)
        return Extraction("lexicon", ssks=ssks)
    try:
        ner = load_ner(settings.ner_model)
    except (OSError, ImportError) as exc:
        log.error("NER model not loaded (%s); using the lexicon", exc)
        return Extraction("lexicon", ssks=ssks)
    if ssks is None:
        log.warning("No SKILLBRIDGE_SSKS_URL: NER skills can't be verified, so none are counted in demand")
    return Extraction(settings.skill_extractor, ner=ner, ssks=ssks)


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
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sites = [name for name, site in load_sites().items() if site.enabled] if args.site == "all" else [args.site]
    settings = load_settings()
    storage = Storage(settings.data_dir)
    paths = write_profile(storage, sites, args.include_inactive, extraction=extraction_from_settings(settings, storage))
    print("Wrote " + " and ".join(str(path) for path in paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
