"""SSKS linking, the NER/both extractor modes and candidate proposals, with a fake SSKS. No network."""

import json

import pytest
import requests

from app.collectors.config import Settings, load_settings
from app.collectors.models import JobAd
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.integrations.ssks import BATCH_LIMIT, SSKSClient, normalize_key
from app.processing.ner_extractor import Mention, clean_mention
from app.processing.roles import RoleTaxonomy
from app.processing.skills import (
    Extraction,
    SkillLexicon,
    analyse,
    build_profile,
    extraction_from_settings,
    extraction_summary,
    skill_text,
    write_profile,
)
from app.processing.ssks_candidates import FUZZY, SUBMITTED, TO_SUBMIT, find_candidates, submit

TAXONOMY = RoleTaxonomy.load()
LEXICON = SkillLexicon.load()

# What the fake SSKS knows: name → (status, method, id, preferred name)
KNOWN = {
    "python": ("MATCHED", "CANONICAL_NAME", "SK-000899", "Python"),
    "ms excel": ("MATCHED", "VERIFIED_ALIAS", "SK-000075", "use spreadsheets software"),
    "excel": ("MATCHED", "VERIFIED_ALIAS", "SK-000075", "use spreadsheets software"),
    "communication": ("SUGGESTED", None, None, "Telecommunications"),
}


class FakeResponse:
    def __init__(self, status_code, body=None):
        self.status_code, self._body, self.text = status_code, body, json.dumps(body)

    def json(self):
        return self._body


class FakeSSKS:
    """A requests.Session stand-in: answers /normalize/skills and /candidates/entities."""

    def __init__(self, down=False):
        self.down, self.calls, self.candidates = down, [], []

    def post(self, url, json=None, timeout=None):
        self.calls.append((url.rsplit("/ssks", 1)[-1], json))
        if self.down:
            raise requests.ConnectionError("refused")
        if url.endswith("/candidates/entities"):
            if normalize_key(json["submitted_name"]) in {normalize_key(c["submitted_name"]) for c in self.candidates}:
                return FakeResponse(409, {"detail": "A pending candidate already exists"})
            self.candidates.append(json)
            return FakeResponse(201, {"candidate_entity_id": f"CAND-{len(self.candidates)}"})
        return FakeResponse(200, {"results": [self._result(name) for name in json["items"]]})

    @staticmethod
    def _result(name):
        status, method, cid, preferred = KNOWN.get(normalize_key(name), ("UNMATCHED", None, None, None))
        if status == "SUGGESTED":
            return {"input_name": name, "status": status, "canonical_id": None, "preferred_name": None,
                    "matching_method": "FUZZY_SUGGESTION",
                    "suggestions": [{"canonical_id": "SK-000775", "preferred_name": preferred, "score": 0.84}]}
        return {"input_name": name, "status": status, "canonical_id": cid, "preferred_name": preferred,
                "matching_method": method, "suggestions": []}


def client(tmp_path, session=None, now="2026-10-18T10:00:00+00:00"):
    return SSKSClient("http://ssks.test/ssks", cache_path=tmp_path / "ssks_cache.json",
                      session=session or FakeSSKS(), now=lambda: now)


class FakeNer:
    """Finds the given words wherever they appear (a stand-in for a trained model)."""

    def __init__(self, *words, label="KNOWLEDGE"):
        self.words, self.label = words, label

    def extract(self, text):
        found = []
        for word in self.words:
            start = text.lower().find(word.lower())
            if start >= 0:
                found.append(Mention(text[start:start + len(word)], start, start + len(word), self.label))
        return found


TEXT = ("Requirements:\nGood communication skills and teamwork\nPython and MS Excel experience\n"
        "Degree in computer science with at least two years of relevant experience in a busy office")


def ad(job_id, text=TEXT, sectors=("IT",)):
    return clean_ad(JobAd(site="topjobs", job_id=job_id, url=f"https://www.topjobs.lk/ad?jc={job_id}",
                          sectors=list(sectors), job_title="Software Engineer", description_text=text))


def profile_for(extraction, ads):
    analysed = analyse(ads, TAXONOMY, LEXICON, [], extraction)
    return analysed, build_profile(analysed, [], "2026-10-18T10:00:00+00:00", sectors=["IT"],
                                   extraction=extraction_summary(analysed, extraction, LEXICON))


# --- the client --------------------------------------------------------------------------------------


def test_lookup_match_types(tmp_path):
    matches = client(tmp_path).lookup(["Python", "MS Excel", "Communication", "Teamwork"])
    assert (matches["Python"].match_type, matches["Python"].ssk_id) == ("exact", "SK-000899")
    assert (matches["MS Excel"].match_type, matches["MS Excel"].preferred_name) == ("alias", "use spreadsheets software")
    assert (matches["Communication"].match_type, matches["Communication"].suggestion) == ("fuzzy", "Telecommunications")
    assert matches["Teamwork"].match_type == "unmatched"
    assert [m.counted for m in matches.values()] == [True, True, False, False]


