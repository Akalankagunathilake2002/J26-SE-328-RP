"""Sync: ad statuses (active / expired / removed) over several days, with a made-up site. No network."""

import json
from pathlib import Path

import pytest

from app.collectors.base import BaseCollector, local_date, next_status
from app.collectors.config import Settings
from app.collectors.http import FetchFailed
from app.collectors.models import ACTIVE, EXPIRED, REMOVED, Category, JobAd, ListingEntry, SiteConfig
import app.collectors.run as run
from app.collectors.run import main
from app.collectors.storage import Storage
from app.collectors.topjobs import TopjobsCollector

BASE = "https://jobs.example"
CONFIG = SiteConfig(
    name="example", enabled=True, base_url=BASE, categories={"IT": (Category(name="Software", code="SW"),)}
)


class FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text, self.status_code, self.content, self.headers, self.url = text, status_code, b"", {}, ""


class FakeClient:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url):
        page = self.pages.get(url)
        if isinstance(page, Exception):
            raise page
        return page or FakeResponse(status_code=404)


class ExampleSite(BaseCollector):
    """Listing lines are "job_id|closing_date"; the homepage is a comma-separated list of job IDs.
    IDs starting with "A" are agency ads, which the homepage doesn't list (as on topjobs)."""

    site = "example"

    def listing_url(self, category):
        return f"{BASE}/list/{category.code}"

    def parse_listing(self, html, sector, category):
        rows = [line.split("|") for line in html.splitlines() if line]
        return [
            ListingEntry(self.site, job_id, f"{BASE}/ad/{job_id}", sector, category.key, f"Job {job_id}",
                         closing_date=closing)
            for job_id, closing in rows
        ]

    def parse_ad(self, html, entry):
        return JobAd(site=self.site, job_id=entry.job_id, url=entry.url, job_title=html,
                     closing_date=entry.closing_date)

    def homepage_url(self):
        return f"{BASE}/home"

    def parse_live_ids(self, html):
        return {job_id for job_id in html.split(",") if job_id}

    def listed_on_homepage(self, url):
        return not url.rsplit("/", 1)[-1].startswith("A")


def sync_day(storage, now, listing, homepage):
    """One sync. ``homepage`` is a list of live IDs, or an exception / status code if it fails."""
    pages = {f"{BASE}/list/SW": FakeResponse("\n".join(listing))}
    pages |= {f"{BASE}/ad/{line.split('|')[0]}": FakeResponse("Software Engineer") for line in listing}
    if isinstance(homepage, list):
        pages[f"{BASE}/home"] = FakeResponse(",".join(homepage))
    elif isinstance(homepage, Exception):
        pages[f"{BASE}/home"] = homepage
    collector = ExampleSite(CONFIG, FakeClient(pages), storage, now=lambda: now)
    return collector.sync(["IT"])


def statuses(storage):
    return {raw.job_id: raw.meta["status"] for raw in storage.iter_raw("example")}


@pytest.fixture
def storage(tmp_path):
    """Day 1: three ads collected. Ad 3 closes on 20 October."""
    storage = Storage(tmp_path)
    sync_day(storage, "2026-10-17T04:00:00+00:00", ["1|2026-10-30", "2|2026-10-30", "3|2026-10-20"], ["1", "2", "3"])
    return storage


# --- the rules --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("current", "closing", "seen", "homepage_checked", "expected"),
    [
        (ACTIVE, "2026-10-30", True, True, ACTIVE),
        (ACTIVE, "2026-10-17", True, True, EXPIRED),  # closing date passed, even if still listed
        (ACTIVE, "2026-10-18", False, False, ACTIVE),  # closes today: still active
        (ACTIVE, "2026-10-30", False, True, REMOVED),  # gone from the listing pages and the homepage
        (ACTIVE, "2026-10-30", False, False, ACTIVE),  # homepage not read: no proof it is gone
        (ACTIVE, None, False, True, REMOVED),
        (REMOVED, "2026-10-30", True, True, ACTIVE),  # back on the site
        (REMOVED, "2026-10-17", False, True, REMOVED),  # taken down early stays removed
        (EXPIRED, "2026-10-17", True, True, EXPIRED),
        (EXPIRED, "2026-11-05", True, True, ACTIVE),  # closing date extended on the site
    ],
)
def test_next_status(current, closing, seen, homepage_checked, expected):
    assert next_status(current, closing, "2026-10-18", seen=seen, homepage_checked=homepage_checked) == expected


