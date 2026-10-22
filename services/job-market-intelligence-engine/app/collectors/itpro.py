"""itpro.lk: an IT job board, read through the RSS feeds it publishes for automated reading.

Listing pages: one RSS feed per category (``/rss/<code>/``), each with its newest jobs. Every item
holds the full ad: title ("<role> at <company>"), link (``/job/<id>/...``), publication date,
company (``dc:creator``) and the ad body (``content:encoded``: Company, Location, Job Type,
Description and usually a requirements list). So no job page is downloaded: the feed item itself
is stored in raw/ as the ad.

Homepage (live list): ``/sitemap.xml`` lists every live job page, so a sync uses it to confirm
that a job missing from the feeds has been taken down. Ads have no closing date.

robots.txt allows these URLs and asks for 10 seconds between requests (PoliteClient keeps it).
Saved copies of a real feed and sitemap are in tests/fixtures/itpro/.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from app.collectors.base import BaseCollector, CollectResult
from app.collectors.models import Category, JobAd, ListingEntry
from app.collectors.text_utils import html_to_text

FEED_PATH = "/rss/{code}/"
SITEMAP_PATH = "/sitemap.xml"
NS = {"content": "http://purl.org/rss/1.0/modules/content/", "dc": "http://purl.org/dc/elements/1.1/"}
JOB_ID = re.compile(r"/job/(\d+)/")
# The labelled lines at the top of each ad body.
FIELD = re.compile(r"^(Company|Location|Job Type):\s*(.*)$", re.IGNORECASE)

for _prefix, _uri in NS.items():
    ET.register_namespace(_prefix, _uri)


class ItproCollector(BaseCollector):
    site = "itpro"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._items: dict[str, str] = {}  # job_id → the feed item (XML), from this run's feeds

    def listing_url(self, category: Category) -> str:
        return self.config.base_url + FEED_PATH.format(code=category.code)

    def parse_listing(self, html: str, sector: str, category: Category) -> list[ListingEntry]:
        entries = []
        for item in _parse(html).iter("item"):
            link = (item.findtext("link") or "").strip()
            job_id = JOB_ID.search(link)
            if not job_id:
                continue
            company = (item.findtext("dc:creator", namespaces=NS) or "").strip() or None
            fields = _fields(item)
            self._items[job_id.group(1)] = ET.tostring(item, encoding="unicode")
            entries.append(
                ListingEntry(
                    site=self.site,
                    job_id=job_id.group(1),
                    url=link,
                    sector=sector,
                    category=category.key,
                    job_title=_role(item.findtext("title"), company),
                    company=company,
                    posted_date=_date(item.findtext("pubDate")),
                    location=fields.get("location"),
                )
            )
        return entries

    def parse_ad(self, html: str, entry: ListingEntry) -> JobAd:
        item = _parse(html)
        company = (item.findtext("dc:creator", namespaces=NS) or "").strip() or entry.company
        fields = _fields(item)
        return JobAd(
            site=self.site,
            job_id=entry.job_id,
            url=entry.url,
            sectors=[entry.sector],
            categories=[entry.category],
            job_title=_role(item.findtext("title"), company) or entry.job_title,
            company=company,
            location=fields.get("location") or entry.location,
            posted_date=_date(item.findtext("pubDate")) or entry.posted_date,
            employment_type=fields.get("job type"),
            description_text=_body(item) or None,
        )

    def _download(self, entry: ListingEntry, result: CollectResult) -> bool:
        """The feed item is the ad: store it, no request needed."""
        item = self._items.get(entry.job_id)
        if item is None:
            result.skipped.append(f"{entry.url} (not in this run's feeds)")
            return False
        self.storage.save_raw(entry, item, self.now())
        return True

    def homepage_url(self) -> str:
        return self.config.base_url + SITEMAP_PATH

    def parse_live_ids(self, html: str) -> set[str]:
        """Job IDs of every job page in the sitemap."""
        return set(JOB_ID.findall(" ".join(loc.text or "" for loc in _parse(html).iter() if loc.tag.endswith("loc"))))


def _parse(text: str) -> ET.Element:
    """Parse a feed, an item or the sitemap. Documents with a DOCTYPE (where entity tricks live)
    are refused; itpro's feeds have none."""
    if "<!DOCTYPE" in text[:2000].upper():
        raise ValueError("unexpected DOCTYPE in itpro XML")
    return ET.fromstring(text.encode("utf-8"))


def _body_lines(item: ET.Element) -> list[str]:
    content = item.findtext("content:encoded", namespaces=NS) or item.findtext("description") or ""
    return html_to_text(content).splitlines()


def _split(item: ET.Element) -> tuple[dict[str, str], list[str]]:
    """The labelled fields at the top (company, location, job type) and the rest of the ad text.
    A label and its value may share a line ("Location: Colombo") or not ("Company:" / "Hatchyard")."""
    lines = [line.strip() for line in _body_lines(item) if line.strip()]
    fields: dict[str, str] = {}
    rest: list[str] = []
    i = 0
    while i < len(lines):
        match = FIELD.match(lines[i])
        if match:
            value = match.group(2).strip()
            if not value and i + 1 < len(lines) and not FIELD.match(lines[i + 1]):
                value, i = lines[i + 1], i + 1
            fields.setdefault(match.group(1).lower(), value)
        elif not (lines[i].rstrip(":").lower() == "description" and not rest):
            rest.append(lines[i])
        i += 1
    return fields, rest


def _fields(item: ET.Element) -> dict[str, str]:
    return {k: v for k, v in _split(item)[0].items() if v}


def _body(item: ET.Element) -> str:
    """The ad text without the labelled fields at the top (they are stored as their own fields)."""
    return "\n".join(_split(item)[1])


def _role(title: str | None, company: str | None) -> str | None:
    """"Senior Software Engineer - Java at Hatchyard" → "Senior Software Engineer - Java"."""
    title = " ".join((title or "").split())
    if company and title.lower().endswith(f" at {company}".lower()):
        title = title[: -len(f" at {company}")]
    return title or None


def _date(value: str | None) -> str | None:
    """RSS date (e.g. "Thu, 22 Oct 2026 00:43:12 +0530") → the ISO date as published."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value.strip()).date().isoformat()
    except (TypeError, ValueError):
        return None
