"""Run skill extraction on one document or a folder of documents.

    python -m scripts.extract_cv data/cvs/HR/10399912.pdf            one CV, skill table
    python -m scripts.extract_cv data/cvs/HR/10399912.pdf --json     one CV, full JSON
    python -m scripts.extract_cv data/cvs --summary                  every CV, totals and top skills
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

from app.extraction.pipeline import extract_from_document
from app.extraction.reader import SUPPORTED_EXTENSIONS, DocumentError
from app.schemas.evidence import SourceType


def _documents(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS)


def _print_document(path: Path, source: SourceType) -> None:
    result = extract_from_document(path.read_bytes(), path.name, source)
    print(f"{path.name}: sections {', '.join(result.sections)}; {len(result.skills)} skills")
    for skill in sorted(result.skills, key=lambda s: -s.mention_count):
        types = ", ".join(skill.evidence_types)
        print(f"  {skill.skill_id:<11} {skill.name[:40]:<40} x{skill.mention_count:<3} {types}")


def _print_summary(paths: list[Path], source: SourceType, top: int) -> None:
    skill_documents: Counter[str] = Counter()
    evidence: Counter[str] = Counter()
    names: dict[str, str] = {}
    skill_counts, no_sections, failed = [], 0, 0
    for path in paths:
        try:
            result = extract_from_document(path.read_bytes(), path.name, source)
        except DocumentError as error:
            failed += 1
            print(f"  skipped: {error}", file=sys.stderr)
            continue
        skill_counts.append(len(result.skills))
        no_sections += set(result.sections) <= {"header"}
        evidence.update(m.evidence_type for m in result.mentions)
        for skill in result.skills:
            skill_documents[skill.skill_id] += 1
            names[skill.skill_id] = skill.name
    read = len(skill_counts)
    print(f"Documents read: {read} (failed {failed}, no section headings found {no_sections})")
    if read:
        print(f"Skills per document: mean {sum(skill_counts) / read:.1f}, "
              f"min {min(skill_counts)}, max {max(skill_counts)}")
    print("Mentions by evidence type:")
    for evidence_type, count in evidence.most_common():
        print(f"  {evidence_type:<22} {count}")
    print(f"Top {top} skills (documents containing them):")
    for skill_id, count in skill_documents.most_common(top):
        print(f"  {count:>4}  {skill_id:<11} {names[skill_id]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--source", default=SourceType.CV, type=SourceType,
                        choices=list(SourceType))
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    parser.add_argument("--summary", action="store_true", help="totals over all documents")
    parser.add_argument("--top", type=int, default=40)
    args = parser.parse_args()

    paths = _documents(args.path)
    if not paths:
        parser.error(f"no PDF, DOCX or TXT files in {args.path}")
    if args.summary:
        _print_summary(paths, args.source, args.top)
    elif args.json:
        for path in paths:
            print(extract_from_document(path.read_bytes(), path.name, args.source)
                  .model_dump_json(indent=2))
    else:
        for path in paths:
            _print_document(path, args.source)


if __name__ == "__main__":
    main()
