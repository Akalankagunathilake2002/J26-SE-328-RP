"""Build one student skill profile from several documents (demo of TAF task 2 + 7).

Each file's type is detected from its content, as in the service.

    python -m scripts.build_profile data/samples/sample_cv.txt
    python -m scripts.build_profile data/samples/sample_cv.txt \
        data/samples/sample_project_report.txt data/samples/sample_python_certificate.txt
    python -m scripts.build_profile cv.pdf --github https://github.com/<user>
"""
import argparse
from pathlib import Path

from app.profile.builder import SubmittedDocument, build_profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", type=Path, nargs="*")
    parser.add_argument("--github", action="append", default=[], help="GitHub user/repo link")
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()

    documents = [SubmittedDocument(path.name, path.read_bytes()) for path in args.files]
    if not documents and not args.github:
        parser.error("give at least one document or link, e.g. cv.pdf")
    profile = build_profile(documents, links=args.github)
    for document in profile.documents:
        how = f", detected by {document.type_detected_by}" if document.type_detected_by else ""
        print(f"{document.name} ({document.source_type}{how}): {document.skill_count} skills")
    print(f"\n{'conf':>5} {'level':<9}{'skill':<34}evidence")
    for skill in profile.skills[:args.top]:
        evidence = ", ".join(f"{c.source}/{c.evidence_type} x{c.mentions}" for c in skill.evidence)
        print(f"{skill.confidence:>5.2f} {skill.confidence_level:<9}{skill.name[:33]:<34}{evidence}")


if __name__ == "__main__":
    main()