def test_closing_dates_are_sri_lankan_dates():
    assert local_date("2026-10-17T18:00:00+00:00") == "2026-10-17"  # 23:30 in Colombo
    assert local_date("2026-10-17T19:00:00+00:00") == "2026-10-18"  # 00:30 in Colombo


# --- syncs over several days ------------------------------------------------------------------------


def test_new_ads_start_active(storage):
    assert statuses(storage) == {"1": ACTIVE, "2": ACTIVE, "3": ACTIVE}
    meta = next(storage.iter_raw("example")).meta
    assert meta["status_history"] == [{"status": ACTIVE, "at": "2026-10-17T04:00:00+00:00"}]


def test_ad_missing_from_its_category_page_but_on_the_homepage_stays_active(storage):
    _, result = sync_day(storage, "2026-10-19T04:00:00+00:00", ["1|2026-10-30"], ["1", "2", "3"])
    assert statuses(storage) == {"1": ACTIVE, "2": ACTIVE, "3": ACTIVE}
    assert (result.live_on_homepage, result.active, result.removed) == (3, 3, [])


def test_expired_and_removed(storage):
    _, result = sync_day(storage, "2026-10-21T04:00:00+00:00", ["1|2026-10-30"], ["1"])

    assert statuses(storage) == {"1": ACTIVE, "2": REMOVED, "3": EXPIRED}
    assert (result.expired, result.removed, result.active) == (["3"], ["2"], 1)
    meta = {raw.job_id: raw.meta for raw in storage.iter_raw("example")}
    assert meta["2"]["status_changed_at"] == "2026-10-21T04:00:00+00:00"
    assert meta["2"]["last_seen_at"] == "2026-10-17T04:00:00+00:00"  # the last day it was live
    assert meta["1"]["last_seen_at"] == "2026-10-21T04:00:00+00:00"
    assert [h["status"] for h in meta["2"]["status_history"]] == [ACTIVE, REMOVED]


def test_removed_ad_that_comes_back_is_active_again(storage):
    sync_day(storage, "2026-10-19T04:00:00+00:00", ["1|2026-10-30"], ["1", "3"])
    assert statuses(storage)["2"] == REMOVED

    _, result = sync_day(storage, "2026-10-20T04:00:00+00:00", ["1|2026-10-30", "2|2026-10-30"], ["1", "2"])
    assert statuses(storage)["2"] == ACTIVE and result.reactivated == ["2"]


@pytest.mark.parametrize("homepage", [FetchFailed("timeout"), None, ["999", "998"]])
def test_without_a_trustworthy_homepage_nothing_is_removed(storage, homepage):
    """Homepage unreachable, missing (404), or listing none of the category page's ads."""
    _, result = sync_day(storage, "2026-10-19T04:00:00+00:00", ["1|2026-10-30"], homepage)
    assert statuses(storage) == {"1": ACTIVE, "2": ACTIVE, "3": ACTIVE}
    assert result.live_on_homepage is None


def test_agency_ads_are_never_marked_removed_only_expired(tmp_path):
    storage = Storage(tmp_path)
    sync_day(storage, "2026-10-17T04:00:00+00:00", ["1|2026-10-30", "A9|2026-10-25"], ["1"])
    assert statuses(storage) == {"1": ACTIVE, "A9": ACTIVE}  # the homepage was trusted without A9

    _, result = sync_day(storage, "2026-10-19T04:00:00+00:00", ["1|2026-10-30"], ["1"])
    assert statuses(storage)["A9"] == ACTIVE and result.unconfirmed == 1

    sync_day(storage, "2026-10-26T04:00:00+00:00", ["1|2026-10-30"], ["1"])
    assert statuses(storage)["A9"] == EXPIRED


