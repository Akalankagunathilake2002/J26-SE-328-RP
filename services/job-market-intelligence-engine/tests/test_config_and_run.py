"""Settings, site selection and the command line. No network."""

import json

import pytest

from app.collectors.config import Settings, load_settings, load_sites
from app.collectors.models import ListingEntry
from app.collectors.run import choose_sites, main
from app.collectors.storage import Storage


def test_mapping_loads_all_sites_with_their_categories():
    sites = load_sites()
    topjobs = sites["topjobs"]
    assert topjobs.enabled and topjobs.base_url == "https://www.topjobs.lk"
    assert [c.code for c in topjobs.categories["IT"]] == ["SDQ", "HNS", "ITT"]
    assert not sites["xpress"].enabled and sites["xpress"].categories["HR"][0].id == 29


def test_settings_from_env_and_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# local settings\nSKILLBRIDGE_CONTACT='me@example.com'\n")
    from_file = load_settings(env={}, env_file=env_file)
    assert from_file.contact == "me@example.com"
    assert from_file.data_dir.name == "data"

    from_env = load_settings(env={"SKILLBRIDGE_CONTACT": "other@example.com"}, env_file=env_file)
    assert from_env.contact == "other@example.com"


def test_choose_sites():
    sites = load_sites()
    assert choose_sites("all", sites) == ["topjobs"]
    assert choose_sites("topjobs", sites) == ["topjobs"]
    with pytest.raises(ValueError, match="written permission"):
        choose_sites("ikman", sites)
    with pytest.raises(ValueError, match="Unknown site"):
        choose_sites("linkedin", sites)


def test_disabled_site_is_refused_with_its_reason(tmp_path, capsys):
    assert main(["--site", "xpress", "--reparse"], settings=Settings(tmp_path, None)) == 2
    assert "prohibit" in capsys.readouterr().err


def test_reparse_rebuilds_processed_data_offline_without_personal_data(tmp_path):
    storage = Storage(tmp_path)
    page = (
        '<h1 id="position">Payroll Officer</h1><h2 id="employer">Lanka Foods PLC</h2>'
        '<div id="remark"><p>Requirements:</p><p>2+ years payroll experience.</p>'
        "<p>Send CVs to Ms. Dilani Fernando at careers@lankafoods.lk or 077 123 4567</p>"
        + "<p>Strong Excel skills and knowledge of labour law are essential for this role.</p>" * 3
        + "</div>"
    )
    entry = ListingEntry("topjobs", "0001175200", "https://www.topjobs.lk/employer/JobAdvertismentServlet?jc=0001175200", "HR", "HAT")
    storage.save_raw(entry, page, "2026-10-17T10:00:00+00:00")

    assert main(["--site", "topjobs", "--reparse"], settings=Settings(tmp_path, None)) == 0

    [record] = [json.loads(line) for line in (tmp_path / "processed" / "topjobs.jsonl").read_text().splitlines()]
    assert record["job_title"] == "Payroll Officer" and record["sectors"] == ["HR"]
    assert record["experience_level"] == "2+ years"
    text = record["description_text"]
    assert "careers@lankafoods.lk" not in text and "077 123 4567" not in text and "Dilani" not in text
    assert (tmp_path / "processed" / "combined.csv").exists()
    assert (tmp_path / "processed" / "dedup_log.csv").exists()
