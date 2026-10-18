"""Job roles, skill extraction and the skill profile, using the real config files. No network."""

import json

import pytest
import yaml

from app.collectors.models import EXPIRED, JobAd
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.processing.roles import DEFAULT_TAXONOMY, RoleMatch, RoleTaxonomy
from app.processing.skills import (
    BANNER_ONLY,
    CATEGORIES,
    DEFAULT_LEXICON,
    NO_REQUIREMENTS_SECTION,
    NOT_AGRICULTURE,
    SkillLexicon,
    analyse,
    build_profile,
    render,
    skill_text,
    write_profile,
)

TAXONOMY = RoleTaxonomy.load()
LEXICON = SkillLexicon.load()
AGRICULTURE_KEYWORDS = ["agriculture", "agricultural", "plantation", "farm", "estate"]


def ad(job_id, title, text=None, sectors=("HR",), **fields):
    """A processed ad: cleaned like the real pipeline, so requirements are filled in."""
    return clean_ad(JobAd(
        site="topjobs",
        job_id=job_id,
        url=f"https://www.topjobs.lk/employer/JobAdvertismentServlet?jc={job_id}",
        sectors=list(sectors),
        job_title=title,
        description_text=text,
        **fields,
    ))


def skills_in(text, sectors=("HR",)):
    return {skill.name for skill in LEXICON.find(text, sectors)}


# --- config files ---------------------------------------------------------------------------------


def test_lexicon_file_is_valid():
    entries = yaml.safe_load(DEFAULT_LEXICON.read_text())["skills"]
    names = [entry["skill"] for entry in entries]
    assert len(names) >= 100 and len(names) == len(set(names))
    for entry in entries:
        assert entry["category"] in CATEGORIES, entry["skill"]
        assert "ssk_id" in entry, entry["skill"]  # filled in when linked to Shared Skill Knowledge
        assert entry.get("aliases") or entry.get("patterns"), entry["skill"]
        assert all(alias == alias.lower() for alias in entry.get("aliases", [])), entry["skill"]


def test_taxonomy_file_is_valid():
    data = yaml.safe_load(DEFAULT_TAXONOMY.read_text())
    names = [role["role"] for role in data["roles"]]
    assert len(names) == len(set(names))
    assert {"HR Executive / Officer", "Software Engineer / Developer", "Management Trainee"} <= set(names)


# --- roles ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("title", "sector", "role"),
    [
        ("HR Executive", "HR", "HR Executive / Officer"),
        ("Executive – Human Resources", "HR", "HR Executive / Officer"),
        ("HR & Admin Executive", "HR", "HR Executive / Officer"),
        ("HR Executive / HR Assistant", "HR", "HR Executive / Officer"),  # the first title named
        ("HR Assistant", "HR", "HR Assistant"),
        ("Head of HR", "HR", "HR Manager"),
        ("Payroll Administrator", "HR", "Payroll"),
        ("Talent Acquisition Specialist | Senior Executive - Talent Acquisition", "HR",
         "Recruitment / Talent Acquisition"),
        ("Senior Software Engineer", "IT", "Software Engineer / Developer"),
        ("QA Engineer", "IT", "QA / Test Engineer"),
        ("UI/UX Designer", "IT", "UI/UX / Graphic Designer"),
        ("Quality Assurance Executive", "Agriculture", "Food Safety / Quality"),  # not software QA
        ("Management Trainee", "Management", "Management Trainee"),
    ],
)
def test_titles_map_to_roles(title, sector, role):
    match = TAXONOMY.classify(title, [sector])
    assert (match.role, match.mapped) == (role, True)


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("Senior Executive - Talent Acquisition", "Senior / Lead"),
        ("HR Assistant", "Assistant / Junior"),
        ("Head of HR", "Manager / Head"),
        ("Management Trainee", "Trainee / Intern"),
        ("HR Executive", "Executive / Officer"),
    ],
)
def test_seniority(title, level):
    assert TAXONOMY.classify(title, ["HR", "Management"]).seniority == level


