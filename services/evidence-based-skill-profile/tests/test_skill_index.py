import csv

import pytest

from app.extraction.matcher import SkillEntry
from app.semantic.skill_index import (
    SkillIndex, SkillIndexError, load_esco_entries, load_ssks_esco_uris, texts_for,
)
from tests.fakes import WordEncoder

ENTRIES = [
    SkillEntry("SK-1", "Deep Learning", ("deep neural networks",),
               "machine learning with multi-layer neural networks"),
    SkillEntry("SK-2", "Recruitment", ("hiring",), "finding and hiring new staff for a company"),
    SkillEntry("SK-3", "JavaScript", ("JS",), ""),
]


@pytest.fixture
def index():
    return SkillIndex.build(ENTRIES, WordEncoder())


def test_each_skill_is_stored_as_name_aliases_and_description():
    kinds = [(t.kind, t.text) for t in texts_for(ENTRIES[0])]
    assert kinds == [
        ("name", "Deep Learning"),
        ("alias", "deep neural networks"),
        ("description", "Deep Learning: machine learning with multi-layer neural networks"),
    ]
    assert [t.kind for t in texts_for(ENTRIES[2])] == ["name", "alias"]  # no description


def test_search_finds_the_skill_by_its_description(index):
    [hits] = index.search(["trained neural networks"], WordEncoder())
    assert hits[0].skill_id == "SK-1"
    assert hits[0].matched_kind in {"alias", "description"}
    [hits] = index.search(["hiring new staff"], WordEncoder())
    assert hits[0].skill_id == "SK-2"


def test_each_skill_appears_once_with_its_best_score(index):
    [hits] = index.search(["deep learning neural networks"], WordEncoder(), top_k=5)
    ids = [hit.skill_id for hit in hits]
    assert len(ids) == len(set(ids))
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


def test_min_score_and_empty_queries(index):
    assert index.search([], WordEncoder()) == []
    [hits] = index.search(["completely unrelated words"], WordEncoder(), min_score=0.5)
    assert hits == []


def test_save_and_load(index, tmp_path):
    index.save(tmp_path, "ssks")
    loaded = SkillIndex.load(tmp_path, "ssks", "test-words")
    assert loaded.rows == index.rows
    assert loaded.search(["JS"], WordEncoder())[0][0].skill_id == "SK-3"


def test_load_refuses_a_missing_index_or_another_model(index, tmp_path):
    with pytest.raises(SkillIndexError, match="build_skill_index"):
        SkillIndex.load(tmp_path, "ssks", "test-words")
    index.save(tmp_path, "ssks")
    with pytest.raises(SkillIndexError, match="rebuild"):
        SkillIndex.load(tmp_path, "ssks", "another-model")


def test_esco_entries_skip_skills_ssks_already_has(tmp_path):
    esco = tmp_path / "skills_en.csv"
    with esco.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["conceptUri", "preferredLabel", "altLabels", "status", "description"])
        writer.writerow(["esco:1", "use Python", "Python\nPython 3", "released", "Write  code."])
        writer.writerow(["esco:2", "compose music", "", "released", "Write music."])
        writer.writerow(["esco:3", "old skill", "", "obsolete", ""])
    ids = tmp_path / "external_ids.csv"
    ids.write_text("id,canonical_entity_id,source_system,external_id,source_version\n"
                   "EXT-1,SK-000001,ESCO,esco:1,1.2.1\nEXT-2,RL-000001,ESCO,esco:2,1.2.1\n",
                   encoding="utf-8")

    in_ssks = load_ssks_esco_uris(ids)
    assert in_ssks == {"esco:1"}  # roles are not skills
    entries = load_esco_entries(esco, in_ssks)
    assert [(e.skill_id, e.aliases, e.description) for e in entries] == [
        ("esco:2", (), "Write music."),
    ]
    assert load_esco_entries(esco)[0].aliases == ("Python", "Python 3")