def test_lookup_sends_small_batches(tmp_path):
    session = FakeSSKS()
    client(tmp_path, session).lookup([f"skill {i}" for i in range(201)])
    assert [len(payload["items"]) for _, payload in session.calls] == [100, 100, 1]

    big = FakeSSKS()
    SSKSClient("http://ssks.test/ssks", session=big, batch_size=2000).lookup([f"s{i}" for i in range(501)])
    assert max(len(payload["items"]) for _, payload in big.calls) == BATCH_LIMIT  # the endpoint's limit


def test_cache_and_recheck(tmp_path):
    session = FakeSSKS()
    client(tmp_path, session).lookup(["Python", "Teamwork"])
    client(tmp_path, session, now="2026-10-20T10:00:00+00:00").lookup(["Python", "Teamwork"])
    assert len(session.calls) == 1  # both cached

    client(tmp_path, session, now="2026-10-26T10:00:00+00:00").lookup(["Python", "Teamwork"])
    assert session.calls[-1][1]["items"] == ["teamwork"]  # unmatched is asked again after 7 days; IDs are kept


def test_ssks_down_means_pending_not_failure(tmp_path):
    down = FakeSSKS(down=True)
    c = client(tmp_path, down)
    assert c.lookup(["Python"])["Python"].match_type == "pending" and c.reachable is False
    c.lookup(["Teamwork"])
    assert len(down.calls) == 1  # not retried in the same run

    assert client(tmp_path).lookup(["Python"])["Python"].match_type == "exact"  # looked up on the next run


# --- extractor modes ----------------------------------------------------------------------------------


def test_lexicon_mode_counts_as_before_and_adds_ssk_ids(tmp_path):
    _, plain = profile_for(Extraction("lexicon"), [ad("1")])
    analysed, linked = profile_for(Extraction("lexicon", ssks=client(tmp_path)), [ad("1")])

    assert [s["skill"] for s in linked["skills"]] == [s["skill"] for s in plain["skills"]]
    skills = {s["skill"]: s for s in linked["skills"]}
    assert skills["Python"]["ssk_id"] == "SK-000899"
    assert skills["Microsoft Excel"]["ssk_ids"] == ["SK-000075"]  # through its aliases
    assert skills["Communication"]["ssk_ids"] == []  # a fuzzy suggestion is not a match
    assert linked["unverified"] == []
    assert linked["extraction"]["lexicon_skills"] == len(LEXICON.skills)
    assert linked["extraction"]["lexicon_skills_linked"] == 2  # Python, Microsoft Excel


def test_ner_mode_counts_only_exact_and_alias_matches(tmp_path):
    ner = FakeNer("Python", "MS Excel", "communication", "teamwork")
    _, profile = profile_for(Extraction("ner", ner=ner, ssks=client(tmp_path)), [ad("1"), ad("2")])

    assert {s["skill"]: (s["ssk_id"], s["source"], s["share"]) for s in profile["skills"]} == {
        "Python": ("SK-000899", "ner", 1.0),
        "use spreadsheets software": ("SK-000075", "ner", 1.0),
    }
    unverified = {u["text"]: u for u in profile["unverified"]}
    assert unverified["communication"]["match_type"] == "fuzzy"
    assert unverified["communication"]["suggestion"] == "Telecommunications"
    assert unverified["teamwork"] == {"text": "teamwork", "ads": 2, "match_type": "unmatched", "suggestion": None}
    assert profile["extraction"]["mention_match_types"] == {"exact": 2, "alias": 2, "fuzzy": 2, "unmatched": 2,
                                                            "pending": 0}
    assert profile["extraction"]["mention_match_rate"] == 0.5


def test_both_mode_does_not_count_a_skill_twice(tmp_path):
    ner = FakeNer("Python", "teamwork", "communication")
    _, profile = profile_for(Extraction("both", ner=ner, ssks=client(tmp_path)), [ad("1")])

    names = [s["skill"] for s in profile["skills"]]
    assert names.count("Python") == 1 and "Teamwork" in names  # from the lexicon
    assert profile["unverified"] == []  # NER mentions the lexicon already counted are not listed again


def test_ner_mode_with_ssks_down_keeps_the_raw_skills(tmp_path):
    storage = Storage(tmp_path)
    storage.write_jsonl("topjobs", [ad("1")])
    extraction = Extraction("ner", ner=FakeNer("Python", "teamwork"), ssks=client(tmp_path, FakeSSKS(down=True)))

    _, json_path = write_profile(storage, ["topjobs"], extraction=extraction)

    profile = json.loads(json_path.read_text())
    assert profile["skills"] == [] and {u["match_type"] for u in profile["unverified"]} == {"pending"}
    assert profile["extraction"]["ssks_reachable"] is False
    rows = [json.loads(line) for line in (tmp_path / "processed" / "ad_skills.jsonl").read_text().splitlines()]
    assert [(r["text"], r["match_type"]) for r in rows] == [("Python", "pending"), ("teamwork", "pending")]
    text = skill_text(ad("1"))
    assert all(text[r["start"]:r["end"]] == r["text"] for r in rows)  # offsets point at the raw text


