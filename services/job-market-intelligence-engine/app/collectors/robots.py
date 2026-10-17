"""robots.txt rules for one site.

A URL may be fetched only if two parsers both allow it:

- Python's ``urllib.robotparser``, and
- an RFC 9309 matcher. ``robotparser`` reads only the first ``User-agent: *`` group and treats
  ``*`` and ``$`` literally, so on its own it allows URLs that sites such as ikman.lk disallow
  (e.g. ``?query=`` pages listed in a second ``*`` group).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser


@dataclass(frozen=True)
class Rule:
    allow: bool
    pattern: str

    def matches(self, path: str) -> bool:
        return _compile(self.pattern).match(path) is not None


@lru_cache(maxsize=512)
def _compile(pattern: str) -> re.Pattern[str]:
    """RFC 9309 path pattern: ``*`` matches any characters, a trailing ``$`` anchors the end."""
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile(regex + ("$" if anchored else ""))


@dataclass
class _Group:
    agents: list[str] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    crawl_delay: float | None = None
    has_body: bool = False  # set once a non-user-agent line follows the user-agent lines


def _parse_groups(text: str) -> list[_Group]:
    groups: list[_Group] = []
    current: _Group | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if current is None or current.has_body:
                current = _Group()
                groups.append(current)
            current.agents.append(value.lower())
            continue
        if current is None:
            continue  # rules before the first user-agent line belong to no group
        current.has_body = True
        if key in ("allow", "disallow") and value:  # an empty Disallow means "allow everything"
            current.rules.append(Rule(allow=key == "allow", pattern=value))
        elif key == "crawl-delay":
            try:
                current.crawl_delay = float(value)
            except ValueError:
                pass
    return groups


def _groups_for(groups: list[_Group], product: str) -> list[_Group]:
    """Groups naming the product token exactly, combined; otherwise all ``*`` groups, combined."""
    product = product.lower()
    named = [group for group in groups if product in group.agents]
    return named or [group for group in groups if "*" in group.agents]


class RobotsPolicy:
    def __init__(
        self,
        rules: list[Rule],
        crawl_delay: float | None = None,
        parser: RobotFileParser | None = None,
        user_agent: str = "",
    ) -> None:
        self._rules = rules
        self.crawl_delay = crawl_delay
        self._parser = parser
        self._user_agent = user_agent

    @classmethod
    def from_text(cls, text: str, user_agent: str) -> RobotsPolicy:
        product = user_agent.split("/", 1)[0]
        groups = _groups_for(_parse_groups(text), product)
        delays = [group.crawl_delay for group in groups if group.crawl_delay is not None]
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        return cls(
            rules=[rule for group in groups for rule in group.rules],
            crawl_delay=max(delays) if delays else None,
            parser=parser,
            user_agent=user_agent,
        )

    @classmethod
    def allow_all(cls) -> RobotsPolicy:
        return cls(rules=[])

    @classmethod
    def disallow_all(cls) -> RobotsPolicy:
        return cls(rules=[Rule(allow=False, pattern="/")])

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        if path == "/robots.txt":
            return True
        if self._parser is not None and not self._parser.can_fetch(self._user_agent, url):
            return False
        return self._rfc_allows(path)

    def _rfc_allows(self, path: str) -> bool:
        matching = [rule for rule in self._rules if rule.matches(path)]
        if not matching:
            return True
        # The longest pattern wins; on a tie, Allow wins (RFC 9309, section 2.2.2).
        return max(matching, key=lambda rule: (len(rule.pattern), rule.allow)).allow
