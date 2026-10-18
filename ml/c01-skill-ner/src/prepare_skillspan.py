"""Step 1: SkillSpan → training files for spaCy and JobBERT.

    .venv/bin/python src/prepare_skillspan.py

SkillSpan (Zhang et al., NAACL 2022; CC-BY-4.0) is loaded with ``load_dataset("jjzha/skillspan")``.
Its train split is used for training, validation for model selection, test only for evaluation.

Writes to data/skillspan/:
  {train,validation,test}.spacy   spaCy DocBin files with SKILL and KNOWLEDGE entities
  {train,validation,test}.jsonl   tokens + BIO tags, for JobBERT
  stats.json                      span counts and lengths per split
"""

from __future__ import annotations

import json
from collections import Counter

import spacy
from datasets import load_dataset
from spacy.tokens import Doc, DocBin, Span

from common import DATA, LABELS, skillspan_spans, spans_to_bio, write_json

OUT = DATA / "skillspan"
DATASET = "jjzha/skillspan"


def main() -> None:
    dataset = load_dataset(DATASET)
    nlp = spacy.blank("en")
    OUT.mkdir(parents=True, exist_ok=True)
    stats = {"dataset": DATASET, "dataset_fingerprints": {}, "splits": {}}

    for split in ("train", "validation", "test"):
        rows = dataset[split]
        stats["dataset_fingerprints"][split] = rows._fingerprint
        doc_bin = DocBin(store_user_data=False)
        counts, lengths, dropped = Counter(), Counter(), 0
        with (OUT / f"{split}.jsonl").open("w", encoding="utf-8") as jsonl:
            for row in rows:
                tokens = list(row["tokens"])
                spans, n_dropped = skillspan_spans(row)
                dropped += n_dropped
                doc = Doc(nlp.vocab, words=tokens, spaces=[True] * (len(tokens) - 1) + [False])
                doc.ents = [Span(doc, s.start, s.end, label=s.label) for s in spans]
                doc_bin.add(doc)
                jsonl.write(json.dumps({"tokens": tokens, "ner_tags": spans_to_bio(len(tokens), spans)}) + "\n")
                for s in spans:
                    counts[s.label] += 1
                    lengths[s.label] += s.end - s.start
        doc_bin.to_disk(OUT / f"{split}.spacy")
        stats["splits"][split] = {
            "sentences": len(rows),
            "spans": {label: counts[label] for label in LABELS},
            "mean_tokens": {label: round(lengths[label] / counts[label], 2) for label in LABELS if counts[label]},
            "skill_spans_dropped_for_overlap": dropped,
        }
        print(split, stats["splits"][split])

    write_json(OUT / "stats.json", stats)


if __name__ == "__main__":
    main()
