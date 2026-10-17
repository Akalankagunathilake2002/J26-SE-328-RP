"""The data quality report, built from a small data/ folder with known numbers. No network."""

import pytest

from app.collectors.config import Settings
from app.collectors.models import JobAd, ListingEntry
from app.collectors.report import render, sector_quality, write_report
from app.collectors.run import main as run_main
from app.collectors.storage import Storage

SECTORS = ["IT", "HR", "Management", "Agriculture"]
URL = "https://www.topjobs.lk/employer/JobAdvertismentServlet?jc={}"


def store(storage, job_id, sector, category):
    entry = ListingEntry("topjobs", job_id, URL.format(job_id), sector, category)
    storage.save_raw(entry, "<html></html>", "2026-10-17T10:00:00+00:00")
    return entry


@pytest.fixture
def storage(tmp_path):
    """HR: two image ads and one text ad. IT: one text ad (also listed under Management) and a
    re-post of it that deduplication removed. Agriculture: nothing collected."""
    storage = Storage(tmp_path)
    for job_id in ("1", "2", "3"):
        store(storage, job_id, "HR", "HAT")
    store(storage, "4", "IT", "SDQ")
    storage.add_listing(ListingEntry("topjobs", "4", URL.format("4"), "Management", "COM"))
    store(storage, "5", "IT", "SDQ")

    def ad(job_id, sectors, **fields):
        return JobAd(site="topjobs", job_id=job_id, url=URL.format(job_id), sectors=sectors, **fields)

    storage.write_jsonl("topjobs", [
        ad("1", ["HR"], is_image_ad=True, company="ABC", posted_date="2026-10-17", closing_date="2026-10-29"),
        ad("2", ["HR"], is_image_ad=True, location="Colombo", posted_date="2026-10-17"),
        ad("3", ["HR"], location="Kandy", company="XYZ", description_text="Requirements: payroll",
           experience_level="2+ years", posted_date="2026-10-16", closing_date="2026-10-30"),
        ad("4", ["IT", "Management"], location="Colombo", company="Tech Co",
           description_text="Java and SQL", posted_date="2026-10-15", closing_date="2026-10-31"),
    ])
    storage.write_dedup_log([{"kept": "topjobs:4", "removed": "topjobs:5", "reason": "similar_text", "score": 96}])
    storage.record_listing_counts("topjobs", {"HR": 207, "IT": 282}, "2026-10-17T10:00:00+00:00")
    return storage


def test_counts_per_sector(storage):
    rows = {row.sector: row for row in sector_quality(storage, "topjobs", SECTORS)}

    hr, it, management, agriculture = rows["HR"], rows["IT"], rows["Management"], rows["Agriculture"]
    assert (hr.live_on_site, hr.collected, hr.duplicates, hr.active) == (207, 3, 0, 3)
    assert (hr.image_ads, hr.text_ads, hr.verdict) == (2, 1, "No – needs OCR")
    assert (it.live_on_site, it.collected, it.duplicates, len(it.ads)) == (282, 2, 1, 1)
    assert it.verdict == "Yes"  # its one ad is text
    assert (management.live_on_site, management.collected, len(management.ads)) == (None, 1, 1)
    assert (agriculture.collected, agriculture.verdict) == (0, "No data yet")


def test_missing_values(storage):
    hr = {row.sector: row for row in sector_quality(storage, "topjobs", SECTORS)}["HR"]
    assert hr.missing_share("location") == pytest.approx(1 / 3)
    assert hr.missing_share("company") == pytest.approx(1 / 3)
    assert hr.missing_share("description / requirements") == pytest.approx(2 / 3)
    assert hr.missing_share("salary_text") == 1
    assert hr.missing_share("posted_date") == 0


def test_rendered_report(storage):
    text = render("topjobs", sector_quality(storage, "topjobs", SECTORS), "2026-10-17T10:00:00+00:00", "now")

    assert "| HR | 207 | 3 | 3 | 0 | 2 (67%) | 1 (33%) | No – needs OCR |" in text
    assert "| IT | 282 | 2 | 1 | 1 | 0 (0%) | 1 (100%) | Yes |" in text
    assert "| Agriculture | – | 0 | 0 | 0 | 0 | 0 | No data yet |" in text
    assert "| HR | 33% | 33% | 67% | 100% | 67% | 0% | 33% |" in text
    assert "| Agriculture | – | – | – | – | – | – | – |" in text


def test_listing_counts_are_kept_per_sector_across_runs(storage):
    storage.record_listing_counts("topjobs", {"HR": 210}, "2026-10-18T10:00:00+00:00")
    counts = storage.listing_counts()["topjobs"]
    assert counts["HR"] == {"listed": 210, "checked_at": "2026-10-18T10:00:00+00:00"}
    assert counts["IT"]["listed"] == 282  # not part of this run, so unchanged


def test_report_file_is_written(storage):
    path = write_report(storage, "topjobs", SECTORS)
    assert path.name == "quality_report.md" and "# Data quality report" in path.read_text()


def test_every_run_refreshes_the_report(tmp_path):
    store(Storage(tmp_path), "1", "HR", "HAT")
    assert run_main(["--site", "topjobs", "--reparse"], settings=Settings(tmp_path, None)) == 0
    assert (tmp_path / "processed" / "quality_report.md").exists()
