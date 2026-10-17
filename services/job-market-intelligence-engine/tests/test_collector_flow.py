"""The shared collect flow (BaseCollector) and raw storage, with a made-up site. No network."""

from dataclasses import dataclass, field

import pytest

from app.collectors.base import BaseCollector, image_extension
from app.collectors.http import RobotsDisallowed, SiteBlocked
from app.collectors.models import Category, JobAd, ListingEntry, SiteConfig
from app.collectors.storage import Storage

BASE = "https://jobs.example"

CONFIG = SiteConfig(
    name="example",
    enabled=True,
    base_url=BASE,
    categories={
        "IT": (Category(name="Software", code="SW"),),
        "Management": (Category(name="Management", code="MG"),),
    },
)


@dataclass
class FakeResponse:
    status_code: int = 200
    text: str = ""
    content: bytes = b""
    headers: dict = field(default_factory=dict)
    url: str = ""


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.requested = []

    def get(self, url):
        self.requested.append(url)
        page = self.pages.get(url)
        if isinstance(page, Exception):
            raise page
        return page or FakeResponse(status_code=404)


class ExampleCollector(BaseCollector):
    """Listing pages hold lines "job_id|title|posted_date"; ad pages hold "title|image_url"."""

    site = "example"

    def listing_url(self, category):
        return f"{BASE}/list/{category.code}"

    def parse_listing(self, html, sector, category):
        entries = []
        for line in html.splitlines():
            job_id, title, posted = line.split("|")
            entries.append(
                ListingEntry(
                    self.site, job_id, f"{BASE}/ad/{job_id}", sector, category.key, title,
                    posted_date=posted,
                )
            )
        return entries

    def parse_ad(self, html, entry):
        title, image_url = html.split("|")
        return JobAd(
            site=self.site, job_id=entry.job_id, url=entry.url, job_title=title,
            is_image_ad=bool(image_url), image_url=image_url or None,
        )


def make_collector(tmp_path, pages):
    client = FakeClient(pages)
    collector = ExampleCollector(
        CONFIG, client, Storage(tmp_path), now=lambda: "2026-10-17T10:00:00+00:00"
    )
    return collector, client


def test_collects_newest_ads_up_to_the_limit_and_stores_them_raw(tmp_path):
    pages = {
        f"{BASE}/list/SW": FakeResponse(text="1|Old job|2026-10-01\n2|New job|2026-10-15\n3|Mid job|2026-10-10"),
        f"{BASE}/ad/2": FakeResponse(text="New job|"),
        f"{BASE}/ad/3": FakeResponse(text="Mid job|"),
    }
    collector, client = make_collector(tmp_path, pages)

    result = collector.collect(["IT"], limit=2)

    assert result.new_ads == {"IT": 2}
    assert f"{BASE}/ad/1" not in client.requested  # the oldest was beyond the limit
    stored = collector.storage.find_raw("example", "2")
    assert stored == tmp_path / "raw" / "example" / "IT" / "2.html"
    assert stored.read_text() == "New job|"


def test_ad_listed_in_two_sectors_is_downloaded_once(tmp_path):
    pages = {
        f"{BASE}/list/SW": FakeResponse(text="1|Analyst|2026-10-15"),
        f"{BASE}/list/MG": FakeResponse(text="1|Analyst|2026-10-15"),
        f"{BASE}/ad/1": FakeResponse(text="Analyst|"),
    }
    collector, client = make_collector(tmp_path, pages)

    result = collector.collect(["IT", "Management"])

    assert client.requested.count(f"{BASE}/ad/1") == 1
    assert result.already_stored == 1
    [ad] = collector.reparse()
    assert ad.sectors == ["IT", "Management"] and ad.categories == ["SW", "MG"]


def test_second_run_downloads_only_new_ads(tmp_path):
    pages = {
        f"{BASE}/list/SW": FakeResponse(text="1|Job one|2026-10-15"),
        f"{BASE}/ad/1": FakeResponse(text="Job one|"),
    }
    collector, client = make_collector(tmp_path, pages)
    collector.collect(["IT"])
    client.requested.clear()

    result = collector.collect(["IT"])

    assert result.new_ads == {"IT": 0} and result.already_stored == 1
    assert client.requested == [f"{BASE}/list/SW"]


def test_flyer_image_is_saved_next_to_the_page(tmp_path):
    pages = {
        f"{BASE}/list/SW": FakeResponse(text="7|Designer|2026-10-15"),
        f"{BASE}/ad/7": FakeResponse(text=f"Designer|{BASE}/flyers/7.png"),
        f"{BASE}/flyers/7.png": FakeResponse(content=b"\x89PNG..."),
    }
    collector, _ = make_collector(tmp_path, pages)
    collector.collect(["IT"])

    [ad] = collector.reparse()
    assert ad.is_image_ad and ad.image_path.endswith("7.png")
    assert (tmp_path / "raw" / "example" / "IT" / "7.png").read_bytes() == b"\x89PNG..."
    assert ad.collected_at == "2026-10-17T10:00:00+00:00"


def test_missing_and_disallowed_ad_pages_are_skipped(tmp_path):
    pages = {
        f"{BASE}/list/SW": FakeResponse(text="1|Gone|2026-10-15\n2|Private|2026-10-14"),
        f"{BASE}/ad/2": RobotsDisallowed(f"{BASE}/ad/2"),
    }
    collector, _ = make_collector(tmp_path, pages)
    result = collector.collect(["IT"])
    assert result.gone == 1 and len(result.skipped) == 1 and result.new_ads == {"IT": 0}


def test_site_blocked_stops_the_run(tmp_path):
    pages = {
        f"{BASE}/list/SW": FakeResponse(text="1|Job|2026-10-15"),
        f"{BASE}/ad/1": SiteBlocked("HTTP 429"),
    }
    collector, _ = make_collector(tmp_path, pages)
    with pytest.raises(SiteBlocked):
        collector.collect(["IT"])


def test_collector_rejects_another_sites_config(tmp_path):
    other = SiteConfig(name="other", enabled=True, base_url=BASE, categories={})
    with pytest.raises(ValueError):
        ExampleCollector(other, FakeClient({}), Storage(tmp_path))


def test_image_extension_from_url_or_content_type():
    assert image_extension("https://x.lk/a/flyer.JPG", None) == ".jpg"
    assert image_extension("https://x.lk/image?id=4", "image/png") == ".png"
    assert image_extension("https://x.lk/image?id=4", None) == ".img"
