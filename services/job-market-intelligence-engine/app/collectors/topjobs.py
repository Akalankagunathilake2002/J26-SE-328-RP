"""topjobs.lk: category listing pages → ad pages → flyer images.

Listing pages: each ad is a table row whose ``onclick`` calls
``createAlert('<rid>', '<agent code>', '<job code>', '<employer code>', …)``; topjobs builds the ad
URL from those codes. The row also holds the title (``h2``), company (``h1``), opening and closing
dates and location in their own cells. (The page repeats the dates inside HTML comments, which
are ignored.)

Ad pages: ``#position``, ``#employer``, ``#adview-job-location``, ``#endDate``, the job-type
labels in ``.ad-status``, and ``#remark``, the ad body, usually a single flyer image.

If topjobs changes its layout, the listing returns no ads and the run reports it, rather than
collecting the wrong pages. Saved copies of real pages are in tests/fixtures/topjobs/.
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
AD_PATH = (  # sic: "Advertisment" is topjobs' own spelling
    "/employer/JobAdvertismentServlet?rid={rid}&ac={agent}&jc={job}&ec={employer}"
    "&pg=applicant/vacancybyfunctionalarea.jsp"
)
CREATE_ALERT = re.compile(r"createAlert\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'")
WITHHELD = re.compile(r"withheld|confidential", re.IGNORECASE)
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
        for row in soup.find_all("tr", onclick=CREATE_ALERT):
            rid, agent, job, employer = CREATE_ALERT.search(row["onclick"]).groups()
            if not job or job in entries:
                continue
            # Only the row's own cells: the comments between them repeat the dates.
            cells = [_text(cell) or "" for cell in row.find_all("td", recursive=False)]
            date_cells = [i for i, cell in enumerate(cells) if find_dates(cell)]
            after_dates = date_cells[-1] + 1 if date_cells else None
            company = _text(row.find("h1"))
            entries[job] = ListingEntry(
                site=self.site,
                job_id=job,
                url=self.config.base_url
                + AD_PATH.format(rid=rid, agent=agent, job=job, employer=employer),
                sector=sector,
                category=category.key,
                job_title=_text(row.find("h2")),
                company=None if not company or WITHHELD.search(company) else company,
                posted_date=find_dates(cells[date_cells[0]])[0] if date_cells else None,
                closing_date=find_dates(cells[date_cells[1]])[0] if len(date_cells) > 1 else None,
                location=(cells[after_dates] or None)
                if after_dates is not None and after_dates < len(cells)
                else None,
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
            location=_text(soup.find(id="adview-job-location")) or entry.location,
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
    """The ad's job-type labels, e.g. "Full Time; Permanent; Onsite"."""
    labels = [_text(label) for label in soup.select(".ad-status label")]
    return "; ".join(label for label in labels if label) or None


def _text(element) -> str | None:
    if element is None:
        return None
    return " ".join(element.get_text(" ").split()) or None
