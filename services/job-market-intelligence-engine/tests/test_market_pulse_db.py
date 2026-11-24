"""Market Pulse from the database: the same profile as skill_profile.json, on a temporary SQLite database."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import app.main as api
from app.collectors.models import EXPIRED, JobAd, ListingEntry
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.database.loader import load
from app.database.market_pulse import profile_from_database
from app.processing.skills import write_profile
from tests.test_database import TEXT

client = TestClient(api.app)


def ad(job_id, status="active", sectors=("HR",), job_title="HR Executive", description_text=TEXT, **fields):
    return clean_ad(JobAd(site="topjobs", job_id=job_id, url=f"https://www.topjobs.lk/ad?jc={job_id}",
                          sectors=list(sectors), job_title=job_title, company="ABC (Pvt) Ltd",
                          description_text=description_text, posted_date="2026-10-17", closing_date="2026-10-30",
                          collected_at="2026-10-17T08:00:00+00:00", status=status, **fields))


@pytest.fixture
def storage(tmp_path):
    """Three active ads in two sectors, one banner-only flyer and an expired ad, with the profile file."""
    storage = Storage(tmp_path / "data")
    for job_id in ("1", "2", "3", "4", "5"):
        entry = ListingEntry("topjobs", job_id, f"https://www.topjobs.lk/ad?jc={job_id}", "HR", "HAT")
        storage.save_raw(entry, "<html></html>", "2026-10-17T08:00:00+00:00")
    storage.write_jsonl("topjobs", [
        ad("1", sectors=("HR", "Management")),
        ad("2"),
        ad("3", sectors=("IT",), job_title="Junior Software Engineer", experience_level="2+ years"),
        ad("4", description_text="We're hiring!"),  # banner only
        ad("5", status=EXPIRED),
    ])
    storage.append_sync_log({"synced_at": "2026-10-18T08:00:00+00:00", "site": "topjobs", "live_on_homepage": 3245,
                             "listed": 207, "new_ads": 5, "active": 4, "expired": 1, "removed": 0, "reactivated": 0,
                             "unconfirmed": 0})
    write_profile(storage, ["topjobs"])
    return storage


@pytest.fixture
def db_url(tmp_path, storage):
    url = f"sqlite:///{tmp_path / 'job_market.db'}"
    load(create_engine(url), storage, ["topjobs"])
    return url


def file_profile(storage):
    return json.loads((storage.processed_dir / "skill_profile.json").read_text(encoding="utf-8"))


def without_times(profile):
    """generated_at (file: written at; database: last sync) and last_checked (file: listing log) differ."""
    profile = {**profile, "generated_at": None}
    profile["sources"] = [{**s, "last_checked": None} for s in profile["sources"]]
    return profile


def test_the_database_gives_the_same_profile_as_the_file(storage, db_url):
    from_db = profile_from_database(create_engine(db_url), ["topjobs"])

    assert without_times(from_db) == without_times(file_profile(storage))
    assert from_db["totals"]["ads"] == 4  # the expired ad is left out
    assert from_db["generated_at"] == "2026-10-18T08:00:00+00:00"  # the last sync
    assert from_db["sources"][0]["last_checked"] == "2026-10-18T08:00:00+00:00"


def test_an_empty_database_gives_no_profile(tmp_path, storage):
    engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    load(engine, Storage(tmp_path / "nothing"), ["topjobs"])  # creates the tables, loads no ads
    assert profile_from_database(engine, ["topjobs"]) is None


@pytest.fixture
def api_env(monkeypatch, storage):
    monkeypatch.setenv("SKILLBRIDGE_DATA_DIR", str(storage.root))
    monkeypatch.setattr(api, "_cache", {"url": None, "at": 0.0, "profile": None, "engine": None})
    return monkeypatch


def test_the_api_reads_the_database_when_it_is_set(api_env, db_url):
    api_env.setenv("SKILLBRIDGE_DATABASE_URL", db_url)
    body = client.get("/jobs/market-pulse").json()
    assert body["data_source"] == "database"
    assert body["totals"]["ads"] == 4


def test_the_api_uses_the_file_without_a_database(api_env):
    api_env.delenv("SKILLBRIDGE_DATABASE_URL", raising=False)
    body = client.get("/jobs/market-pulse").json()
    assert body["data_source"] == "file"
    assert body["totals"]["ads"] == 4


def test_the_api_falls_back_to_the_file_when_the_database_is_down(api_env, caplog):
    api_env.setenv("SKILLBRIDGE_DATABASE_URL", "postgresql+psycopg://user:secret@127.0.0.1:1/skillaro")
    body = client.get("/jobs/market-pulse").json()
    assert body["data_source"] == "file"
    assert "secret" not in caplog.text  # the password is never logged
