"""topjobs.lk: category listing pages → ad pages → flyer images.

Ad pages: the fields come from the feasibility check (``#position``, ``#employer``,
``#adview-job-location``, ``#endDate`` and ``#remark``, the ad body, usually one flyer image).

Listing pages: every link to an ad page (``JobAdvertismentServlet``) is an ad; its job code is
the ``jc`` query parameter and the dates (opening, then closing) are read from the same table row.
Check this against a saved listing page before large runs. If topjobs changes its layout, the
listing returns no ads and the run reports it, rather than collecting the wrong pages.
"""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from app.collectors.base import BaseCollector
from app.collectors.models import Category, JobAd, ListingEntry
from app.collectors.text_utils import html_to_text

LISTING_PATH = "/applicant/vacancybyfunctionalarea.jsp?FA={code}"
AD_LINK = re.compile(r"JobAdvertismentServlet", re.IGNORECASE)  # sic: topjobs' own spelling
WITHHELD = re.compile(r"withheld|confidential", re.IGNORECASE)
EMPLOYMENT_TYPES = (
    "Full Time", "Part Time", "Contract", "Permanent", "Temporary", "Internship",
    "Onsite", "On-site", "Remote", "Hybrid",
)
MIN_TEXT_AD_CHARS = 200  # an ad body with less text than this beside a flyer is an image ad

MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
DATE_PATTERNS = [
    (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), "%Y-%m-%d"),
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"), "%d/%m/%Y"),
    (re.compile(rf"\b((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*,?\s+(?:{MONTHS})\w*\s+\d{{1,2}},?\s+\d{{4}})"), None),
    (re.compile(rf"\b(\d{{1,2}}[\s-](?:{MONTHS})\w*[\s-]\d{{4}})"), None),
    (re.compile(rf"\b((?:{MONTHS})\w*\s+\d{{1,2}},?\s+\d{{4}})"), None),
]
FLEXIBLE_FORMATS = ["%a %b %d %Y", "%A %B %d %Y", "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y"]


class TopjobsCollector(BaseCollector):
    site = "topjobs"

    def listing_url(self, category: Category) -> str:
        return self.config.base_url + LISTING_PATH.format(code=category.code)

    def parse_listing(self, html: str, sector: str, category: Category) -> list[ListingEntry]:
        soup = BeautifulSoup(html, "html.parser")
        entries: dict[str, ListingEntry] = {}
        for link in soup.find_all("a", href=AD_LINK):
            url = urljoin(self.config.base_url + "/", link["href"])
            job_id = job_code(url)
            if not job_id or job_id in entries:
                continue
            row = link.find_parent("tr")
            dates = find_dates(row.get_text(" ") if row else "")
            entries[job_id] = ListingEntry(
                site=self.site,
                job_id=job_id,
                url=url,
                sector=sector,
                category=category.key,
                job_title=_text(link),
                posted_date=dates[0] if dates else None,
                closing_date=dates[1] if len(dates) > 1 else None,
            )
        return list(entries.values())

    def parse_ad(self, html: str, entry: ListingEntry) -> JobAd:
        soup = BeautifulSoup(html, "html.parser")
        employer = _text(soup.find(id="employer"))
        closing_dates = find_dates(_text(soup.find(id="endDate")) or "")
        body = soup.find(id="remark")

        image = body.find("img", src=True) if isinstance(body, Tag) else None
        image_url = urljoin(entry.url, image["src"]) if image else None
        body_text = html_to_text(str(body)) if body else ""
        is_image_ad = image_url is not None and len(body_text) < MIN_TEXT_AD_CHARS

        return JobAd(
            site=self.site,
            job_id=entry.job_id,
            url=entry.url,
            sectors=[entry.sector],
            categories=[entry.category],
            job_title=_text(soup.find(id="position")) or entry.job_title,
            company=None if not employer or WITHHELD.search(employer) else employer,
            location=_text(soup.find(id="adview-job-location")),
            posted_date=entry.posted_date,
            closing_date=closing_dates[0] if closing_dates else entry.closing_date,
            employment_type=_employment_type(soup),
            description_text=None if is_image_ad else (body_text or None),
            is_image_ad=is_image_ad,
            image_url=image_url,
        )


def job_code(url: str) -> str | None:
    """topjobs' job code (``jc`` query parameter), or the last path segment if there is none."""
    parts = urlsplit(url)
    code = parse_qs(parts.query).get("jc", [None])[0]
    return code or (parts.path.rstrip("/").rsplit("/", 1)[-1] or None)


def find_dates(text: str) -> list[str]:
    """Dates in the order they appear, as ISO strings (yyyy-mm-dd)."""
    found: list[tuple[int, int, str]] = []  # (start, end, iso)
    for pattern, fmt in DATE_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span(1)
            if any(start < other_end and other_start < end for other_start, other_end, _ in found):
                continue  # this text was already read as a date by an earlier pattern
            iso = _to_iso(match.group(1), fmt)
            if iso:
                found.append((start, end, iso))
    return [iso for _, _, iso in sorted(found)]


def _to_iso(raw: str, fmt: str | None) -> str | None:
    """Parse with ``fmt``, or, for written-out dates, with each of the flexible formats."""
    if fmt:
        formats, value = [fmt], raw
    else:
        formats, value = FLEXIBLE_FORMATS, " ".join(raw.replace(",", " ").replace("-", " ").split())
    for candidate in formats:
        try:
            return datetime.strptime(value, candidate).date().isoformat()
        except ValueError:
            continue
    return None


def _employment_type(soup: BeautifulSoup) -> str | None:
    """Labels such as "Full Time; Permanent; Onsite" shown in the ad's header area."""
    position = soup.find(id="position")
    header = position.find_parent(["div", "table", "section"]) if position else None
    text = header.get_text(" ") if header else ""
    found = [label for label in EMPLOYMENT_TYPES if re.search(rf"\b{re.escape(label)}\b", text, re.I)]
    return "; ".join(found) or None


def _text(element) -> str | None:
    if element is None:
        return None
    return " ".join(element.get_text(" ").split()) or None
