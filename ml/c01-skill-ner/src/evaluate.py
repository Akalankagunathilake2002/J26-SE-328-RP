"""Step 5: evaluate the lexicon and the NER models → reports/evaluation.md (+ evaluation.json).

    .venv/bin/python src/evaluate.py [--ssks-url http://localhost:8005/ssks]

1. SkillSpan test split: every model in models/ (SKILL and KNOWLEDGE merged into one label), and
   the lexicon for reference. Checks that training worked.
2. topjobs test set (needs data/topjobs_test/labelled.json, exported from Label Studio): lexicon vs
   each model. This is the main result.
3. Correct skills only NER found, typical errors, and (with --ssks-url) how many of the extracted
   skills SSKS matches exactly / by alias / only fuzzily / not at all.

All methods are scored on character spans, after trimming punctuation and bullets the same way
the service does: "exact" needs the same start and end, "partial" any overlap. 95% confidence
intervals come from 1,000 bootstrap resamples of the documents (seed 42). Whatever can't be
measured (no labels, no SSKS) is reported as not measured.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet  # noqa: F401  (datasets needs it; imported early for a clear error)
from datasets import load_dataset

from app.integrations.ssks import SSKSClient
from app.processing.ner_extractor import NerExtractor, clean_mention, load_ner
from app.processing.skills import SkillLexicon

from common import DATA, MODELS, REPORTS, SEED, bio_to_spans, write_json
from export_label_studio import text_fingerprint

ALL_SECTORS = ["IT", "HR", "Management", "Agriculture"]
EXCLUDED_LEXICON_CATEGORIES = {"Qualification"}  # not skills in the labelling guide
BOOTSTRAP = 1000
CharSpan = tuple[int, int]


@dataclass
class Document:
    id: str
    text: str
    gold: list[CharSpan]
    sectors: list[str]


# --- data -------------------------------------------------------------------------------------------


def skillspan_test() -> tuple[list[Document], set[str]]:
    """SkillSpan test sentences as text with gold character spans (both labels, merged), and the
    IDs of test sentences that also appear, word for word, in the training split."""
    data = load_dataset("jjzha/skillspan")
    train_sentences = {tuple(row["tokens"]) for row in data["train"]}
    docs, duplicates = [], set()
    for i, row in enumerate(data["test"]):
        tokens = list(row["tokens"])
        if tuple(tokens) in train_sentences:
            duplicates.add(f"skillspan-test-{i}")
        starts, pos = [], 0
        for token in tokens:
            starts.append(pos)
            pos += len(token) + 1
        text = " ".join(tokens)
        spans = bio_to_spans(row["tags_skill"], "SKILL") + bio_to_spans(row["tags_knowledge"], "KNOWLEDGE")
        gold = {_trim(text, starts[s.start], starts[s.end - 1] + len(tokens[s.end - 1])) for s in spans}
        docs.append(Document(f"skillspan-test-{i}", text, sorted(g for g in gold if g), ALL_SECTORS))
    return docs, duplicates


def topjobs_test() -> list[Document] | None:
    """The hand-labelled topjobs ads (Label Studio JSON export), checked against selection.json."""
    labelled = DATA / "topjobs_test" / "labelled.json"
    if not labelled.is_file():
        return None
    selection = json.loads((DATA / "topjobs_test" / "selection.json").read_text())
    fingerprints = {a["ad"]: a["text_sha256"] for a in selection["ads"]}
    docs = []
    for task in json.loads(labelled.read_text()):
        data = task["data"]
        if text_fingerprint(data["text"]) != fingerprints.get(data["ad"]):
            raise ValueError(f"{data['ad']}: the labelled text differs from the exported one")
        annotations = [a for a in task.get("annotations", []) if not a.get("was_cancelled")]
        if not annotations:
            continue  # not labelled yet
        result = annotations[-1]["result"]
        gold = {_trim(data["text"], r["value"]["start"], r["value"]["end"]) for r in result if r.get("type") == "labels"}
        docs.append(Document(data["ad"], data["text"], sorted(g for g in gold if g), data["sectors"].split(", ")))
    return docs


def _trim(text: str, start: int, end: int) -> CharSpan | None:
    mention = clean_mention(text, start, end, "SKILL")
    return (mention.start, mention.end) if mention else None


# --- predictions ------------------------------------------------------------------------------------


def lexicon_predict(lexicon: SkillLexicon, doc: Document) -> list[CharSpan]:
    spans = {
        _trim(doc.text, m.start, m.end)
        for m in lexicon.find_mentions(doc.text, doc.sectors)
        if m.skill.category not in EXCLUDED_LEXICON_CATEGORIES
    }
    return sorted(s for s in spans if s)


def ner_predict(model: NerExtractor, doc: Document) -> list[CharSpan]:
    return sorted({(m.start, m.end) for m in model.extract(doc.text)})


def available_models() -> dict[str, Path]:
    models = {}
    for folder in sorted(MODELS.glob("spacy-skill-ner-*/model-best")):
        models[f"spaCy NER {folder.parent.name.removeprefix('spacy-skill-ner-')}"] = folder
    for folder in sorted(MODELS.glob("jobbert-skill-ner-*")):
        if (folder / "config.json").is_file():
            models[f"JobBERT NER {folder.name.removeprefix('jobbert-skill-ner-')}"] = folder
    return models


# --- metrics ----------------------------------------------------------------------------------------


def counts(pred: list[CharSpan], gold: list[CharSpan]) -> dict:
    overlaps = lambda a, b: a[0] < b[1] and b[0] < a[1]  # noqa: E731
    return {
        "pred": len(pred), "gold": len(gold),
        "exact": len(set(pred) & set(gold)),
        "partial_pred": sum(any(overlaps(p, g) for g in gold) for p in pred),
        "partial_gold": sum(any(overlaps(g, p) for p in pred) for g in gold),
    }


def scores(per_doc: list[dict]) -> dict:
    total = Counter()
    for c in per_doc:
        total.update(c)
    return {
        "exact": _prf(total["exact"], total["pred"], total["exact"], total["gold"]),
        "partial": _prf(total["partial_pred"], total["pred"], total["partial_gold"], total["gold"]),
        "predicted": total["pred"], "gold": total["gold"],
    }


def _prf(tp_p: int, n_pred: int, tp_r: int, n_gold: int) -> dict:
    p = tp_p / n_pred if n_pred else 0.0
    r = tp_r / n_gold if n_gold else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}


def bootstrap_f1(per_doc: list[dict]) -> dict:
    rng = random.Random(SEED)
    samples = {"exact": [], "partial": []}
    for _ in range(BOOTSTRAP):
        sample = [per_doc[rng.randrange(len(per_doc))] for _ in per_doc]
        s = scores(sample)
        for kind in samples:
            samples[kind].append(s[kind]["f1"])
    return {kind: (sorted(v)[int(0.025 * BOOTSTRAP)], sorted(v)[int(0.975 * BOOTSTRAP) - 1]) for kind, v in samples.items()}


def evaluate(docs: list[Document], predictions: dict[str, dict[str, list[CharSpan]]]) -> dict:
    results = {}
    for method, by_doc in predictions.items():
        per_doc = [counts(by_doc[d.id], d.gold) for d in docs]
        results[method] = {**scores(per_doc), "f1_95ci": bootstrap_f1(per_doc)}
    return results


# --- error analysis ---------------------------------------------------------------------------------

OCR_NOISE = re.compile(r"[^\x00-\x7F]|[A-Za-z]\d|\d[A-Za-z]|[|~^`{}\\]|\b[bcdfghjklmnpqrstvwxz]{4,}\b", re.I)


def error_kind(text: str, span: CharSpan, other: list[CharSpan]) -> str:
    phrase = text[span[0]:span[1]]
    if any(span[0] < o[1] and o[0] < span[1] for o in other):
        return "boundary (overlaps, but not the same span)"
    if OCR_NOISE.search(phrase):
        return "OCR noise"
    if len(phrase.split()) > 4:
        return "long phrase (5+ words)"
    return "other"


def error_analysis(docs: list[Document], by_doc: dict[str, list[CharSpan]], limit: int = 5) -> dict:
    kinds = {"false positive": Counter(), "missed": Counter()}
    examples = {"false positive": {}, "missed": {}}
    for d in docs:
        pred, gold = set(by_doc[d.id]), set(d.gold)
        for name, spans, other in (("false positive", pred - gold, d.gold), ("missed", gold - pred, by_doc[d.id])):
            for span in spans:
                kind = error_kind(d.text, span, other)
                kinds[name][kind] += 1
                examples[name].setdefault(kind, [])
                if len(examples[name][kind]) < limit:
                    examples[name][kind].append(d.text[span[0]:span[1]])
    return {"counts": {k: dict(v) for k, v in kinds.items()}, "examples": examples}


def ner_only_correct(docs: list[Document], ner: dict[str, list[CharSpan]], lexicon: dict[str, list[CharSpan]]) -> dict:
    """Gold skills a model found (partial overlap) that the lexicon missed."""
    found = []
    for d in docs:
        overlaps = lambda g, preds: any(g[0] < p[1] and p[0] < g[1] for p in preds)  # noqa: E731
        found += [d.text[g[0]:g[1]] for g in d.gold if overlaps(g, ner[d.id]) and not overlaps(g, lexicon[d.id])]
    return {"count": len(found), "examples": [t for t, _ in Counter(found).most_common(15)]}


def ssks_match_types(client: SSKSClient, docs: list[Document], by_doc: dict[str, list[CharSpan]]) -> dict | None:
    """Match types of the extracted mentions; None (not measured) if SSKS didn't answer for all."""
    mentions = [d.text[s[0]:s[1]] for d in docs for s in by_doc[d.id]]
    matches = client.lookup(mentions)
    types = Counter(matches[m].match_type for m in mentions if m in matches)
    if types["pending"]:
        return None
    return {"mentions": sum(types.values()), **{t: types[t] for t in ("exact", "alias", "fuzzy", "unmatched")}}


