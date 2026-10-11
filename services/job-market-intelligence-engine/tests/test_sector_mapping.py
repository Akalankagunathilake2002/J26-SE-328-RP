from pathlib import Path

import yaml

MAPPING = yaml.safe_load((Path(__file__).parent.parent / "config" / "sector_mapping.yaml").read_text())


def test_every_site_maps_all_four_sectors():
    for name, site in MAPPING["sites"].items():
        assert set(site["categories"]) == set(MAPPING["sectors"]), name
        assert all(site["categories"][sector] for sector in MAPPING["sectors"]), name


def test_disabled_sites_say_why():
    for name, site in MAPPING["sites"].items():
        if not site["enabled"]:
            assert site.get("disabled_reason"), name


def test_only_topjobs_is_collected():
    enabled = [name for name, site in MAPPING["sites"].items() if site["enabled"]]
    assert enabled == ["topjobs"]


def test_agriculture_keywords_are_lowercase():
    keywords = MAPPING["agriculture_keywords"]
    assert keywords and all(word == word.lower() for word in keywords)
