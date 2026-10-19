"""Loading the collected ads into the database, on a temporary SQLite database. No Docker needed."""

import os

import pytest
from sqlalchemy import create_engine, func, select, text

from app.collectors.config import Settings
from app.collectors.models import EXPIRED, JobAd, ListingEntry
from app.collectors.run import main as run_main
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.database.loader import load
from app.database.schema import job_ad_sectors, job_ad_skills, job_ad_status_history, job_ads, sync_runs
from app.processing.skills import write_profile

TEXT = ("Requirements:\nExcellent communication skills in English\nExperience with payroll and HR administration\n"
        "Knowledge of labour law and MS Excel is essential for this busy HR office")


def ad(job_id, status="active", sectors=("HR",), **fields):
    return clean_ad(JobAd(site="topjobs", job_id=job_id, url=f"https://www.topjobs.lk/ad?jc={job_id}",
                          sectors=list(sectors), job_title="HR Executive", company="ABC (Pvt) Ltd",
                          description_text=TEXT, posted_date="2026-10-17", closing_date="2026-10-30",
                          collected_at="2026-10-17T08:00:00+00:00", status=status, **fields))


@pytest.fixture
def storage(tmp_path):
    """Two HR ads (one also listed under Management) and an expired one, with the profile files."""
    storage = Storage(tmp_path / "data")
    for job_id, sector in (("1", "HR"), ("2", "HR"), ("3", "HR")):
        entry = ListingEntry("topjobs", job_id, f"https://www.topjobs.lk/ad?jc={job_id}", sector, "HAT")
        storage.save_raw(entry, "<html></html>", "2026-10-17T08:00:00+00:00")
    storage.write_jsonl("topjobs", [ad("1", sectors=("HR", "Management")), ad("2"), ad("3", status=EXPIRED)])
    storage.append_sync_log({"synced_at": "2026-10-18T08:00:00+00:00", "site": "topjobs", "live_on_homepage": 3245,
                             "listed": 207, "new_ads": 3, "active": 2, "expired": 1, "removed": 0, "reactivated": 0,
                             "unconfirmed": 0})
    write_profile(storage, ["topjobs"])
    return storage


@pytest.fixture
def engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'job_market.db'}")


def count(engine, table):
    with engine.connect() as conn:
        return conn.execute(select(func.count()).select_from(table)).scalar_one()


def test_everything_is_loaded(storage, engine):
    result = load(engine, storage, ["topjobs"], now="2026-10-19T08:00:00+00:00")

    assert (result.ads, result.sector_rows, result.status_changes, result.sync_runs) == (3, 4, 3, 1)
    with engine.connect() as conn:
        row = conn.execute(select(job_ads).where(job_ads.c.job_id == "1")).mappings().one()
        statuses = dict(conn.execute(select(job_ads.c.job_id, job_ads.c.status)).all())
        sectors = conn.execute(select(job_ad_sectors.c.sector).where(job_ad_sectors.c.job_id == "1")).scalars().all()
        skills = conn.execute(select(job_ad_skills.c.counted_as).where(job_ad_skills.c.job_id == "1")).scalars().all()
        sync = conn.execute(select(sync_runs)).mappings().one()
    assert (row["role"], row["seniority"], row["has_text"], row["company"]) == (
        "HR Executive / Officer", "Executive / Officer", True, "ABC (Pvt) Ltd")
    assert str(row["closing_date"]) == "2026-10-30" and "payroll" in row["description_text"]
    assert statuses == {"1": "active", "2": "active", "3": "expired"}  # history is kept
    assert sorted(sectors) == ["HR", "Management"]
    assert {"Communication", "English", "Payroll", "Microsoft Excel"} <= set(skills)
    assert (sync["live_on_homepage"], sync["new_ads"]) == (3245, 3)


def test_loading_again_updates_without_duplicates(storage, engine):
    load(engine, storage, ["topjobs"])
    before = {t.name: count(engine, t) for t in (job_ads, job_ad_sectors, job_ad_skills, job_ad_status_history, sync_runs)}

    storage.write_jsonl("topjobs", [ad("1", sectors=("HR", "Management")), ad("2", status=EXPIRED), ad("3", status=EXPIRED)])
    load(engine, storage, ["topjobs"])

    after = {t.name: count(engine, t) for t in (job_ads, job_ad_sectors, job_ad_skills, job_ad_status_history, sync_runs)}
    assert after == before
    with engine.connect() as conn:
        assert conn.execute(select(job_ads.c.status).where(job_ads.c.job_id == "2")).scalar_one() == "expired"


def test_role_skill_demand_view_counts_active_ads(storage, engine):
    load(engine, storage, ["topjobs"])
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT role, sector, skill, ads, ads_with_text, share FROM role_skill_demand "
            "WHERE sector = 'HR' AND skill = 'Payroll'"
        )).mappings().all()
    assert [dict(r) for r in rows] == [
        {"role": "HR Executive / Officer", "sector": "HR", "skill": "Payroll", "ads": 2, "ads_with_text": 2, "share": 1.0}
    ]  # the expired ad is left out


def test_every_run_loads_the_database(tmp_path):
    entry = ListingEntry("topjobs", "1", "https://www.topjobs.lk/ad?jc=1", "HR", "HAT")
    Storage(tmp_path).save_raw(entry, f'<h1 id="position">HR Executive</h1><div id="remark">{TEXT}</div>',
                               "2026-10-17T08:00:00+00:00")
    url = f"sqlite:///{tmp_path / 'job_market.db'}"

    assert run_main(["--site", "topjobs", "--reparse", "--no-ocr"], settings=Settings(tmp_path, None, database_url=url)) == 0
    assert count(create_engine(url), job_ads) == 1


def test_a_database_that_is_down_does_not_stop_the_run(tmp_path, caplog):
    entry = ListingEntry("topjobs", "1", "https://www.topjobs.lk/ad?jc=1", "HR", "HAT")
    Storage(tmp_path).save_raw(entry, "<html></html>", "2026-10-17T08:00:00+00:00")
    down = "postgresql+psycopg://user:secret@127.0.0.1:1/job_market_db"  # nothing listens on port 1

    assert run_main(["--site", "topjobs", "--reparse", "--no-ocr"], settings=Settings(tmp_path, None, database_url=down)) == 0
    assert "database not updated" in caplog.text
    assert "secret" not in caplog.text  # the password is never logged
    assert (tmp_path / "processed" / "skill_profile.json").exists()


@pytest.mark.skipif(not os.environ.get("SKILLBRIDGE_TEST_DATABASE_URL"), reason="needs a PostgreSQL test database")
def test_on_postgresql(storage):
    """Run with SKILLBRIDGE_TEST_DATABASE_URL pointing to an empty PostgreSQL database."""
    engine = create_engine(os.environ["SKILLBRIDGE_TEST_DATABASE_URL"])
    load(engine, storage, ["topjobs"])
    load(engine, storage, ["topjobs"])
    assert count(engine, job_ads) == 3
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM role_skill_demand")).scalar_one() > 0
