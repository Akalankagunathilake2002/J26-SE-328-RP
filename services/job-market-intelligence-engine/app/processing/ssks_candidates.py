"""Propose skills the Shared Skill Knowledge Service doesn't know yet (POST /ssks/candidates/entities).

    python -m app.processing.ssks_candidates            # dry run: list them, nothing is sent
    python -m app.processing.ssks_candidates --submit   # send them (agree with the SSKS owner first)

Reads processed/ad_skills.jsonl (written with the skill profile, with SKILLBRIDGE_SSKS_URL set).
A skill is proposed only if SSKS returned it as UNMATCHED and it was seen in at least --min-ads ads
(default 2):

- lexicon skills: the lexicon name, if neither the name nor any alias has an SSKS ID and the name
  itself is UNMATCHED (qualifications are left out);
- NER mentions: the text as written most often, if UNMATCHED.

Fuzzy matches are listed for review but never sent (SSKS may already have the skill under another
name). Each name is sent once: results are kept in processed/ssks_candidates_submitted.json, and
an HTTP 409 (already in SSKS, or already waiting for review) counts as done. The dry run writes
processed/ssks_candidates.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.collectors.base import utc_now
from app.collectors.config import load_settings
from app.collectors.storage import Storage
from app.integrations.ssks import SSKSClient, SSKSUnavailable, normalize_key

SOURCE_COMPONENT = "C01 job-market-intelligence-engine"
EXCLUDED_CATEGORIES = {"Qualification"}
# Suggested SSKS skill type / nature; the reviewer can change them when approving.
LEXICON_TYPES = {
    "Technical": ("OTHER_SKILL", "TECHNICAL"),
    "Tool": ("SOFTWARE_OR_TOOL", "TECHNICAL"),
    "Domain knowledge": ("KNOWLEDGE", "OTHER"),
    "Soft skill": ("OTHER_SKILL", "BEHAVIOURAL"),
    "Language": ("KNOWLEDGE", "OTHER"),
}
NER_TYPES = {"KNOWLEDGE": ("KNOWLEDGE", None), "SKILL": ("OTHER_SKILL", None)}

TO_SUBMIT, FUZZY, SUBMITTED = "to submit", "fuzzy match: review by hand, not sent", "already submitted"


@dataclass
class Candidate:
    name: str
    source: str  # lexicon | ner
    ads: list[str]  # "site:job_id"
    skill_type: str | None
    skill_nature: str | None
    status: str = TO_SUBMIT

    def payload(self) -> dict:
        return {
            "entity_type": "SKILL",
            "submitted_name": self.name,
            "description": None,
            "proposed_skill_type": self.skill_type,
            "proposed_skill_nature": self.skill_nature,
            "source_component": SOURCE_COMPONENT,
            "source_reference": f"{len(self.ads)} job ads, e.g. {self.ads[0]}",
        }


def find_candidates(rows: list[dict], min_ads: int, submitted: dict[str, dict]) -> list[Candidate]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if row["extractor"] == "lexicon":
            if row["label"] in EXCLUDED_CATEGORIES or row.get("lexicon_ssk_ids"):
                continue
            if row.get("lexicon_name_match_type") in ("unmatched", "fuzzy"):
                groups[("lexicon", row["lexicon_skill"])].append(row)
        elif row["match_type"] in ("unmatched", "fuzzy"):
            groups[("ner", normalize_key(row["text"]))].append(row)

    candidates = []
    for (source, key), group in groups.items():
        ads = sorted({f"{r['site']}:{r['job_id']}" for r in group})
        if len(ads) < min_ads:
            continue
        if source == "lexicon":
            name, match_type = key, group[0]["lexicon_name_match_type"]
            skill_type, nature = LEXICON_TYPES.get(group[0]["label"], ("OTHER_SKILL", None))
        else:
            name = Counter(r["text"] for r in group).most_common(1)[0][0]
            match_type = "fuzzy" if any(r["match_type"] == "fuzzy" for r in group) else "unmatched"
            skill_type, nature = NER_TYPES.get(Counter(r["label"] for r in group).most_common(1)[0][0], (None, None))
        status = SUBMITTED if normalize_key(name) in submitted else FUZZY if match_type == "fuzzy" else TO_SUBMIT
        candidates.append(Candidate(name, source, ads, skill_type, nature, status))
    return sorted(candidates, key=lambda c: (c.status != TO_SUBMIT, -len(c.ads), c.name.lower()))


def write_csv(path: Path, candidates: list[Candidate]) -> None:
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["name", "source", "ads", "example_ads", "proposed_skill_type", "proposed_skill_nature", "status"])
        for c in candidates:
            writer.writerow([c.name, c.source, len(c.ads), "; ".join(c.ads[:3]), c.skill_type, c.skill_nature, c.status])


def submit(client: SSKSClient, candidates: list[Candidate], submitted: dict[str, dict]) -> Counter:
    results: Counter = Counter()
    for c in candidates:
        if c.status != TO_SUBMIT:
            continue
        outcome = client.submit_candidate(c.payload())  # raises SSKSUnavailable if SSKS is down
        submitted[normalize_key(c.name)] = {"name": c.name, "result": outcome, "at": utc_now()}
        results[outcome] += 1
    return results


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Propose unknown skills to the Shared Skill Knowledge Service.")
    parser.add_argument("--min-ads", type=int, default=2, help="seen in at least this many ads (default: 2)")
    parser.add_argument("--submit", action="store_true", help="send them (default: dry run)")
    args = parser.parse_args(argv)

    settings = load_settings()
    processed = Storage(settings.data_dir).processed_dir
    rows_path = processed / "ad_skills.jsonl"
    if not rows_path.is_file():
        print(f"error: {rows_path} not found; build the skill profile with SKILLBRIDGE_SSKS_URL set first",
              file=sys.stderr)
        return 2
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    submitted_path = processed / "ssks_candidates_submitted.json"
    submitted = json.loads(submitted_path.read_text(encoding="utf-8")) if submitted_path.is_file() else {}

    candidates = find_candidates(rows, args.min_ads, submitted)
    write_csv(processed / "ssks_candidates.csv", candidates)
    counts = Counter(c.status for c in candidates)
    for c in candidates:
        print(f"  [{c.status}] {c.name} ({c.source}, {len(c.ads)} ads)")
    print(f"{counts[TO_SUBMIT]} to submit, {counts[FUZZY]} fuzzy (not sent), {counts[SUBMITTED]} already submitted; "
          f"list in {processed / 'ssks_candidates.csv'}")
    if not args.submit:
        print("Dry run: nothing was sent. Run with --submit once the SSKS owner agrees.")
        return 0
    if not settings.ssks_url:
        print("error: set SKILLBRIDGE_SSKS_URL to submit", file=sys.stderr)
        return 2
    try:
        results = submit(SSKSClient(settings.ssks_url), candidates, submitted)
    except SSKSUnavailable as exc:
        print(f"error: SSKS not reachable ({exc}); nothing more was sent", file=sys.stderr)
        return 1
    finally:
        submitted_path.write_text(json.dumps(submitted, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"submitted: {results['created']} created, {results['exists']} already known to SSKS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
