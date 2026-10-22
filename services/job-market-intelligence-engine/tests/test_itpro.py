"""itpro.lk, read through its RSS feeds; tested on a real feed and sitemap saved in
tests/fixtures/itpro/ (3 jobs). No network."""

import re
from pathlib import Path

import pytest

from app.collectors.itpro import ItproCollector, _date, _parse, _role
from app.collectors.models import ACTIVE, REMOVED, Category, SiteConfig
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad

FIXTURES = Path(__file__).parent / "fixtures" / "itpro"
FEED = (FIXTURES / "feed.xml").read_text()
SITEMAP = (FIXTURES / "sitemap.xml").read_text()
BASE = "https://itpro.lk"
SOFTWARE = Category(name="Software Engineering", code="software-engineering")
CONFIG = SiteConfig(name="itpro", enabled=True, base_url=BASE, categories={"IT": (SOFTWARE,)})


class FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text, self.status_code, self.content, self.headers, self.url = text, status_code, b"", {}, ""


class FakeClient:
    def __init__(self, pages):
        self.pages, self.requested = pages, []

    def get(self, url):
        self.requested.append(url)
        return self.pages.get(url) or FakeResponse(status_code=404)


def collector(tmp_path, pages=None, now="2026-10-22T08:00:00+00:00"):
    client = FakeClient(pages or {})
    return ItproCollector(CONFIG, client, Storage(tmp_path), now=lambda: now), client


def without_job(feed, job_id):
    return re.sub(rf"<item>(?:(?!</item>).)*?/job/{job_id}/.*?</item>", "", feed, flags=re.S)


def test_feed_items_become_listing_entries(tmp_path):
    c, _ = collector(tmp_path)
    entries = c.parse_listing(FEED, "IT", SOFTWARE)

    assert [e.job_id for e in entries] == ["15536", "15528", "15526"]
    first = entries[0]
    assert first.url == "https://itpro.lk/job/15536/senior-software-engineer-java-at-hatchyard/"
    assert (first.job_title, first.company) == ("Senior Software Engineer - Java", "Hatchyard")  # " at Hatchyard" removed
    assert (first.posted_date, first.sector, first.category) == ("2026-10-22", "IT", "software-engineering")


def test_ad_fields_come_from_the_feed_item(tmp_path):
    c, _ = collector(tmp_path)
    entries = c.parse_listing(FEED, "IT", SOFTWARE)
    ads = {e.job_id: c.parse_ad(c._items[e.job_id], e) for e in entries}

    java = ads["15536"]
    assert (java.location, java.employment_type, java.is_image_ad) == ("Colombo", "Full-time", False)
    assert not java.description_text.startswith(("Company", "Hatchyard"))  # the labelled fields are separate
    assert "Java" in clean_ad(java).requirements_text  # from its "Key Requirements" section
    assert ads["15528"].employment_type == "Internship"
    assert ads["15526"].employment_type == "Contract"


def test_collect_stores_the_feed_items_without_downloading_job_pages(tmp_path):
    feed_url = f"{BASE}/rss/software-engineering/"
    c, client = collector(tmp_path, {feed_url: FakeResponse(FEED)})

    result = c.collect(["IT", "HR"])

    # HR is skipped quietly: itpro.lk has no HR category, so there is no listing to check
    assert result.new_ads == {"IT": 3} and result.listed == {"IT": 3} and client.requested == [feed_url]
    ads = {ad.job_id: ad for ad in c.reparse()}
    assert ads["15536"].company == "Hatchyard" and ads["15536"].description_text


def test_sitemap_lists_the_live_jobs(tmp_path):
    c, _ = collector(tmp_path)
    assert c.homepage_url() == "https://itpro.lk/sitemap.xml"
    assert c.parse_live_ids(SITEMAP) == {"15390", "15528", "15536", "15537"}


def test_a_job_gone_from_the_feeds_and_the_sitemap_is_removed(tmp_path):
    feed_url, sitemap_url = f"{BASE}/rss/software-engineering/", f"{BASE}/sitemap.xml"
    c, _ = collector(tmp_path, {feed_url: FakeResponse(FEED), sitemap_url: FakeResponse(SITEMAP)})
    c.sync(["IT"])
    statuses = {raw.job_id: raw.meta["status"] for raw in c.storage.iter_raw("itpro")}
    assert statuses == {"15536": ACTIVE, "15528": ACTIVE, "15526": ACTIVE}  # 15526 is still in the feed

    later, _ = collector(tmp_path, {feed_url: FakeResponse(without_job(FEED, "15526")), sitemap_url: FakeResponse(SITEMAP)},
                         now="2026-10-23T08:00:00+00:00")
    _, result = later.sync(["IT"])

    statuses = {raw.job_id: raw.meta["status"] for raw in later.storage.iter_raw("itpro")}
    assert statuses["15526"] == REMOVED and result.removed == ["15526"]
    assert statuses["15536"] == ACTIVE


def test_helpers():
    assert _role("Tech Lead - DevOps at Hatchyard", "Hatchyard") == "Tech Lead - DevOps"
    assert _role("Data Engineer", None) == "Data Engineer"
    assert _date("Thu, 22 Oct 2026 00:43:12 +0530") == "2026-10-22"
    assert _date("not a date") is None
    with pytest.raises(ValueError):
        _parse('<!DOCTYPE rss [<!ENTITY x "y">]><rss/>')
