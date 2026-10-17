"""Removing duplicate ads.

1. Same source URL: an ad listed under two categories or sectors is kept once, with all of its
   sectors and categories.
2. Similar content, across sites and re-posts: normalised title + company + description
   similarity above the threshold (rapidfuzz ratio). Image ads have no text to compare, so they
   also need the same closing date.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from rapidfuzz import fuzz

from app.collectors.models import JobAd

DEFAULT_THRESHOLD = 90.0
DESCRIPTION_CHARS = 2000  # enough to tell ads apart, and keeps comparisons fast


@dataclass(frozen=True)
class DedupRecord:
    kept: str  # "site:job_id"
    removed: str
    reason: str  # "same_url" | "similar_text" | "similar_image_ad"
    score: float

    def as_row(self) -> dict:
        return {
            "kept": self.kept,
            "removed": self.removed,
            "reason": self.reason,
            "score": round(self.score, 1),
        }


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = urlencode(sorted(parse_qsl(parts.query)))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def normalize(text: str | None) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", (text or "").lower()).split())


def deduplicate(
    ads: list[JobAd], threshold: float = DEFAULT_THRESHOLD
) -> tuple[list[JobAd], list[DedupRecord]]:
    """Unique ads (first occurrence kept, with sectors merged) and a record of each removal."""
    log: list[DedupRecord] = []

    by_url: dict[str, JobAd] = {}
    for ad in ads:
        key = normalize_url(ad.url)
        if key in by_url:
            _merge(by_url[key], ad)
            log.append(DedupRecord(by_url[key].key, ad.key, "same_url", 100.0))
        else:
            by_url[key] = ad

    unique: list[JobAd] = []
    for ad in by_url.values():
        for kept in unique:
            score = similarity(kept, ad, threshold)
            if score is not None:
                _merge(kept, ad)
                reason = "similar_text" if _has_text(kept) and _has_text(ad) else "similar_image_ad"
                log.append(DedupRecord(kept.key, ad.key, reason, score))
                break
        else:
            unique.append(ad)
    return unique, log


def similarity(a: JobAd, b: JobAd, threshold: float = DEFAULT_THRESHOLD) -> float | None:
    """The similarity score if ``a`` and ``b`` look like the same job, otherwise None."""
    if a.company and b.company and fuzz.ratio(normalize(a.company), normalize(b.company)) <= threshold:
        return None
    with_text = _has_text(a) and _has_text(b)
    if not with_text and (not a.closing_date or a.closing_date != b.closing_date):
        return None
    score = fuzz.ratio(_signature(a, with_text), _signature(b, with_text))
    return score if score > threshold else None


def _has_text(ad: JobAd) -> bool:
    return bool(ad.description_text and ad.description_text.strip())


def _signature(ad: JobAd, with_text: bool) -> str:
    parts = [normalize(ad.job_title), normalize(ad.company)]
    if with_text:
        parts.append(normalize(ad.description_text)[:DESCRIPTION_CHARS])
    return " | ".join(parts)


def _merge(kept: JobAd, duplicate: JobAd) -> None:
    kept.sectors = sorted(set(kept.sectors) | set(duplicate.sectors))
    kept.categories = sorted(set(kept.categories) | set(duplicate.categories))
