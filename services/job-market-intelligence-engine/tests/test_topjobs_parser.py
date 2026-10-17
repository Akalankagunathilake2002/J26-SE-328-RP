"""topjobs parsing.

The pages below are small samples built from the element IDs recorded in the feasibility check
(#position, #employer, #adview-job-location, #endDate, #remark). Add real saved pages to
tests/fixtures/topjobs/ and test against them before large collection runs.
"""

from app.collectors.models import Category, ListingEntry, SiteConfig
from app.collectors.storage import Storage
from app.collectors.topjobs import TopjobsCollector, find_dates, job_code

BASE = "https://www.topjobs.lk"
HR = Category(name="HR/Training", code="HAT")
CONFIG = SiteConfig(name="topjobs", enabled=True, base_url=BASE, categories={"HR": (HR,)})

LISTING = """
<table>
  <tr><td>1</td>
      <td><a href="/employer/JobAdvertismentServlet?ac=DEFZZZ&jc=0001175110&ec=DEFZZZ">HR Executive</a></td>
      <td>Wed Oct 15 2026</td><td>Mon Oct 27 2026</td></tr>
  <tr><td>2</td>
      <td><a href="/employer/JobAdvertismentServlet?ac=DEFZZZ&jc=0001175111&ec=DEFZZZ">HR Assistant</a></td>
      <td>14/10/2026</td><td>28/10/2026</td></tr>
  <tr><td><a href="/employer/JobAdvertismentServlet?ac=DEFZZZ&jc=0001175110&ec=DEFZZZ">HR Executive</a></td></tr>
  <tr><td><a href="/applicant/help.jsp">Help</a></td></tr>
</table>
"""

IMAGE_AD = """
<div class="header">
  <h1 id="position">HR Executive</h1>
  <h2 id="employer">ABC Holdings (Pvt) Ltd</h2>
  <span id="adview-job-location">Colombo</span>
  <span>Full Time</span> <span>Permanent</span> <span>Onsite</span>
</div>
<div>Closing date: <span id="endDate">Mon Oct 27 2026</span></div>
<div id="remark"><img src="/logo/ads/0001175110.png"></div>
"""

TEXT_AD = (
    '<div><h1 id="position">Management Trainee</h1><h2 id="employer">Company Name Withheld</h2></div>'
    '<div id="remark"><h3>Requirements</h3><p>'
    + "A degree in management and strong communication skills are expected. " * 4
    + "</p></div>"
)


def collector(tmp_path):
    return TopjobsCollector(CONFIG, client=None, storage=Storage(tmp_path))


def entry(job_id="0001175110"):
    return ListingEntry("topjobs", job_id, f"{BASE}/employer/JobAdvertismentServlet?jc={job_id}", "HR", "HAT")


def test_listing_url_uses_the_category_code(tmp_path):
    assert collector(tmp_path).listing_url(HR) == f"{BASE}/applicant/vacancybyfunctionalarea.jsp?FA=HAT"


def test_listing_finds_each_ad_once_with_its_dates(tmp_path):
    entries = collector(tmp_path).parse_listing(LISTING, "HR", HR)

    assert [e.job_id for e in entries] == ["0001175110", "0001175111"]
    first = entries[0]
    assert first.url.startswith(f"{BASE}/employer/JobAdvertismentServlet?")
    assert first.job_title == "HR Executive"
    assert (first.posted_date, first.closing_date) == ("2026-10-15", "2026-10-27")
    assert (entries[1].posted_date, entries[1].closing_date) == ("2026-10-14", "2026-10-28")


def test_image_ad(tmp_path):
    ad = collector(tmp_path).parse_ad(IMAGE_AD, entry())

    assert ad.job_title == "HR Executive"
    assert ad.company == "ABC Holdings (Pvt) Ltd"
    assert ad.location == "Colombo"
    assert ad.closing_date == "2026-10-27"
    assert ad.employment_type == "Full Time; Permanent; Onsite"
    assert ad.is_image_ad and ad.description_text is None
    assert ad.image_url == f"{BASE}/logo/ads/0001175110.png"


def test_text_ad_and_withheld_company(tmp_path):
    ad = collector(tmp_path).parse_ad(TEXT_AD, entry("0001175112"))

    assert ad.company is None
    assert not ad.is_image_ad and ad.image_url is None
    assert ad.description_text.startswith("Requirements")


def test_job_code_and_date_formats():
    assert job_code(f"{BASE}/employer/JobAdvertismentServlet?ac=X&jc=0001175110") == "0001175110"
    assert find_dates("Opening Wed Oct 15 2026, closing 27-Oct-2026") == ["2026-10-15", "2026-10-27"]
    assert find_dates("2026-10-15 and 28/10/2026") == ["2026-10-15", "2026-10-28"]
    assert find_dates("no dates here") == []
