"""The Market Pulse API, reading a skill profile written to a temporary data folder."""

import pytest
from fastapi.testclient import TestClient

from app.collectors.models import JobAd
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.main import app
from app.processing.skills import write_profile

client = TestClient(app)


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLBRIDGE_DATA_DIR", str(tmp_path))
    return tmp_path


def test_health():
    assert client.get("/jobs/health").json() == {"status": "healthy", "service": "job-market-intelligence-engine"}


def test_no_profile_yet(data_dir):
    response = client.get("/jobs/market-pulse")
    assert response.status_code == 404
    assert "No market data yet" in response.json()["detail"]


def test_market_pulse(data_dir):
    storage = Storage(data_dir)
    text = "Requirements:\n" + "Excellent communication skills and payroll experience with MS Excel. " * 3
    storage.write_jsonl("topjobs", [clean_ad(JobAd(
        site="topjobs", job_id="1", url="https://www.topjobs.lk/ad?jc=1", sectors=["HR"],
        job_title="HR Executive", description_text=text, collected_at="2026-10-17T07:52:07+00:00",
    ))])
    write_profile(storage, ["topjobs"])

    body = client.get("/jobs/market-pulse").json()

    assert body["totals"]["ads"] == 1 and body["roles"][0]["role"] == "HR Executive / Officer"
    assert {"skill": "Communication", "category": "Soft skill", "ssk_id": None, "ssk_ids": [], "source": "lexicon",
            "ads": 1, "share": 1.0} in body["skills"]
    assert body["extraction"]["extractor"] == "lexicon" and body["unverified"] == []
    assert [s["sector"] for s in body["sectors"]] == ["IT", "HR", "Management", "Agriculture"]
    sources = {source["site"]: source for source in body["sources"]}
    assert sources["topjobs"]["name"] == "topjobs.lk" and sources["topjobs"]["collected"] is True
    assert (sources["topjobs"]["ads"], sources["topjobs"]["last_collected"]) == (1, "2026-10-17T07:52:07+00:00")
    # Sites that are not collected are listed with the reason.
    assert sources["xpress"]["collected"] is False and "prohibit" in sources["xpress"]["reason"]
    assert sources["ikman"]["ads"] == 0
