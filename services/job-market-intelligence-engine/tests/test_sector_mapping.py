from pathlib import Path

import yaml

MAPPING = yaml.safe_load((Path(__file__).parent.parent / "config" / "sector_mapping.yaml").read_text())


def test_every_site_lists_all_four_sectors():
    for name, site in MAPPING["sites"].items():
        assert set(site["categories"]) == set(MAPPING["sectors"]), name
        assert any(site["categories"][sector] for sector in MAPPING["sectors"]), name


def test_topjobs_covers_every_sector():
    # itpro.lk is an IT job board and has no HR or Agriculture categories
    topjobs = MAPPING["sites"]["topjobs"]["categories"]
    assert all(topjobs[sector] for sector in MAPPING["sectors"])


def test_disabled_sites_say_why():
    for name, site in MAPPING["sites"].items():
        if not site["enabled"]:
            assert site.get("disabled_reason"), name


def test_collected_sites():
    enabled = [name for name, site in MAPPING["sites"].items() if site["enabled"]]
    assert enabled == ["topjobs", "itpro"]


def test_agriculture_keywords_are_lowercase():
    keywords = MAPPING["agriculture_keywords"]
    assert keywords and all(word == word.lower() for word in keywords)
