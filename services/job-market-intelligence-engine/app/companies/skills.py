"""Finds what a company's job description asks for, with the same skill list as Market Pulse.

- Skills: every lexicon skill the title or description mentions, in the order they first appear. A skill is
  PREFERRED when every mention is under a "Nice to have:" style heading or on a line that says "preferred",
  "an advantage" and so on; otherwise REQUIRED. The company checks and changes these before publishing.
- Education: the first degree, diploma or exam the text asks for (a required line before a preferred one).
- Certificates and licences: the lexicon's other qualifications (e.g. "Driving licence").
- Minimum years: the first "N years" / "N+ yrs" / "N-M years" in the text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.database.role_profiles import EDUCATION, QUALIFICATION, SKILL_TYPE
from app.processing.skills import SkillLexicon

PREFERRED_WORDS = re.compile(
    r"nice[ \t]+to[ \t]+have|preferred|preferable|desirable|bonus|advantage|advantageous|a[ \t]+plus|plus[ \t]+point",
    re.IGNORECASE,
)
YEARS = re.compile(r"\b(\d{1,2})\s*\+?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?(?:years?|yrs?)\b", re.IGNORECASE)
HEADING = re.compile(r"^[^:\n]{2,60}:$")

# The education choices a company can pick: label → (SLQF level, completion), as C01's role profiles use.
EDUCATION_OPTIONS = dict(EDUCATION)
EDUCATION_LABELS = {code: label for label, code in EDUCATION.items()}


@dataclass
class DetectedSkill:
    name: str
    skill_type: str  # TECHNICAL | BEHAVIOURAL
    category: str  # the lexicon category, e.g. "Tool" or "Soft skill"
    importance: str  # REQUIRED | PREFERRED
    in_skill_list: bool = True


@dataclass
class Detected:
    skills: list[DetectedSkill] = field(default_factory=list)
    education: str | None = None  # a label of EDUCATION_OPTIONS
    certifications: list[str] = field(default_factory=list)
    minimum_years: int | None = None


def detect(title: str, description: str, sector: str | None, lexicon: SkillLexicon) -> Detected:
    sectors = [sector] if sector else []
    skills: dict[str, DetectedSkill] = {}
    education: list[tuple[bool, str]] = []  # (preferred, label) in reading order
    certifications: list[str] = []
    preferred_section = False
    for raw in [title, *description.splitlines()]:
        line = raw.strip().lstrip("-•*·").strip()
        if not line:
            continue
        if HEADING.match(line):
            preferred_section = bool(PREFERRED_WORDS.search(line))
            continue
        preferred = preferred_section or bool(PREFERRED_WORDS.search(line))
        mentions = sorted(lexicon.find_mentions(line, sectors), key=lambda m: m.start)
        for mention in mentions:
            skill = mention.skill
            if skill.category == QUALIFICATION:
                if skill.name in EDUCATION_OPTIONS:
                    education.append((preferred, skill.name))
                elif skill.name not in certifications:
                    certifications.append(skill.name)
                continue
            known = skills.get(skill.name)
            if known is None:
                skills[skill.name] = DetectedSkill(skill.name, SKILL_TYPE.get(skill.category, "TECHNICAL"), skill.category,
                                                   "PREFERRED" if preferred else "REQUIRED")
            elif not preferred:
                known.importance = "REQUIRED"
    years = YEARS.search(description)
    chosen = next((label for preferred, label in education if not preferred), None) or (education[0][1] if education else None)
    return Detected(list(skills.values()), chosen, certifications, int(years.group(1)) if years else None)


def canonical_skill(name: str, lexicon: SkillLexicon) -> tuple[str, str, bool] | None:
    """(name, skill type, in the skill list) for a skill a company typed: the lexicon's name when the text is a
    lexicon skill or one of its aliases. None for a qualification (those go to education or certificates)."""
    key = " ".join(name.split()).casefold()
    for skill in lexicon.skills:
        if key == skill.name.casefold() or key in (alias.casefold() for alias in skill.aliases):
            if skill.category == QUALIFICATION:
                return None
            return skill.name, SKILL_TYPE.get(skill.category, "TECHNICAL"), True
    return " ".join(name.split()), "TECHNICAL", False
