"""Turning ad pages into clean text, and removing personal data from it.

Processed data keeps only the company name: e-mail addresses, phone numbers, contact lines and
titled names (Mr/Ms/Dr …) are removed from every text field.
"""

from __future__ import annotations

import re
from dataclasses import replace

from bs4 import BeautifulSoup

from app.collectors.models import JobAd

SEP = r"[\s\-./()]*"  # what may sit between the digits of a phone number

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(
    # Sri Lankan: 0 or (+/00)94, an area or mobile prefix (never 0), then 8 more digits.
    rf"(?<![\w+])(?:(?:\+|00)?94{SEP}|0)[1-9](?:{SEP}\d){{8}}(?!\d)"
    # Other international numbers.
    rf"|(?<![\w+])\+\d(?:{SEP}\d){{7,14}}(?!\d)"
)
# A contact line starts with one of these words and contains a colon, a digit or an "@"
# ("Contact centre experience required" is a requirement, not a contact line).
CONTACT_LINE = re.compile(
    r"^[ \t]*(?:contact(?:[ \t]+(?:person|us|details|number|no\.?))?|call(?:[ \t]+us)?"
    r"|tel(?:ephone)?|mobile|phone|hotline|whats[ \t]*app|fax)\b(?=[^\n]*[:\d@])[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
TITLED_NAME = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Dr|Prof)\.?[ \t]+(?:[A-Z][\w.'-]*[ \t]?){1,3}")

# A heading stands on its own line, or ends with ":" followed by content on the same line.
REQUIREMENT_HEADING = re.compile(
    r"^(?:job[ \t]+|minimum[ \t]+|basic[ \t]+|key[ \t]+|essential[ \t]+)?"
    r"(?:requirements?|qualifications?(?:[ \t]*(?:&|and)[ \t]*experience)?"
    r"|(?:required[ \t]+)?skills(?:[ \t]*(?:&|and)[ \t]*(?:competencies|experience))?"
    r"|(?:the[ \t]+)?ideal[ \t]+candidate|candidate[ \t]+profile|eligibility"
    r"|you[ \t]+(?:should|must)[ \t]+have"
    r"|what[ \t]+(?:we(?:'re|[ \t]+are)[ \t]+looking[ \t]+for|you(?:'ll)?[ \t]+need))"
    r"[ \t]*(?:[:\-–][ \t]*(?P<rest>.*))?$",
    re.IGNORECASE,
)
SECTION_END = re.compile(
    r"^(?:benefits|perks|(?:what[ \t]+)?we[ \t]+offer|how[ \t]+to[ \t]+apply|to[ \t]+apply"
    r"|apply[ \t]+(?:now|before)|about[ \t]+(?:us|the[ \t]+company)|salary|remuneration|privacy"
    r"|closing[ \t]+date)\b",
    re.IGNORECASE,
)

YEARS = r"years?"
EXPERIENCE_PATTERNS = [
    (re.compile(rf"(\d{{1,2}})\s*(?:-|–|to)\s*(\d{{1,2}})\s*\+?\s*{YEARS}", re.I), "{0}–{1} years"),
    (re.compile(rf"(\d{{1,2}})\s*(?:\+|plus)\s*{YEARS}", re.I), "{0}+ years"),
    (
        re.compile(rf"(?:minimum|at\s+least|over|more\s+than)\s+(?:of\s+)?(\d{{1,2}})\s*{YEARS}", re.I),
        "{0}+ years",
    ),
    (re.compile(rf"(\d{{1,2}})\s*{YEARS}", re.I), "{0} years"),
]
MAX_PLAUSIBLE_YEARS = 15  # OCR often drops dashes ("1–6 years" becomes "16 years")

SALARY_LINE = re.compile(r"^[ \t]*(?:salary|remuneration)[ \t]*[:\-–][ \t]*(.+)$", re.I | re.M)
SALARY_AMOUNT = re.compile(
    r"(?:Rs\.?|LKR)\s*[\d,]+(?:\.\d+)?(?:\s*(?:-|–|to)\s*(?:Rs\.?|LKR)?\s*[\d,]+(?:\.\d+)?)?", re.I
)


def html_to_text(html: str) -> str:
    """Visible text of an HTML fragment, one line per block, blank lines collapsed."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return _tidy_lines(soup.get_text("\n"))


def scrub_personal_data(text: str | None) -> str | None:
    if not text:
        return text
    text = EMAIL.sub("[email removed]", text)
    text = PHONE.sub("[phone removed]", text)
    text = CONTACT_LINE.sub("", text)
    text = TITLED_NAME.sub("[name removed] ", text)
    return _tidy_lines(text) or None


def extract_requirements(text: str | None) -> str | None:
    """The part of an ad saying what the employer wants, if it has a recognisable heading."""
    if not text:
        return None
    collected: list[str] = []
    inside = False
    for line in text.splitlines():
        heading = REQUIREMENT_HEADING.match(line.strip())
        if heading:
            inside = True
            if heading.group("rest"):
                collected.append(heading.group("rest").strip())
        elif inside and SECTION_END.match(line.strip()):
            break
        elif inside:
            collected.append(line)
    return "\n".join(collected) or None


def extract_experience(text: str | None) -> str | None:
    """Experience asked for, e.g. "2+ years" or "1–3 years". Implausible values are ignored."""
    if not text:
        return None
    for sentence in re.split(r"[\n;]|\.(?!\d)", text):
        if "experience" not in sentence.lower():
            continue
        for pattern, label in EXPERIENCE_PATTERNS:
            for match in pattern.finditer(sentence):
                if all(int(number) <= MAX_PLAUSIBLE_YEARS for number in match.groups()):
                    return label.format(*match.groups())
    return None


def extract_salary(text: str | None) -> str | None:
    if not text:
        return None
    line = SALARY_LINE.search(text)
    if line:
        return line.group(1).strip()[:100]
    amount = SALARY_AMOUNT.search(text)
    return amount.group(0).strip() if amount else None


def clean_ad(ad: JobAd) -> JobAd:
    """Fill requirements, experience and salary from the description, then remove personal data."""
    requirements = ad.requirements_text or extract_requirements(ad.description_text)
    return replace(
        ad,
        description_text=scrub_personal_data(ad.description_text),
        requirements_text=scrub_personal_data(requirements),
        experience_level=ad.experience_level or extract_experience(requirements or ad.description_text),
        salary_text=ad.salary_text or extract_salary(ad.description_text),
    )


def _tidy_lines(text: str) -> str:
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join(line for line in lines if line)
