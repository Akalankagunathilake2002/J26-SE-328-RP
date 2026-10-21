import pytest
from httpx import AsyncClient

from app.extraction.matcher import SkillEntry
from app.normalisation.normaliser import Normaliser, clean_term, term_variants
from app.schemas.normalisation import MatchMethod
from app.semantic.skill_index import SkillIndex
from tests.fakes import KeywordReranker, WordEncoder

ENTRIES = [
    SkillEntry("SK-1", "Python", ()),
    SkillEntry("SK-2", "JavaScript", ("JS",)),
    SkillEntry("SK-3", "React", ("React.js",)),
    SkillEntry("SK-4", "Node.js", ()),
    SkillEntry("SK-5", "Java", ()),
    SkillEntry("SK-6", "Deep Learning", (), "machine learning with multi-layer neural networks"),
    SkillEntry("SK-7", "Machine Learning", (), "computers that learn from data with models"),
    SkillEntry("SK-8", "recruit employees", ("hiring",), "hiring new staff for a company"),
    SkillEntry("SK-9", "Kubernetes", ()),
    SkillEntry("SK-10", "Kubernetes alias owner", ("Python",)),  # name beats this alias
    SkillEntry("SK-11", "Postgres", ()),
    SkillEntry("SK-12", "Postgrex", ()),
]
ESCO = [SkillEntry("esco:1", "compose music", (), "write music for films")]


@pytest.fixture
def normaliser():
    encoder = WordEncoder()
    return Normaliser(ENTRIES, encoder, SkillIndex.build(ENTRIES, encoder),
                      esco_index=SkillIndex.build(ESCO, encoder))


def _one(normaliser: Normaliser, term: str):
    return normaliser.normalise([term])[0]


def test_clean_term_and_variants():
    assert clean_term("  • Python, ") == "python"
    assert term_variants("Python3") == ["python"]
    assert term_variants("Python 3.10") == ["python"]
    assert set(term_variants("ReactJS")) == {"react.js", "react"}
    assert "react" in term_variants("React-based")
    assert "node.js" in term_variants("Node JS")
    assert term_variants("python") == []


def test_exact_ignores_case_and_a_name_beats_an_alias(normaliser):
    result = _one(normaliser, "PYTHON")
    assert (result.skill_id, result.method, result.score) == ("SK-1", MatchMethod.EXACT, 1.0)
    assert _one(normaliser, "js").skill_id == "SK-2"


@pytest.mark.parametrize("term, skill_id", [
    ("Python3", "SK-1"), ("ReactJS", "SK-3"), ("Node JS", "SK-4"), ("React-based", "SK-3"),
])
def test_cleaned(normaliser, term, skill_id):
    result = _one(normaliser, term)
    assert (result.skill_id, result.method) == (skill_id, MatchMethod.CLEANED)


def test_fuzzy_fixes_spelling_mistakes(normaliser):
    result = _one(normaliser, "Javascrpit")  # two letters swapped = one edit
    assert (result.skill_id, result.method) == ("SK-2", MatchMethod.FUZZY)
    assert 0.8 < result.score < 1.0
    assert _one(normaliser, "Pyhton").skill_id == "SK-1"
    assert _one(normaliser, "Kubernets").skill_id == "SK-9"


def test_fuzzy_never_guesses_short_terms_or_ties(normaliser):
    assert _one(normaliser, "Jav").method != MatchMethod.FUZZY  # too short
    assert _one(normaliser, "Postgrez").method != MatchMethod.FUZZY  # Postgres or Postgrex?


def test_semantic_finds_other_wording(normaliser):
    result = _one(normaliser, "hiring new staff")
    assert (result.skill_id, result.method) == ("SK-8", MatchMethod.SEMANTIC)
    assert result.candidates[0].skill_id == "SK-8"


def test_reranker_can_change_the_choice():
    encoder = WordEncoder()
    index = SkillIndex.build(ENTRIES, encoder)
    term = "machine learning neural networks models data"  # close to SK-6 and SK-7
    assert Normaliser(ENTRIES, encoder, index, KeywordReranker("deep")).normalise(
        [term])[0].skill_id == "SK-6"
    assert Normaliser(ENTRIES, encoder, index, KeywordReranker("data")).normalise(
        [term])[0].skill_id == "SK-7"


def test_esco_candidate_and_unmatched(normaliser):
    result = _one(normaliser, "write music for films")
    assert (result.skill_id, result.method) == ("esco:1", MatchMethod.ESCO_CANDIDATE)
    result = _one(normaliser, "references available on request")
    assert (result.skill_id, result.method) == (None, MatchMethod.UNMATCHED)


def test_without_an_index_only_lexical_methods_run():
    plain = Normaliser(ENTRIES)
    assert plain.normalise(["Pyhton", "hiring new staff"])[1].method == MatchMethod.UNMATCHED


def test_switches_turn_layers_off():
    assert Normaliser(ENTRIES, use_cleaning=False).normalise(["Python3"])[0].method != "cleaned"
    assert Normaliser(ENTRIES, use_fuzzy=False).normalise(["Pyhton"])[0].method == "unmatched"


@pytest.mark.anyio
async def test_normalise_endpoint(client: AsyncClient, monkeypatch, normaliser):
    monkeypatch.setattr("app.api.routers.normalisation.get_normaliser", lambda: normaliser)
    response = await client.post("/api/v1/profile/normalise", json={"terms": ["Pyhton", "xyz"]})
    assert response.status_code == 200
    body = response.json()
    assert [(r["skill_id"], r["method"]) for r in body] == [("SK-1", "fuzzy"), (None, "unmatched")]
    response = await client.post("/api/v1/profile/normalise", json={"terms": []})
    assert response.status_code == 422


def test_acronyms_in_capitals_are_never_fuzzy_matched():
    normaliser = Normaliser([SkillEntry("SK-1", "Spark", ())])
    assert normaliser.normalise(["SPARC"])[0].method == MatchMethod.UNMATCHED
    assert normaliser.normalise(["Sparkk"])[0].method == MatchMethod.FUZZY


def test_fuzzy_needs_the_same_first_letter():
    normaliser = Normaliser([SkillEntry("SK-1", "ML systems", ())])
    assert normaliser.normalise(["IT systems"])[0].method == MatchMethod.UNMATCHED
    assert normaliser.normalise(["ML sytems"])[0].method == MatchMethod.FUZZY