def test_extraction_from_settings_falls_back_to_the_lexicon(tmp_path):
    storage = Storage(tmp_path)
    assert extraction_from_settings(Settings(tmp_path, None), storage).ssks is None
    no_model = extraction_from_settings(Settings(tmp_path, None, skill_extractor="ner"), storage)
    assert no_model.mode == "lexicon"
    missing = extraction_from_settings(Settings(tmp_path, None, "both", tmp_path / "nothing", "http://x/ssks"), storage)
    assert missing.mode == "lexicon" and missing.ssks is not None


def test_extractor_setting_is_checked(tmp_path):
    assert load_settings(env={"SKILLBRIDGE_SKILL_EXTRACTOR": "NER"}, env_file=tmp_path / ".env").skill_extractor == "ner"
    with pytest.raises(ValueError):
        load_settings(env={"SKILLBRIDGE_SKILL_EXTRACTOR": "magic"}, env_file=tmp_path / ".env")


def test_mentions_are_trimmed():
    text = "• Strong Python, .NET and C++ skills (MS Excel)"
    assert clean_mention(text, 0, 16, "KNOWLEDGE").text == "Strong Python"
    assert clean_mention(text, 16, 21, "KNOWLEDGE").text == ".NET"
    assert clean_mention(text, 26, 30, "KNOWLEDGE").text == "C++"
    assert clean_mention("- 1 -", 0, 5, "SKILL") is None


# --- candidates -----------------------------------------------------------------------------------------


def rows(*specs):
    """(job_id, extractor, text, label, match_type[, lexicon_skill, lexicon_ssk_ids, name_match])"""
    out = []
    for job_id, extractor, text, label, match_type, *lexicon in specs:
        row = {"site": "topjobs", "job_id": job_id, "extractor": extractor, "text": text, "label": label,
               "match_type": match_type}
        if lexicon:
            row.update(lexicon_skill=lexicon[0], lexicon_ssk_ids=lexicon[1], lexicon_name_match_type=lexicon[2])
        out.append(row)
    return out


CANDIDATE_ROWS = rows(
    ("1", "ner", "Payroll processing", "SKILL", "unmatched"),
    ("2", "ner", "payroll processing", "SKILL", "unmatched"),
    ("1", "ner", "Hostel management", "SKILL", "unmatched"),  # one ad only
    ("1", "ner", "Python", "KNOWLEDGE", "exact"),
    ("2", "ner", "Python", "KNOWLEDGE", "exact"),
    ("1", "lexicon", "teamwork", "Soft skill", "unmatched", "Teamwork", [], "unmatched"),
    ("2", "lexicon", "team player", "Soft skill", "unmatched", "Teamwork", [], "unmatched"),
    ("1", "lexicon", "communication", "Soft skill", "fuzzy", "Communication", [], "fuzzy"),
    ("2", "lexicon", "communication", "Soft skill", "fuzzy", "Communication", [], "fuzzy"),
    ("1", "lexicon", "degree", "Qualification", "unmatched", "Bachelor's degree", [], "unmatched"),
    ("2", "lexicon", "degree", "Qualification", "unmatched", "Bachelor's degree", [], "unmatched"),
    ("1", "lexicon", "MS Excel", "Tool", "alias", "Microsoft Excel", ["SK-000075"], "unmatched"),
    ("2", "lexicon", "excel", "Tool", "alias", "Microsoft Excel", ["SK-000075"], "unmatched"),
)


def test_candidates_are_unmatched_skills_seen_in_two_ads():
    found = {c.name: c for c in find_candidates(CANDIDATE_ROWS, min_ads=2, submitted={})}
    assert set(found) == {"Payroll processing", "Teamwork", "Communication"}
    assert found["Payroll processing"].status == TO_SUBMIT and found["Teamwork"].status == TO_SUBMIT
    assert found["Communication"].status == FUZZY  # listed for review, never sent
    assert found["Teamwork"].payload()["proposed_skill_nature"] == "BEHAVIOURAL"
    assert found["Payroll processing"].payload()["source_reference"] == "2 job ads, e.g. topjobs:1"


def test_dry_run_sends_nothing_and_submit_sends_each_name_once(tmp_path):
    session = FakeSSKS()
    session.candidates.append({"submitted_name": "Teamwork"})  # already waiting for review in SSKS
    submitted = {}

    results = submit(client(tmp_path, session), find_candidates(CANDIDATE_ROWS, 2, submitted), submitted)

    assert results == {"created": 1, "exists": 1}
    assert [c["submitted_name"] for c in session.candidates] == ["Teamwork", "Payroll processing"]
    again = find_candidates(CANDIDATE_ROWS, 2, submitted)
    assert {c.name: c.status for c in again if c.source != "lexicon" or c.name == "Teamwork"} == {
        "Payroll processing": SUBMITTED, "Teamwork": SUBMITTED,
    }
