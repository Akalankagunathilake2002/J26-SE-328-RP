"""Personal-data removal, text extraction and deduplication."""

from app.collectors.dedup import deduplicate, normalize_url
from app.collectors.models import JobAd
from app.collectors.text_utils import (
    clean_ad,
    extract_experience,
    extract_requirements,
    extract_salary,
    html_to_text,
    scrub_personal_data,
)

# --- personal data --------------------------------------------------------------------------------


def test_removes_emails_and_phone_numbers():
    text = "Send your CV to hr.team@abc.lk or call 077 123 4567 / +94 11 234 5678 today."
    scrubbed = scrub_personal_data(text)
    assert "@" not in scrubbed.replace("[email removed]", "")
    assert "077" not in scrubbed and "234 5678" not in scrubbed
    assert scrubbed.count("[phone removed]") == 2


def test_removes_emails_whose_dot_was_lost_in_ocr():
    assert scrub_personal_data("Apply Now: ta@career4icom") == "Apply Now: [email removed]"


def test_keeps_job_codes_that_only_look_like_phone_numbers():
    assert "0001174519" in scrub_personal_data("Job reference 0001174519")


def test_removes_contact_lines_and_titled_names_but_keeps_requirements():
    text = (
        "Contact centre experience required\n"
        "Contact person: Nimal\n"
        "Hotline: 0112345678\n"
        "Applications to Mr. Kamal Perera, HR Manager"
    )
    scrubbed = scrub_personal_data(text)
    assert "Contact centre experience required" in scrubbed
    assert "Nimal" not in scrubbed and "Hotline" not in scrubbed
    assert "Kamal" not in scrubbed and "[name removed]" in scrubbed


def test_html_to_text_drops_scripts_and_blank_lines():
    html = "<div><h2>Requirements</h2><script>x()</script><ul><li>SQL</li><li>Python</li></ul></div>"
    assert html_to_text(html) == "Requirements\nSQL\nPython"


# --- extraction -----------------------------------------------------------------------------------


def test_requirements_section_stops_at_benefits():
    text = (
        "About us\nWe build software.\n"
        "Requirements:\nDegree in IT\nSkills in Python and SQL\n"
        "Benefits\nMedical cover"
    )
    assert extract_requirements(text) == "Degree in IT\nSkills in Python and SQL"


def test_requirements_heading_with_inline_content():
    assert extract_requirements("Key Skills: Payroll, Labour law") == "Payroll, Labour law"


def test_requirement_headings_seen_on_real_flyers():
    flyer = (
        "WE ARE HIRING\nJob Responsibilities\n= Process weekly payroll\n"
        "Experience and Qualifications\n— 2 years of experience in UK payroll.\n"
        "= Strong Excel skills\nInterested candidates please send your CV"
    )
    assert extract_requirements(flyer) == "2 years of experience in UK payroll.\nStrong Excel skills"
    ideal = "The ideal candidate should possess the following :\n© Degree in HR\nCandidates meeting above criteria"
    assert extract_requirements(ideal) == "Degree in HR"
    assert extract_requirements("Candidate Requrements\n¢ English Communication Skill") == "English Communication Skill"


def test_requirements_end_at_responsibilities_but_not_at_responsible():
    text = "Requirements:\nResponsible attitude\nTeamwork\nKey Responsibilities\nManage staff"
    assert extract_requirements(text) == "Responsible attitude\nTeamwork"


def test_office_skills_are_not_mistaken_for_names():
    scrubbed = scrub_personal_data("Ms Word / Excel Knowledge\nMS Office\nContact Ms. Perera")
    assert "Ms Word" in scrubbed and "MS Office" in scrubbed
    assert "Perera" not in scrubbed


def test_experience_formats():
    assert extract_experience("Minimum 2 years of experience in HR") == "2+ years"
    assert extract_experience("1-3 years experience in payroll") == "1–3 years"
    assert extract_experience("3+ years industry experience") == "3+ years"
    assert extract_experience("Should have at-least 3 years of HR experience") == "3+ years"
    assert extract_experience("Age 25-35 years with 2 years experience") == "2 years"
    assert extract_experience("16 years experience") is None  # OCR-mangled "1–6 years"
    assert extract_experience("Degree required") is None


def test_salary():
    assert extract_salary("Salary: Negotiable\nApply now") == "Negotiable"
    assert extract_salary("We offer Rs. 150,000 - 200,000 per month") == "Rs. 150,000 - 200,000"


def test_clean_ad_fills_fields_and_scrubs_text():
    ad = JobAd(
        site="topjobs",
        job_id="1",
        url="https://www.topjobs.lk/ad/1",
        description_text="Requirements:\n2+ years experience\nE-mail jobs@abc.lk\nBenefits\nBonus",
    )
    cleaned = clean_ad(ad)
    assert cleaned.experience_level == "2+ years"
    assert "jobs@abc.lk" not in cleaned.description_text
    assert cleaned.requirements_text == "2+ years experience\nE-mail [email removed]"


# --- deduplication --------------------------------------------------------------------------------


def make_ad(job_id, **fields):
    defaults = {"site": "topjobs", "url": f"https://www.topjobs.lk/ad?jc={job_id}", "sectors": ["IT"]}
    return JobAd(job_id=job_id, **{**defaults, **fields})


def test_url_normalization_ignores_query_order_and_fragments():
    assert normalize_url("https://x.lk/ad?b=2&a=1#top") == normalize_url("https://X.lk/ad/?a=1&b=2")


def test_same_url_in_two_sectors_is_kept_once_with_both_sectors():
    it = make_ad("1", sectors=["IT"], categories=["SDQ"])
    mgmt = make_ad("1", sectors=["Management"], categories=["COM"])
    unique, log = deduplicate([it, mgmt])
    assert len(unique) == 1
    assert unique[0].sectors == ["IT", "Management"] and unique[0].categories == ["COM", "SDQ"]
    assert log[0].reason == "same_url"


def test_reposted_text_ad_is_a_duplicate():
    text = "We need a software engineer with Java, Spring Boot and SQL. 3+ years experience."
    first = make_ad("1", job_title="Software Engineer", company="ABC (Pvt) Ltd", description_text=text)
    repost = make_ad(
        "2", job_title="Software Engineer.", company="ABC (Pvt) Ltd", description_text=text + "!"
    )
    unique, log = deduplicate([first, repost])
    assert [ad.job_id for ad in unique] == ["1"] and log[0].reason == "similar_text"


def test_image_ads_need_the_same_closing_date():
    a = make_ad("1", job_title="HR Executive", company="XYZ", is_image_ad=True, closing_date="2026-10-20")
    b = make_ad("2", job_title="HR Executive", company="XYZ", is_image_ad=True, closing_date="2026-10-20")
    c = make_ad("3", job_title="HR Executive", company="XYZ", is_image_ad=True, closing_date="2026-11-30")
    unique, log = deduplicate([a, b, c])
    assert [ad.job_id for ad in unique] == ["1", "3"]
    assert log[0].reason == "similar_image_ad"


def test_different_companies_are_never_duplicates():
    a = make_ad("1", job_title="Accountant", company="ABC Holdings", closing_date="2026-10-20")
    b = make_ad("2", job_title="Accountant", company="Lanka Tiles", closing_date="2026-10-20")
    unique, _ = deduplicate([a, b])
    assert len(unique) == 2