def ssks_snapshot(url: str) -> dict | None:
    """The SSKS data the results depend on (its own snapshot metadata)."""
    import requests

    try:
        meta = requests.get(f"{url.rstrip('/')}/snapshots/metadata", timeout=30).json()
    except (requests.RequestException, ValueError):
        return None
    return {"version": meta.get("version"), "counts": meta.get("counts")}


def lexicon_ssks_coverage(client: SSKSClient, lexicon: SkillLexicon) -> dict | None:
    """How many lexicon skills get an SSKS ID through their name or a verified alias; None if SSKS
    didn't answer for every name."""
    names = [n for skill in lexicon.skills for n in (skill.name, *skill.aliases)]
    matches = client.lookup(names)
    if any(m.match_type == "pending" for m in matches.values()):
        return None
    linked = [s.name for s in lexicon.skills if any(matches[n].counted for n in (s.name, *s.aliases) if n in matches)]
    return {"skills": len(lexicon.skills), "linked": len(linked)}


# --- report -----------------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ssks-url", help="a running SSKS, e.g. http://localhost:8005/ssks")
    args = parser.parse_args()

    lexicon = SkillLexicon.load()
    models = {name: load_ner(path) for name, path in available_models().items()}
    metadata = {name: json.loads(((path.parent if path.name == "model-best" else path) / "metadata.json").read_text())
                for name, path in available_models().items()}
    ssks = SSKSClient(args.ssks_url, cache_path=DATA / "ssks_cache.json") if args.ssks_url else None
    report = {"generated_at": datetime.now(UTC).isoformat(timespec="seconds"), "models": metadata,
              "ssks_url": args.ssks_url, "ssks_snapshot": ssks_snapshot(args.ssks_url) if args.ssks_url else None}

    docs, duplicates = skillspan_test()
    preds = {"Lexicon (baseline)": {d.id: lexicon_predict(lexicon, d) for d in docs}}
    preds.update({name: {d.id: ner_predict(model, d) for d in docs} for name, model in models.items()})
    unseen = [d for d in docs if d.id not in duplicates]
    report["skillspan"] = {
        "documents": len(docs),
        "gold_spans": sum(len(d.gold) for d in docs),
        "test_sentences_also_in_train": len(duplicates),
        "gold_spans_in_those": sum(len(d.gold) for d in docs if d.id in duplicates),
        "results": evaluate(docs, preds),
        "results_unseen": evaluate(unseen, preds),  # without the test sentences that are also in train
        "unseen_documents": len(unseen),
        "unseen_gold_spans": sum(len(d.gold) for d in unseen),
    }
    if ssks:
        report["skillspan"]["ssks"] = {m: ssks_match_types(ssks, docs, p) for m, p in preds.items()}
        report["lexicon_ssks_coverage"] = lexicon_ssks_coverage(ssks, lexicon)

    topjobs = topjobs_test()
    if topjobs:
        tj_preds = {"Lexicon (baseline)": {d.id: lexicon_predict(lexicon, d) for d in topjobs}}
        tj_preds.update({name: {d.id: ner_predict(model, d) for d in topjobs} for name, model in models.items()})
        report["topjobs"] = {
            "documents": len(topjobs),
            "gold_spans": sum(len(d.gold) for d in topjobs),
            "results": evaluate(topjobs, tj_preds),
            "ner_only_correct": {m: ner_only_correct(topjobs, p, tj_preds["Lexicon (baseline)"])
                                 for m, p in tj_preds.items() if m != "Lexicon (baseline)"},
            "errors": {m: error_analysis(topjobs, p) for m, p in tj_preds.items()},
        }
        if ssks:
            report["topjobs"]["ssks"] = {m: ssks_match_types(ssks, topjobs, p) for m, p in tj_preds.items()}

    write_json(REPORTS / "evaluation.json", report)
    (REPORTS / "evaluation.md").write_text(render(report), encoding="utf-8")
    print(f"wrote {REPORTS / 'evaluation.md'}")
    return 0