def test_unmapped_titles_keep_a_cleaned_title():
    assert TAXONOMY.classify("URGENT - BARISTA (Female)", ["Management"]) == RoleMatch(
        "Barista", mapped=False, seniority="Executive / Officer"
    )
    # IT-only roles are not given to ads from other sectors.
    assert TAXONOMY.classify("Software Engineer", ["HR"]).mapped is False
    assert TAXONOMY.classify(None, ["HR"]).role == "Unknown title"


# --- skills -----------------------------------------------------------------------------------------


def test_aliases_match_whole_words_and_hyphenated_forms():
    found = skills_in("Strong problem-solving skills, MS Office / Excel knowledge and a team player")
    assert {"Problem solving", "Microsoft Office", "Microsoft Excel", "Teamwork"} <= found
    assert "Microsoft Excel" not in skills_in("Excellent written skills")


def test_degree_subjects_and_higher_degrees_are_not_misread():
    found = skills_in("Master's degree in Business Administration or HR administration experience")
    assert "Master's degree" in found and "HR administration & records" in found
    assert "Bachelor's degree" not in found and "Office administration" not in found


def test_networking_counts_only_in_it_ads():
    assert "Networking" in skills_in("Networking and firewall configuration", ["IT"])
    assert "Networking" not in skills_in("Strong networking and relationship building", ["HR"])


def test_ocr_misreads_are_recognised():
    assert "G.C.E. A/L" in skills_in("Passed G.C.E. AIL in Commerce")


def test_urls_and_company_name_are_not_read_as_skills():
    text = "Requirements:\nSend applications via www.abc.lk/applyhere.php\nSage Holdings is a great place"
    item = ad("1", "HR Executive", text, company="Sage Holdings")
    found = skill_text(item)
    assert "php" not in found and "Sage" not in found


def test_about_us_benefits_and_how_to_apply_are_skipped():
    text = (
        "About us\nWe are an ERP software company\n"
        "Job Responsibilities\nManage payroll\n"
        "Requirements:\nGood communication skills\n"
        "Benefits\nFree Excel training\n"
        "How to apply\nSend your CV"
    )
    assert skill_text(ad("1", "HR Executive", text)) == (
        "Job Responsibilities\nManage payroll\nRequirements:\nGood communication skills"
    )


# --- one ad -----------------------------------------------------------------------------------------

HR_EXECUTIVE_A = (
    "We are hiring an HR Executive.\nRequirements:\n"
    "Excellent communication skills in English and Sinhala\n"
    "Experience with payroll and HR administration\n"
    "Bachelor's degree in Business Administration\n"
    "Strong communication with staff at all levels\n"
    "How to apply\nApply via www.example.lk/applyhere.php before the closing date"
)
HR_EXECUTIVE_B = (
    "Requirements:\nGood communication skills\n"
    "At least 2 years of experience in a similar HR role\n"
    "Team player who can work under pressure and meet deadlines"
)
BARISTA = (
    "We are looking for a barista who loves coffee and people. You will prepare drinks, keep the "
    "counter clean and give every guest excellent customer service."
)


def test_flags():
    ads = [
        ad("1", "HR Executive", "WE ARE HIRING\nHR Executive"),
        ad("2", "Barista", BARISTA, sectors=["Management"]),
        ad("3", "HSE Officer", BARISTA.replace("barista", "safety officer"), sectors=["Agriculture"]),
        ad("4", "Field Officer", BARISTA, sectors=["Agriculture"], company="Lanka Plantations PLC"),
        ad("5", "Agricultural Officer", BARISTA, sectors=["Agriculture"]),
    ]
    flags = {item.ad.job_id: item.flags for item in analyse(ads, TAXONOMY, LEXICON, AGRICULTURE_KEYWORDS)}
    assert flags["1"] == [BANNER_ONLY]
    assert flags["2"] == [NO_REQUIREMENTS_SECTION]
    assert NOT_AGRICULTURE in flags["3"]
    assert NOT_AGRICULTURE not in flags["4"] and NOT_AGRICULTURE not in flags["5"]


def test_banner_only_ads_get_no_skills():
    [item] = analyse([ad("1", "HR Executive", "WE ARE HIRING\nHR Executive")], TAXONOMY, LEXICON, [])
    assert item.skills == [] and not item.has_text


# --- the profile -------------------------------------------------------------------------------------