def test_new_ads_are_still_downloaded_during_a_sync(storage):
    collected, _ = sync_day(storage, "2026-10-19T04:00:00+00:00", ["1|2026-10-30", "4|2026-11-02"], ["1", "2", "3", "4"])
    assert collected.new_ads == {"IT": 1} and statuses(storage)["4"] == ACTIVE


def test_extended_closing_date_is_kept(storage):
    sync_day(storage, "2026-10-19T04:00:00+00:00", ["3|2026-11-15"], ["1", "2", "3"])
    meta = {raw.job_id: raw.meta for raw in storage.iter_raw("example")}
    assert meta["3"]["listing"]["closing_date"] == "2026-11-15"

    sync_day(storage, "2026-10-21T04:00:00+00:00", ["3|2026-11-15"], ["1", "2", "3"])
    assert statuses(storage)["3"] == ACTIVE  # 20 October was the old closing date


def test_reparse_reports_ads_expired_since_the_last_sync(storage):
    collector = ExampleSite(CONFIG, FakeClient({}), storage, now=lambda: "2026-10-22T04:00:00+00:00")
    ads = {ad.job_id: ad for ad in collector.reparse()}
    assert (ads["1"].status, ads["3"].status) == (ACTIVE, EXPIRED)
    assert ads["1"].last_seen_at == "2026-10-17T04:00:00+00:00"


# --- topjobs and the command line -------------------------------------------------------------------


def test_topjobs_homepage():
    """A trimmed copy of the real homepage: links to direct ads, and one featured agency ad."""
    collector = TopjobsCollector(
        SiteConfig(name="topjobs", enabled=True, base_url="https://www.topjobs.lk", categories={}),
        client=None, storage=None,
    )
    page = (Path(__file__).parent / "fixtures" / "topjobs" / "homepage.html").read_text()
    assert collector.homepage_url() == "https://www.topjobs.lk/"
    assert collector.parse_live_ids(page) == {"0001556070", "0001561026", "0001560048", "0001560506"}

    ad = "https://www.topjobs.lk/employer/JobAdvertismentServlet?rid=0&ac={}&jc=0001560048&ec=DEFZZZ"
    assert collector.listed_on_homepage(ad.format("DEFZZZ"))  # posted by the employer
    assert not collector.listed_on_homepage(ad.format("0000000094"))  # posted through an agency


def test_sync_and_reparse_cannot_be_combined(tmp_path):
    with pytest.raises(SystemExit):
        main(["--sync", "--reparse"], settings=Settings(tmp_path, None))


def test_every_sync_is_logged(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    monkeypatch.setitem(run.COLLECTORS, "example", ExampleSite)
    pages = {f"{BASE}/list/SW": FakeResponse("1|2026-10-30"), f"{BASE}/ad/1": FakeResponse("Job"),
             f"{BASE}/home": FakeResponse("1")}
    monkeypatch.setattr(run, "PoliteClient", lambda *args, **kwargs: FakeClient(pages))

    code = main(["--site", "example", "--sector", "IT", "--sync", "--no-ocr"],
                settings=Settings(tmp_path, None), sites={"example": CONFIG})

    assert code == 0
    [row] = storage.read_sync_log()
    assert (row["site"], row["live_on_homepage"], row["new_ads"], row["active"], row["removed"]) == (
        "example", "1", "1", "1", "0"
    )
    [record] = [json.loads(line) for line in (tmp_path / "processed" / "example.jsonl").read_text().splitlines()]
    assert record["status"] == ACTIVE and record["last_seen_at"]