def render(r: dict) -> str:
    lines = [
        "# C01 skill extraction: evaluation",
        "",
        f"Generated {r['generated_at']} by `src/evaluate.py`. All numbers are measured; nothing is estimated.",
        "",
        "Scoring: character spans after trimming punctuation and bullets. **Exact** = same start and end; "
        "**partial** = any overlap (precision counts predicted spans that overlap a gold span, recall counts "
        "gold spans that overlap a prediction). SKILL and KNOWLEDGE are merged into one label. "
        f"F1 95% CI: {BOOTSTRAP} bootstrap resamples of the documents (seed {SEED}).",
        "",
        "## Models",
        "",
        "| Model | Trained | Minutes | Device | Validation (SkillSpan) |",
        "|---|---|--:|---|---|",
    ]
    for name, m in r["models"].items():
        val = m["best_validation_scores"]
        f1 = val.get("ents_f", val.get("eval_f1"))
        lines.append(f"| {name} | {m['trained_at']} | {m['training_minutes']} | {m.get('device', 'cpu')} "
                     f"| exact span F1 {f1:.3f} (two labels) |")
    if not r["models"]:
        lines.append("| – | no trained model found in models/ | | | |")

    s = r["skillspan"]
    lines += ["", "## 1. SkillSpan test split (checks that training worked)", "",
              f"{s['documents']} sentences, {s['gold_spans']} gold spans.", "",
              *_results_table(s["results"]), "",
              f"{s['test_sentences_also_in_train']} test sentences also appear word for word in the training "
              f"split ({s['gold_spans_in_those']} of the gold spans are in them). Without those sentences "
              f"({s['unseen_documents']} sentences, {s['unseen_gold_spans']} gold spans):", "",
              *_results_table(s["results_unseen"]), "",
              "The lexicon was not built for these (mostly international tech) postings; it is shown for reference."]

    lines += ["", "## 2. topjobs test set: lexicon vs NER (main result)", ""]
    t = r.get("topjobs")
    if not t:
        lines.append("**Not measured yet:** waiting for the hand-labelled test set "
                     "(`data/topjobs_test/labelled.json`; see LABELLING.md).")
    else:
        lines += [f"{t['documents']} ads, {t['gold_spans']} gold spans.", "", *_results_table(t["results"]), "",
                  "### 3. Correct skills found by NER but missed by the lexicon", ""]
        for m, v in t["ner_only_correct"].items():
            lines.append(f"- **{m}:** {v['count']} gold spans. Examples: " + "; ".join(f"`{e}`" for e in v["examples"]))
        lines += ["", "### 4. Typical errors", "",
                  "Error kinds are assigned by simple rules (overlap with another span, OCR-like characters, "
                  "phrase length), so they are indicative.", ""]
        for m, v in t["errors"].items():
            lines.append(f"**{m}**")
            for side in ("false positive", "missed"):
                for kind, n in sorted(v["counts"][side].items(), key=lambda x: -x[1]):
                    ex = "; ".join(f"`{e}`" for e in v["examples"][side][kind])
                    lines.append(f"- {side}, {kind}: {n} (e.g. {ex})")
            lines.append("")

    lines += ["", "## 5. SSKS match of extracted skills", ""]
    coverage = r.get("lexicon_ssks_coverage")
    if not r.get("ssks_url"):
        lines.append("**Not measured:** run with `--ssks-url` and a running SSKS.")
    else:
        snap = r.get("ssks_snapshot") or {}
        counts = snap.get("counts") or {}
        lines.append(f"SSKS: {r['ssks_url']}, snapshot {snap.get('version', 'unknown')} "
                     f"({counts.get('skills', '?')} skills, {counts.get('aliases', '?')} verified skill aliases, "
                     f"{counts.get('domains', '?')} domains). Only exact and verified-alias matches count.")
        if coverage is None:
            lines.append("Lexicon coverage: **not measured** (SSKS did not answer for every name).")
        else:
            lines.append(f"Lexicon coverage: {coverage['linked']} of {coverage['skills']} lexicon skills "
                         f"({coverage['linked'] / coverage['skills']:.0%}) have an SSKS ID through their name or a "
                         "verified alias.")
        for part, title in (("skillspan", "SkillSpan test"), ("topjobs", "topjobs test")):
            data = (r.get(part) or {}).get("ssks")
            if not data:
                continue
            lines += ["", f"Extracted mentions on the {title} set:", "",
                      "| Method | Mentions | Exact | Alias | Fuzzy only | Unmatched |",
                      "|---|--:|--:|--:|--:|--:|"]
            for m, c in data.items():
                if c is None:
                    lines.append(f"| {m} | not measured (SSKS did not answer for every mention) | | | | |")
                    continue
                n = c["mentions"] or 1
                lines.append(f"| {m} | {c['mentions']} | " + " | ".join(
                    f"{c[k] / n:.0%}" for k in ("exact", "alias", "fuzzy", "unmatched")) + " |")
    lines.append("")
    return "\n".join(lines)


def _results_table(results: dict) -> list[str]:
    rows = ["| Method | Predicted | Exact P | Exact R | Exact F1 (95% CI) | Partial P | Partial R | Partial F1 (95% CI) |",
            "|---|--:|--:|--:|--:|--:|--:|--:|"]
    for m, v in results.items():
        e, p, ci = v["exact"], v["partial"], v["f1_95ci"]
        rows.append(f"| {m} | {v['predicted']} | {e['precision']:.3f} | {e['recall']:.3f} | "
                    f"{e['f1']:.3f} ({ci['exact'][0]:.3f}–{ci['exact'][1]:.3f}) | {p['precision']:.3f} | "
                    f"{p['recall']:.3f} | {p['f1']:.3f} ({ci['partial'][0]:.3f}–{ci['partial'][1]:.3f}) |")
    return rows


if __name__ == "__main__":
    sys.exit(main())
