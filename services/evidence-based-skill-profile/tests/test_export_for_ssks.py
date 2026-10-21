from scripts.build_dictionary import _load_seed
from scripts.export_for_ssks import alias_additions, alias_removals, new_skill_candidates
from tests.test_build_dictionary import _make_custom, _make_source


def test_new_skill_candidates_use_the_ssks_candidate_fields(tmp_path):
    seed = _load_seed(_make_source(tmp_path))
    rows = new_skill_candidates(seed, _make_custom(tmp_path))
    assert rows == [{
        "entity_type": "SKILL",
        "submitted_name": "Adaptability",
        "aliases": "adaptable|flexibility",
        "proposed_skill_type": "OTHER_SKILL",
        "proposed_skill_nature": "BEHAVIOURAL",
        "domains": "",
        "source_component": "C02",
        "source_reference": "C02-000001",
    }]


def test_new_skill_candidates_skip_skills_ssks_now_has(tmp_path):
    seed = _load_seed(_make_source(tmp_path))
    seed["SK-000099"] = {"name": "Adaptability", "aliases": []}
    assert new_skill_candidates(seed, _make_custom(tmp_path)) == []


def test_alias_additions_skip_aliases_ssks_already_has(tmp_path):
    seed = _load_seed(_make_source(tmp_path))
    rows = alias_additions(seed, _make_custom(tmp_path))
    assert [(r["alias"], r["skill_id"]) for r in rows] == [("JS", "SK-000002"), ("MS Excel", "SK-000005")]


def test_alias_removals_cover_blocklist_duplicates_and_moved_aliases(tmp_path):
    seed = _load_seed(_make_source(tmp_path))
    rows = alias_removals(seed, _make_custom(tmp_path))
    assert [(r["alias"], r["skill_id"], r["correct_skill_id"]) for r in rows] == [
        ("Mocha", "SK-000002", ""),
        ("MS Excel", "SK-000006", "SK-000005"),
        ("Python", "SK-000001", "SK-000004"),
    ]
