import csv
from pathlib import Path

import pytest

from scripts.build_dictionary import (
    DictionaryError,
    build_dictionary,
    find_conflicts,
    write_dictionary,
)


def _write(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def _make_source(tmp_path: Path) -> Path:
    source = tmp_path / "seed"
    _write(
        source / "canonical_entities.csv",
        ["id", "entity_type", "name", "description", "skill_type", "concept_kind",
         "skill_nature", "review_status"],
        [
            ["SK-000002", "SKILL", "JavaScript", "", "Software", "PROGRAMMING_LANGUAGE",
             "TECHNICAL", "APPROVED"],
            ["SK-000001", "SKILL", "Python (computer programming)", "", "Software",
             "PROGRAMMING_LANGUAGE", "TECHNICAL", "APPROVED"],
            ["SK-000004", "SKILL", "Python", "", "Software", "PROGRAMMING_LANGUAGE",
             "TECHNICAL", "APPROVED"],
            ["SK-000005", "SKILL", "Microsoft Excel", "", "Software", "SOFTWARE_OR_TOOL",
             "TECHNICAL", "APPROVED"],
            ["SK-000006", "SKILL", "use spreadsheets software", "", "skill/competence",
             "OTHER_SKILL", "TECHNICAL", "APPROVED"],
            ["SK-000003", "SKILL", "Draft skill", "", "", "OTHER_SKILL", "", "PENDING_REVIEW"],
            ["RL-000001", "ROLE", "software developer", "", "", "ROLE", "", "APPROVED"],
        ],
    )
    _write(
        source / "aliases_and_domains.csv",
        ["id", "canonical_entity_id", "record_type", "value", "is_verified"],
        [
            ["AL-1", "SK-000002", "ALIAS", "Mocha", "false"],
            ["AL-2", "SK-000002", "ALIAS", "javascript", "false"],
            ["AL-3", "SK-000002", "ALIAS", "ECMAScript", "false"],
            ["DOM-1", "SK-000002", "DOMAIN", "IT", "1.0"],
            ["AL-4", "SK-000001", "ALIAS", "Python", "false"],
            ["AL-5", "SK-000006", "ALIAS", "MS Excel", "false"],
            ["AL-6", "SK-000005", "ALIAS", "spreadsheets", "false"],
            ["AL-7", "SK-000006", "ALIAS", "spreadsheets", "false"],
            ["AL-8", "RL-000001", "ALIAS", "developer", "false"],
            ["AL-9", "SK-000003", "ALIAS", "draft", "false"],
        ],
    )
    return source


def _make_custom(tmp_path: Path) -> Path:
    custom = tmp_path / "custom"
    _write(
        custom / "custom_skills_supplement.csv",
        ["skill_id", "name", "aliases", "domains", "skill_type", "concept_kind", "skill_nature"],
        [["C02-000001", "Adaptability", "adaptable|flexibility", "", "skill/competence",
          "OTHER_SKILL", "BEHAVIOURAL"]],
    )
    _write(custom / "alias_blocklist.csv", ["alias", "skill_id", "note"],
           [["Mocha", "SK-000002", "test framework"]])
    _write(custom / "alias_map.csv", ["alias", "skill_id", "note"],
           [["JS", "SK-000002", ""], ["MS Excel", "SK-000005", ""]])
    return custom


def _by_id(rows):
    return {row["skill_id"]: row for row in rows}


def test_seed_only_keeps_approved_skills_sorted_by_id(tmp_path):
    rows = build_dictionary(_make_source(tmp_path))
    assert [row["skill_id"] for row in rows] == [
        "SK-000001", "SK-000002", "SK-000004", "SK-000005", "SK-000006",
    ]
    assert _by_id(rows)["SK-000002"]["aliases"] == "Mocha|ECMAScript"
    assert _by_id(rows)["SK-000002"]["domains"] == "IT"


def test_skill_name_wins_over_another_skills_alias(tmp_path):
    rows = _by_id(build_dictionary(_make_source(tmp_path)))
    assert rows["SK-000001"]["aliases"] == ""
    assert rows["SK-000004"]["name"] == "Python"


def test_custom_files_add_skills_block_and_move_aliases(tmp_path):
    rows = _by_id(build_dictionary(_make_source(tmp_path), _make_custom(tmp_path)))
    assert rows["C02-000001"]["aliases"] == "adaptable|flexibility"
    assert rows["SK-000002"]["aliases"] == "ECMAScript|JS"
    assert rows["SK-000005"]["aliases"] == "spreadsheets|MS Excel"
    assert "MS Excel" not in rows["SK-000006"]["aliases"]


def test_supplement_skill_ssks_now_has_is_skipped_and_its_aliases_follow(tmp_path):
    source = _make_source(tmp_path)
    with (source / "canonical_entities.csv").open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["SK-000007", "SKILL", "Adaptability", "", "skill/competence",
                                "OTHER_SKILL", "BEHAVIOURAL", "APPROVED"])
    custom = _make_custom(tmp_path)
    _write(custom / "alias_map.csv", ["alias", "skill_id", "note"],
           [["adaptive", "C02-000001", ""]])

    replaced = {}
    rows = _by_id(build_dictionary(source, custom, replaced))

    assert replaced == {"C02-000001": "SK-000007"}
    assert "C02-000001" not in rows
    assert rows["SK-000007"]["aliases"] == "adaptive"


def test_unknown_skill_in_alias_map_is_an_error(tmp_path):
    custom = _make_custom(tmp_path)
    _write(custom / "alias_map.csv", ["alias", "skill_id", "note"], [["JS", "SK-999999", ""]])
    with pytest.raises(DictionaryError):
        build_dictionary(_make_source(tmp_path), custom)


def test_duplicate_supplement_id_is_an_error(tmp_path):
    custom = _make_custom(tmp_path)
    _write(
        custom / "custom_skills_supplement.csv",
        ["skill_id", "name", "aliases", "domains", "skill_type", "concept_kind", "skill_nature"],
        [["SK-000002", "Again", "", "", "", "", ""]],
    )
    with pytest.raises(DictionaryError):
        build_dictionary(_make_source(tmp_path), custom)


def test_find_conflicts_lists_terms_shared_by_several_skills(tmp_path):
    rows = build_dictionary(_make_source(tmp_path), _make_custom(tmp_path))
    assert find_conflicts(rows) == [
        {
            "term": "spreadsheets",
            "skill_ids": "SK-000005|SK-000006",
            "names": "Microsoft Excel|use spreadsheets software",
        }
    ]


def test_write_dictionary_round_trips(tmp_path):
    rows = build_dictionary(_make_source(tmp_path), _make_custom(tmp_path))
    output = tmp_path / "out" / "clean_skills.csv"
    write_dictionary(rows, output)
    with output.open(encoding="utf-8", newline="") as f:
        assert list(csv.DictReader(f)) == rows
