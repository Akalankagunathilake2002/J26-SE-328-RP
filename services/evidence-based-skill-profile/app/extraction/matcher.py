"""Dictionary skill matching with spaCy PhraseMatcher (TAF task 4, first method).

Every skill name and alias in clean_skills.csv becomes a phrase pattern. Terms of 2 characters or
fewer ("C", "R", "Go", "AI") are real skills that are also common words or letters, so they are
matched case-sensitively and as whole tokens only; longer terms ignore case.

matcher_rules.csv (hand-written) adjusts single terms that are also ordinary words:
`exact_case` matches the term only with the same capitals ("Ada" but not "ADA"),
`skip` never matches the term (the skill can still be found by its other names).
"""
import csv
from dataclasses import dataclass
from pathlib import Path

import spacy
from spacy.matcher import PhraseMatcher
from spacy.util import compile_infix_regex

METHOD = "dictionary"
SHORT_TERM_LENGTH = 2
EXACT_CASE = "exact_case"
SKIP = "skip"
SEPARATOR = "|"
# Split "JavaScript(ES6)" and "HTML/CSS" into separate tokens.
EXTRA_INFIXES = [r"[()\[\]{}/|]"]


@dataclass(frozen=True)
class SkillEntry:
    skill_id: str
    name: str
    aliases: tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class SkillMatch:
    skill_id: str
    name: str
    matched_text: str
    start: int
    end: int
    by_name: bool


def load_entries(path: Path) -> list[SkillEntry]:
    with path.open(encoding="utf-8", newline="") as f:
        return [
            SkillEntry(
                skill_id=row["skill_id"],
                name=row["name"],
                aliases=tuple(a for a in row["aliases"].split(SEPARATOR) if a.strip()),
                description=row.get("description", ""),
            )
            for row in csv.DictReader(f)
        ]


def load_rules(path: Path) -> dict[str, str]:
    """Term (lower case) → rule, from matcher_rules.csv; no file means no rules."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        rules = {row["term"].strip().lower(): row["rule"].strip() for row in csv.DictReader(f)}
    unknown = set(rules.values()) - {EXACT_CASE, SKIP}
    if unknown:
        raise ValueError(f"Unknown matcher rule(s) in {path}: {sorted(unknown)}")
    return rules


def _make_nlp() -> spacy.Language:
    nlp = spacy.blank("en")
    infixes = list(nlp.Defaults.infixes) + EXTRA_INFIXES
    nlp.tokenizer.infix_finditer = compile_infix_regex(infixes).finditer
    return nlp


class SkillMatcher:
    def __init__(self, entries: list[SkillEntry], rules: dict[str, str] | None = None):
        rules = rules or {}
        self.nlp = _make_nlp()
        self.names = {entry.skill_id: entry.name for entry in entries}
        self._any_case = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._exact_case = PhraseMatcher(self.nlp.vocab, attr="ORTH")
        for entry in entries:
            for term, kind in [(entry.name, "name")] + [(a, "alias") for a in entry.aliases]:
                term = term.strip()
                rule = rules.get(term.lower())
                if rule == SKIP:
                    continue
                exact = rule == EXACT_CASE or len(term) <= SHORT_TERM_LENGTH
                matcher = self._exact_case if exact else self._any_case
                matcher.add(f"{entry.skill_id}{SEPARATOR}{kind}", [self.nlp.make_doc(term)])

    @classmethod
    def from_csv(cls, path: Path, rules_path: Path | None = None) -> "SkillMatcher":
        rules = load_rules(rules_path) if rules_path else {}
        return cls(load_entries(path), rules)

    def find(self, text: str) -> list[SkillMatch]:
        """Return non-overlapping skill matches in text order.

        When matches overlap, the longest wins ("Microsoft Excel" beats "Excel"). When one span
        matches several skills, a skill name beats an alias, then the lowest ID wins.
        """
        doc = self.nlp.make_doc(text)
        candidates = []
        for matcher in (self._any_case, self._exact_case):
            for match_id, start, end in matcher(doc):
                skill_id, kind = self.nlp.vocab.strings[match_id].split(SEPARATOR)
                candidates.append((start, end, skill_id, kind == "name"))
        candidates.sort(key=lambda c: (-(c[1] - c[0]), not c[3], c[2], c[0]))

        taken: set[int] = set()
        matches = []
        for start, end, skill_id, by_name in candidates:
            tokens = set(range(start, end))
            if tokens & taken or _stray_letter(doc, start, end):
                continue
            taken |= tokens
            span = doc[start:end]
            matches.append(SkillMatch(
                skill_id=skill_id,
                name=self.names[skill_id],
                matched_text=span.text,
                start=span.start_char,
                end=span.end_char,
                by_name=by_name,
            ))
        return sorted(matches, key=lambda m: m.start)


def _stray_letter(doc, start: int, end: int) -> bool:
    """A one-letter skill (R, C) next to another lone letter or "&" is not the skill.

    It is part of letter-spaced text ("I N T E R") or an abbreviation such as "R & D".
    """
    if end - start != 1 or len(doc[start].text) != 1:
        return False
    neighbours = [doc[i].text for i in (start - 1, end) if 0 <= i < len(doc)]
    return any(text == "&" or (len(text) == 1 and text.isalpha()) for text in neighbours)