@pytest.fixture
def profile():
    ads = [
        ad("1", "HR Executive", HR_EXECUTIVE_A),
        ad("2", "Executive – Human Resources", HR_EXECUTIVE_B),
        ad("3", "HR Executive", "WE ARE HIRING\nHR Executive"),  # banner only
        ad("4", "Barista", BARISTA, sectors=["Management"]),
    ]
    sources = [{"site": "topjobs", "ads": 4, "last_collected": "2026-10-17T10:00:00+00:00", "last_checked": None}]
    analysed = analyse(ads, TAXONOMY, LEXICON, AGRICULTURE_KEYWORDS)
    return build_profile(analysed, sources, "2026-10-17T10:00:00+00:00", sectors=["IT", "HR"])


def test_profile_counts_each_skill_once_per_ad(profile):
    role = profile["roles"][0]
    assert (role["role"], role["ads"], role["ads_with_text"]) == ("HR Executive / Officer", 3, 2)
    skills = {skill["skill"]: skill for skill in role["skills"]}
    # "communication" is mentioned twice in ad 1 and once in ad 2.
    assert (skills["Communication"]["ads"], skills["Communication"]["share"]) == (2, 1.0)
    assert (skills["Payroll"]["ads"], skills["Payroll"]["share"]) == (1, 0.5)
    assert skills["Payroll"]["category"] == "Domain knowledge" and skills["Payroll"]["ssk_id"] is None
    assert "PHP" not in skills and "Office administration" not in skills
    assert role["skills"][0]["skill"] == "Communication"  # most requested first


def test_profile_role_details(profile):
    role = profile["roles"][0]
    assert role["sectors"] == ["HR"] and role["mapped"] is True
    assert role["titles"] == ["Executive – Human Resources", "HR Executive"]
    assert role["experience"] == {"Not stated": 2, "2+ years": 1}
    assert role["seniority"] == {"Executive / Officer": 3}
    assert role["flags"] == {BANNER_ONLY: 1}


def test_profile_totals(profile):
    assert profile["totals"] == {"ads": 4, "ads_with_text": 3, "roles": 2, "unmapped_roles": 1, "unique_skills": 10}
    # Configured sectors first, even without ads; then any other sector found in the ads.
    assert [(s["sector"], s["ads"], s["ads_with_text"]) for s in profile["sectors"]] == [
        ("IT", 0, 0), ("HR", 3, 2), ("Management", 1, 1)
    ]
    hr_skills = {skill["skill"]: skill["share"] for skill in profile["sectors"][1]["skills"]}
    assert hr_skills["Communication"] == 1.0 and "Customer service" not in hr_skills
    assert profile["roles"][1]["role"] == "Barista" and profile["roles"][1]["mapped"] is False
    assert profile["skills"][0] == {
        "skill": "Communication", "category": "Soft skill", "ssk_id": None, "ssk_ids": [], "source": "lexicon",
        "ads": 2, "share": 0.667,
    }


def test_rendered_profile(profile):
    text = render(profile)
    assert "## HR Executive / Officer: 3 ads" in text
    assert "| Communication | Soft skill | 2 of 2 (100%) |" in text
    assert "Barista *(unmapped)*" in text
    assert "Flags: banner only, no requirements readable (1)" in text


def test_only_active_ads_unless_asked(tmp_path):
    storage = Storage(tmp_path)
    storage.write_jsonl("topjobs", [
        ad("1", "HR Executive", HR_EXECUTIVE_A, collected_at="2026-10-16T08:00:00+00:00"),
        ad("2", "HR Executive", HR_EXECUTIVE_B, status=EXPIRED, collected_at="2026-10-17T08:00:00+00:00"),
    ])

    md_path, json_path = write_profile(storage, ["topjobs"])
    active = json.loads(json_path.read_text())
    assert active["totals"]["ads"] == 1 and active["ad_statuses"] == ["active"]
    assert active["sources"][0]["last_collected"] == "2026-10-16T08:00:00+00:00"
    assert md_path.read_text().startswith("# Skill demand profile")

    _, json_path = write_profile(storage, ["topjobs"], include_inactive=True)
    history = json.loads(json_path.read_text())
    assert history["totals"]["ads"] == 2 and history["ad_statuses"] == ["active", "expired", "removed"]
