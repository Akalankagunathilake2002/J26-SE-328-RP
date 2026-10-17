"""topjobs parsing, tested on real pages saved in tests/fixtures/topjobs/ (contact details removed)."""

from pathlib import Path

from app.collectors.models import Category, ListingEntry, SiteConfig
from app.collectors.storage import Storage
from app.collectors.topjobs import TopjobsCollector, find_dates, job_code

FIXTURES = Path(__file__).parent / "fixtures" / "topjobs"
BASE = "https://www.topjobs.lk"
HR = Category(name="HR/Training", code="HAT")
CONFIG = SiteConfig(name="topjobs", enabled=True, base_url=BASE, categories={"HR": (HR,)})
AD_URL = (
    f"{BASE}/employer/JobAdvertismentServlet?rid=0&ac=DEFZZZ&jc=0001560048&ec=DEFZZZ"
    "&pg=applicant/vacancybyfunctionalarea.jsp"
)


def collector(tmp_path):
    return TopjobsCollector(CONFIG, client=None, storage=Storage(tmp_path))


def listing(tmp_path):
    return collector(tmp_path).parse_listing((FIXTURES / "listing.html").read_text(), "HR", HR)


def test_listing_url_uses_the_category_code(tmp_path):
    assert collector(tmp_path).listing_url(HR) == f"{BASE}/applicant/vacancybyfunctionalarea.jsp?FA=HAT"


def test_listing_reads_each_ad_row(tmp_path):
    entries = listing(tmp_path)

    assert [e.job_id for e in entries] == ["0001560048", "0001560024", "0001558758"]
    first = entries[0]
    assert first.url == AD_URL  # built from the row's createAlert(...) codes
    assert first.job_title == "HR Executive / HR Assistant"
    assert first.company == "Upcot Green Fields (Pvt) Ltd"
    assert first.location == "Colombo 2"
    assert (first.posted_date, first.closing_date) == ("2026-10-17", "2026-10-29")


def test_dates_repeated_in_html_comments_are_not_read_twice(tmp_path):
    third = listing(tmp_path)[2]
    assert (third.posted_date, third.closing_date) == ("2026-10-17", "2026-10-26")


def test_image_ad(tmp_path):
    entry = listing(tmp_path)[0]
    ad = collector(tmp_path).parse_ad((FIXTURES / "ad.html").read_text(), entry)

    assert ad.job_title == "HR Executive / HR Assistant"
    assert ad.company == "Upcot Green Fields (Pvt) Ltd"
    assert ad.location == "Colombo 2, Sri Lanka"
    assert ad.closing_date == "2026-10-29"
    assert ad.employment_type == "Full Time; Permanent; Onsite"
    assert ad.is_image_ad and ad.description_text is None
    assert ad.image_url == f"{BASE}/logo/DEFZZZ/5598cAAAA.png"


def test_text_ad_and_withheld_company(tmp_path):
    # A small sample (no real text-only ad saved yet), using the same element IDs as the real page.
    page = (
        '<h1 id="position">Management Trainee</h1><h2 id="employer">Company Name Withheld</h2>'
        '<div id="remark"><h3>Requirements</h3><p>'
        + "A degree in management and strong communication skills are expected. " * 4
        + "</p></div>"
    )
    entry = ListingEntry("topjobs", "0001175112", AD_URL, "Management", "COM", location="Colombo")
    ad = collector(tmp_path).parse_ad(page, entry)

    assert ad.company is None
    assert ad.location == "Colombo"  # taken from the listing when the ad page has none
    assert not ad.is_image_ad and ad.image_url is None
    assert ad.description_text.startswith("Requirements")


def test_job_code_and_date_formats():
    assert job_code(AD_URL) == "0001560048"
    assert find_dates("Opening Sat Oct 17 2026, closing 29/10/2026") == ["2026-10-17", "2026-10-29"]
    assert find_dates("2026-10-15 and 27-Oct-2026") == ["2026-10-15", "2026-10-27"]
    assert find_dates("Please refer the vacancy") == []
