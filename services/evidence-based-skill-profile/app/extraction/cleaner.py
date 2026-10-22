"""Clean raw document text (TAF task 3)."""
import re
import unicodedata

from app.extraction.sections import heading_type

# Text that was saved as UTF-8 and read back as Windows-1252.
MOJIBAKE = {
    "ï¼": " ",
    "â€™": "'",
    "â€˜": "'",
    "â€œ": '"',
    "â€\x9d": '"',
    "â€“": "-",
    "â€”": "-",
    "â€¢": "",
    "Â": "",
}
INVISIBLE = re.compile(r"[​-‏⁠﻿­]")
BULLET = re.compile(r"^[\s•●○◦▪▫■□‣⁃∙·\-–—*>➢➤✓✔]+")
# Letter-spaced titles on certificates and posters: "C o m p e t i t i o n", "I N T E R".
SPACED_LETTERS = re.compile(r"(?<!\S)(?:[^\W\d_] ){2,}[^\W\d_](?!\S)")
SPACES = re.compile(r"[ \t ]+")
SENTENCE_END = (".", ":", ";", "!", "?")
# A line ending like this is not finished, so the next line continues it even if capitalised.
UNFINISHED = re.compile(
    r"(?:[,&/+-]|\b(?:and|or|with|using|in|of|for|to|the|a|an|on|at|by|from|including|via|"
    r"such as|like))$",
    re.IGNORECASE,
)


def _fix_line(line: str) -> str:
    for broken, fixed in MOJIBAKE.items():
        line = line.replace(broken, fixed)
    line = INVISIBLE.sub("", line)
    line = unicodedata.normalize("NFKC", line)
    line = BULLET.sub("", line)
    # Joined before spaces are collapsed, so a wider gap between spaced words stays a word break.
    line = SPACED_LETTERS.sub(lambda m: m.group().replace(" ", ""), line)
    return SPACES.sub(" ", line).strip()


def clean_text(raw: str) -> str:
    """Fix encoding, drop bullets, empty and repeated lines, and join broken lines.

    A line is joined to the one before when the one before does not end a sentence, is not a
    section heading, and either this line starts with a lower-case letter or the one before ends
    with a comma or a joining word such as "with" (a sentence wrapped by the PDF layout).
    Repeated lines, such as page headers and footers, are kept once; headings are kept.
    """
    lines: list[str] = []
    seen: set[str] = set()
    for raw_line in raw.splitlines():
        line = _fix_line(raw_line)
        if not line:
            continue
        is_heading = heading_type(line) is not None
        key = line.lower()
        if key in seen and not is_heading:
            continue
        seen.add(key)
        previous = lines[-1] if lines else ""
        continues = line[0].islower() or UNFINISHED.search(previous)
        if (previous and continues and not is_heading and not previous.endswith(SENTENCE_END)
                and heading_type(previous) is None):
            lines[-1] = f"{previous} {line}"
        else:
            lines.append(line)
    return "\n".join(lines)
