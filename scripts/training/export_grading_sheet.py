"""Human grading for non-technical interview answers (HR, marketing, finance, design, writing roles).

The technical scorer was calibrated against human grades (Mohler dataset, compare_scoring_methods.py), but
there is no public set of graded answers for behavioural / competency questions, so the LLM's grades for
those roles are unvalidated. This collects the data to validate them:

  1. export   answered, LLM-graded role questions of non-technical roles -> CSV with empty human columns
  2. (people) two graders fill in human_technical_accuracy (1-5) etc. independently, without looking at the
              LLM columns (hide them in the spreadsheet)
  3. score    agreement between human and LLM grades (Pearson, Spearman, quadratic weighted kappa, MAE),
              and between the two graders when both filled in a column, the ceiling to compare against

export needs the interview service's database settings and packages, so run it from that service:
  cd services/interview-service && python ../../scripts/training/export_grading_sheet.py export --out sheet.csv
  (Docker: docker compose run --rm -v "$PWD/scripts:/scripts" interview-service \\
           python /scripts/training/export_grading_sheet.py export --out /scripts/sheet.csv)
score needs only numpy:
  python scripts/training/export_grading_sheet.py score sheet.csv [sheet_grader2.csv]
"""
import argparse
import asyncio
import csv
import os
import sys

CRITERIA = ("technical_accuracy", "relevance", "explanation_quality", "clarity")
COLUMNS = (["turn_id", "role", "level", "topic", "question", "reference_answer", "answer"]
           + [f"llm_{c}" for c in CRITERIA] + [f"human_{c}" for c in CRITERIA] + ["grader", "notes"])


async def export(out: str, limit: int):
    sys.path.insert(0, os.getcwd())
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.core.roles import is_technical
    from app.models.interview import InterviewSession, InterviewTurn

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(InterviewTurn, InterviewSession)
            .join(InterviewSession, InterviewTurn.session_id == InterviewSession.id)
            .where(InterviewTurn.phase == "core", InterviewTurn.technical_accuracy_score.isnot(None),
                   InterviewTurn.transcript.isnot(None))
            .order_by(InterviewTurn.created_at.desc()).limit(limit * 5)
        )).all()
    picked = [(t, s) for t, s in rows if not is_technical(s.target_role) and len((t.transcript or "").split()) >= 5]
    picked = picked[:limit]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for t, s in picked:
            w.writerow({"turn_id": str(t.id), "role": s.target_role, "level": s.experience_level, "topic": t.topic,
                        "question": t.question, "reference_answer": t.reference_answer or "", "answer": t.transcript,
                        **{f"llm_{c}": float(getattr(t, f"{c}_score")) for c in CRITERIA}})
    # Transcripts are what candidates said: keep the sheet among the graders and delete it afterwards
    print(f"Wrote {len(picked)} answers to {out} (non-technical roles; contains candidate transcripts)")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return {r["turn_id"]: r for r in csv.DictReader(f)}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def score(sheet: str, second: str = None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from metrics import agreement
    a = _read(sheet)
    b = _read(second) if second else {}
    for c in CRITERIA:
        pairs = [(_num(r[f"human_{c}"]), _num(r[f"llm_{c}"])) for r in a.values()]
        pairs = [(h, m) for h, m in pairs if h is not None and m is not None]
        if len(pairs) < 5:
            print(f"{c}: only {len(pairs)} human grades, need at least 5")
            continue
        h, m = zip(*pairs)
        print(f"{c}: human vs LLM {agreement([round(x) for x in h], [round(x) for x in m])}")
        if b:
            both = [(_num(a[k][f"human_{c}"]), _num(b[k][f"human_{c}"])) for k in a if k in b]
            both = [(x, y) for x, y in both if x is not None and y is not None]
            if len(both) >= 5:
                x, y = zip(*both)
                print(f"{c}: grader 1 vs grader 2 {agreement([round(v) for v in x], [round(v) for v in y])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--out", default="grading_sheet.csv")
    e.add_argument("--limit", type=int, default=100)
    s = sub.add_parser("score")
    s.add_argument("sheet")
    s.add_argument("second", nargs="?")
    args = ap.parse_args()
    if args.cmd == "export":
        asyncio.run(export(args.out, args.limit))
    else:
        score(args.sheet, args.second)


if __name__ == "__main__":
    main()
