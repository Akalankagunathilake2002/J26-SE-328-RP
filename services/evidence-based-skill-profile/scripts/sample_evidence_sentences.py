"""Pick CV sentences for hand-labelling the evidence type (TAF tasks 6 and 10).

Runs dictionary extraction on every CV, keeps each distinct sentence that contains a skill, and
draws a sample balanced over (CV section, rule-based evidence type), so hard cases such as
Experience sentences without an action verb are included. Writes a CSV with an empty `label`
column to fill in by hand (the rule's answer is shown in `rule_label` only for reference).

    python -m scripts.sample_evidence_sentences data/cvs --per-group 12 --out data/evaluation/evidence_sentences.csv
"""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from app.extraction.pipeline import extract_from_document
from app.extraction.reader import SUPPORTED_EXTENSIONS, DocumentError

MIN_WORDS, MAX_WORDS = 3, 60
FIELDS = ["id", "cv", "section", "skills", "sentence", "rule_label", "label", "note"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--per-group", type=int, default=12,
                        help="sentences per (section, rule label) group")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    seen: set[str] = set()
    paths = sorted(p for p in args.path.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    for path in paths:
        try:
            result = extract_from_document(path.read_bytes(), path.name, neural=None,
                                           normaliser=None)
        except DocumentError:
            continue
        by_sentence: dict[tuple[str, str], list] = defaultdict(list)
        for mention in result.mentions:
            by_sentence[(mention.section, mention.sentence)].append(mention)
        for (section, sentence), mentions in by_sentence.items():
            key = sentence.lower()
            if key in seen or not MIN_WORDS <= len(sentence.split()) <= MAX_WORDS:
                continue
            seen.add(key)
            groups[(section, mentions[0].evidence_type)].append({
                "cv": path.name, "section": section, "sentence": sentence,
                "skills": "; ".join(dict.fromkeys(m.name for m in mentions)),
                "rule_label": mentions[0].evidence_type,
            })

    rng = random.Random(args.seed)
    rows = []
    for key in sorted(groups):
        rows += rng.sample(groups[key], min(args.per_group, len(groups[key])))
    rng.shuffle(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for number, row in enumerate(rows, 1):
            writer.writerow({"id": number, **row, "label": "", "note": ""})
    print(f"{len(rows)} sentences from {len(paths)} CVs -> {args.out}")
    for (section, label), found in sorted(groups.items()):
        print(f"  {section:<16} {label:<22} {len(found):>5} available")


if __name__ == "__main__":
    main()
