"""Job titles → canonical roles and seniority, using config/role_taxonomy.yaml.

A title often names more than one job ("HR Executive / HR Assistant", "Talent Acquisition
Specialist | Senior Executive - Talent Acquisition"). The first part of the title that matches a
role decides, so each ad counts once, under the job it names first. A title that matches no role
keeps its own cleaned title and is marked as unmapped, so the taxonomy can be extended.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.collectors.config import SERVICE_ROOT

DEFAULT_TAXONOMY = SERVICE_ROOT / "config" / "role_taxonomy.yaml"
UNKNOWN_TITLE = "Unknown title"

# Between two job titles in one ad title. " / " needs the spaces, so "UI/UX Designer" stays whole.
TITLE_SEPARATOR = re.compile(r"\s+/\s+|\s*\|\s*|\s*,\s*|\s+or\s+", re.IGNORECASE)
# Words in a title that say nothing about the job itself: "URGENT", "(Female)", "Vacancy".
TITLE_NOISE = re.compile(
    r"\((?:fe)?male\)|[-–—]\s*(?:fe)?male\b|\b(?:fe)?male\b"
    r"|\b(?:urgent(?:ly)?|immediate(?:ly)?|vacanc(?:y|ies)|wanted|required|hiring)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Role:
    name: str
    patterns: tuple[re.Pattern[str], ...]
    sectors: frozenset[str] = field(default_factory=frozenset)  # empty: ads from any sector

    def matches(self, title: str, sectors: Iterable[str]) -> bool:
        if self.sectors and not self.sectors.intersection(sectors):
            return False
        return any(pattern.search(title) for pattern in self.patterns)


@dataclass(frozen=True)
class RoleMatch:
    role: str
    mapped: bool  # False: the title matched no role in the taxonomy
    seniority: str


class RoleTaxonomy:
    def __init__(
        self,
        roles: list[Role],
        seniority: list[tuple[str, tuple[re.Pattern[str], ...]]],
        default_seniority: str,
    ) -> None:
        self.roles = roles
        self.seniority = seniority
        self.default_seniority = default_seniority

    @classmethod
    def load(cls, path: Path = DEFAULT_TAXONOMY) -> RoleTaxonomy:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        roles = [
            Role(
                name=item["role"],
                patterns=_compile(item["patterns"]),
                sectors=frozenset(item.get("sectors") or ()),
            )
            for item in data["roles"]
        ]
        seniority = [(item["level"], _compile(item["patterns"])) for item in data["seniority"]]
        return cls(roles, seniority, data["default_seniority"])

    def classify(self, title: str | None, sectors: Iterable[str]) -> RoleMatch:
        if not title or not title.strip():
            return RoleMatch(UNKNOWN_TITLE, mapped=False, seniority=self.default_seniority)
        sectors = list(sectors)
        parts = title_parts(title)
        for part in parts:
            role = next((role for role in self.roles if role.matches(part, sectors)), None)
            if role:
                return RoleMatch(role.name, mapped=True, seniority=self.seniority_of(part))
        return RoleMatch(clean_title(parts[0]), mapped=False, seniority=self.seniority_of(parts[0]))

    def seniority_of(self, title: str) -> str:
        for level, patterns in self.seniority:
            if any(pattern.search(title) for pattern in patterns):
                return level
        return self.default_seniority


def title_parts(title: str) -> list[str]:
    """The job titles named in one ad title, in order."""
    parts = [part.strip() for part in TITLE_SEPARATOR.split(title)]
    return [part for part in parts if part] or [title.strip()]


def clean_title(title: str) -> str:
    """A readable role name for an unmapped title: "URGENT - BARISTA (Female)" → "Barista"."""
    cleaned = " ".join(TITLE_NOISE.sub(" ", title).split()).strip(" -–—/|,:")
    if cleaned.isupper():
        cleaned = cleaned.title()
    return cleaned or title.strip()


def _compile(patterns: list[str]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)
