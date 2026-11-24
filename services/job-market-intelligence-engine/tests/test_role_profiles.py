"""Role profiles for C03 (the contract tables), on a temporary SQLite database."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select

from app.collectors.models import EXPIRED, JobAd, ListingEntry
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.database.contract import (
    metadata,
    requirement_evidence,
    role_profile_certifications,
    role_profile_education,
    role_profile_experience,
    role_profile_requirements,
    role_profiles,
)
from app.database.loader import load
from app.database.market_pulse import load_analysed
from app.database.role_profiles import build_profiles, publish, publish_role_profiles
from app.processing.roles import RoleTaxonomy
from app.processing.skills import SkillLexicon, write_profile

TEXT = ("Requirements:\nBachelor's degree in Human Resource Management\nExcellent communication skills in English\n"
        "Experience with payroll and HR administration\nKnowledge of labour law and MS Excel")
NOW = datetime(2026, 11, 24, 6, 0, tzinfo=timezone.utc)


def ad(job_id, title="HR Executive", status="active", experience="2+ years", text=TEXT):
    return clean_ad(JobAd(site="topjobs", job_id=job_id, url=f"https://www.topjobs.lk/ad?jc={job_id}", sectors=["HR"],
                          job_title=title, company="ABC (Pvt) Ltd", description_text=text,
                          experience_level=experience, collected_at="2026-10-17T08:00:00+00:00", status=status))


@pytest.fixture
def storage(tmp_path):
    storage = Storage(tmp_path / "data")
    for job_id in "123456":
        entry = ListingEntry("topjobs", job_id, f"https://www.topjobs.lk/ad?jc={job_id}", "HR", "HAT")
        storage.save_raw(entry, "<html></html>", "2026-10-17T08:00:00+00:00")
    storage.write_jsonl("topjobs", [
        ad("1"), ad("2", experience="3–5 years"), ad("3", experience=None),  # 3 × HR Executive / Officer
        ad("4", title="Senior HR Executive"),  # SENIOR: only one ad → DRAFT
        ad("5", title="Payroll Officer"),  # Payroll has no SSKS role id → not published
        ad("6", status=EXPIRED),  # expired ads are left out
    ])
    storage.append_sync_log({"synced_at": "2026-10-18T08:00:00+00:00", "site": "topjobs", "live_on_homepage": 1,
                             "listed": 6, "new_ads": 6, "active": 5, "expired": 1, "removed": 0, "reactivated": 0,
                             "unconfirmed": 0})
    write_profile(storage, ["topjobs"])  # the role and skills of each ad, which the loader stores
    return storage


@pytest.fixture
def engine(tmp_path, storage):
    engine = create_engine(f"sqlite:///{tmp_path / 'skillaro.db'}")
    load(engine, storage, ["topjobs"])
    metadata.create_all(engine)  # on Neon these come from infrastructure/neon/setup.sql
    return engine


def rows(engine, table, **where):
    query = select(table)
    for name, value in where.items():
        query = query.where(table.c[name] == value)
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(query).mappings()]


def test_profiles_per_role_and_career_level(engine):
    result = publish_role_profiles(engine, ["topjobs"], now=NOW)

    assert (result.published, result.drafts) == (1, 1)
    assert result.unmapped_roles == {"Payroll": 1}
    mid = rows(engine, role_profiles, career_level="MID_LEVEL")[0]
    assert (mid["role_id"], mid["mapping_status"], mid["profile_status"], mid["profile_version"]) == (
        "RL-000016", "VERIFIED", "PUBLISHED", "2026-10-18")  # version = date of the newest sync
    assert (mid["job_posting_count"], mid["ads_with_text"], mid["sector"]) == (3, 3, "HR")
    senior = rows(engine, role_profiles, career_level="SENIOR")[0]
    assert senior["profile_status"] == "DRAFT"  # fewer than 3 readable ads


def test_requirements_education_and_experience(engine):
    publish_role_profiles(engine, ["topjobs"], now=NOW)
    profile_id = rows(engine, role_profiles, career_level="MID_LEVEL")[0]["profile_id"]

    requirements = {r["standard_name"]: r for r in rows(engine, role_profile_requirements, profile_id=profile_id)}
    communication = requirements["Communication"]
    assert float(communication["demand_weight"]) == float(communication["demand_frequency"]) == 1.0
    assert (communication["mapping_status"], communication["skill_id"], communication["skill_type"]) == (
        "UNMAPPED", None, "BEHAVIOURAL")  # no SSKS here
    assert communication["required_proficiency_level"] is None  # never invented
    assert "Bachelor's degree" not in requirements  # qualifications are not skills

    education = rows(engine, role_profile_education, profile_id=profile_id)
    assert [(e["qualification_level"], e["completion_requirement"], e["job_ads_count"]) for e in education] == [
        ("SLQF_5", "COMPLETED", 3)]
    experience = rows(engine, role_profile_experience, profile_id=profile_id)[0]
    assert (float(experience["minimum_years"]), experience["job_ads_count"]) == (2.5, 2)  # median of 2 and 3
    evidence = rows(engine, requirement_evidence, requirement_id=communication["requirement_id"])
    assert sorted(e["job_id"] for e in evidence) == ["1", "2", "3"]
    assert rows(engine, role_profile_certifications) == []


def test_ssks_ids_make_requirements_verified(engine):
    lexicon = SkillLexicon.load()
    analysed, _, _ = load_analysed(engine, ["topjobs"], False, lexicon)
    profiles, _ = build_profiles(analysed, RoleTaxonomy.load(), "2026-10-18", {"Communication": ("SK-000123",)})
    with engine.begin() as conn:
        publish(conn, profiles, NOW)

    communication = rows(engine, role_profile_requirements, standard_name="Communication")[0]
    assert (communication["mapping_status"], communication["skill_id"]) == ("VERIFIED", "SK-000123")


def test_publishing_again_without_changes_writes_nothing(engine):
    publish_role_profiles(engine, ["topjobs"], now=NOW)
    before = len(rows(engine, role_profile_requirements))

    result = publish_role_profiles(engine, ["topjobs"], now=NOW)

    assert (result.published, result.drafts, result.unchanged) == (0, 0, 2)
    assert len(rows(engine, role_profile_requirements)) == before


def test_a_changed_profile_gets_a_new_version_and_archives_the_old(engine, storage):
    publish_role_profiles(engine, ["topjobs"], now=NOW)
    storage.write_jsonl("topjobs", [ad("1"), ad("2", experience="3–5 years"), ad("3", experience=None),
                                    ad("7"), ad("4", title="Senior HR Executive"), ad("5", title="Payroll Officer"),
                                    ad("6", status=EXPIRED)])
    write_profile(storage, ["topjobs"])
    load(engine, storage, ["topjobs"])

    publish_role_profiles(engine, ["topjobs"], now=NOW)

    mid = sorted(rows(engine, role_profiles, career_level="MID_LEVEL"), key=lambda r: r["profile_version"])
    assert [(p["profile_version"], p["profile_status"], p["job_posting_count"]) for p in mid] == [
        ("2026-10-18", "ARCHIVED", 3), ("2026-10-18.2", "PUBLISHED", 4)]  # versions never change
