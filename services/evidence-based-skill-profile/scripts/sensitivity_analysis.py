"""SMAA-style sensitivity analysis of the confidence score (TAF tasks 7 and 10).

Builds profiles from the demo documents (CV only, and CV + project report + certificate) and from
Kaggle resumes, then recomputes every confidence with many random settings that keep the evidence
order. It also tests the two alternative orders for the top tier (certificate above portfolio, and
portfolio above certificate). See app/evidence/sensitivity.py.

    python -m scripts.sensitivity_analysis
    python -m scripts.sensitivity_analysis --cvs data/cvs --sample 40 --draws 1000
"""
import argparse
import random
from pathlib import Path

from app.config.settings import SERVICE_DIR
from app.evidence.fusion import EVIDENCE_RANKING, FusionSettings, kind_strengths
from app.evidence.sensitivity import (
    STABLE_FROM, Profile, SensitivityResult, analyse, compare,
)
from app.extraction.pipeline import extract_from_document
from app.extraction.reader import SUPPORTED_EXTENSIONS, DocumentError
from app.profile.builder import SubmittedDocument, profile_evidence
from app.schemas.evidence import SourceType

SAMPLES = SERVICE_DIR / "data" / "samples"
DEMO = [("sample_cv.txt", SourceType.CV),
        ("sample_project_report.txt", SourceType.PROJECT_DESCRIPTION),
        ("sample_python_certificate.txt", SourceType.CERTIFICATE)]


def _documents(files: list[tuple[Path, SourceType]]) -> list[SubmittedDocument]:
    return [SubmittedDocument(path.name, path.read_bytes(), source) for path, source in files]


def _print(label: str, result: SensitivityResult) -> None:
    print(f"{label:<34} level kept {result.level_stability:6.1%}   "
          f"stable skills {result.stable_skills:6.1%}   "
          f"rank tau {result.rank_stability:5.3f}   mean change {result.mean_change:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cvs", type=Path, default=SERVICE_DIR / "data" / "cvs")
    parser.add_argument("--sample", type=int, default=40, help="Kaggle resumes to include")
    parser.add_argument("--draws", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--neural", action="store_true", help="also use GLiNER (much slower)")
    args = parser.parse_args()

    def extract(data: bytes, name: str, source: SourceType):
        layers = {} if args.neural else {"neural": None, "normaliser": None}
        return extract_from_document(data, name, source, **layers)

    demo = [(SAMPLES / name, source) for name, source in DEMO]
    profiles: list[Profile] = [
        profile_evidence(_documents(demo[:1]), extract),
        profile_evidence(_documents(demo), extract),
    ]
    paths = sorted(p for p in args.cvs.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    for path in random.Random(args.seed).sample(paths, min(args.sample, len(paths))):
        try:
            profiles.append(profile_evidence(_documents([(path, SourceType.CV)]), extract))
        except DocumentError:
            continue

    print(f"{len(profiles)} profiles (2 demo + {len(profiles) - 2} Kaggle resumes), "
          f"{args.draws} draws each; a skill is stable if it keeps its level in "
          f"{STABLE_FROM:.0%} of draws\n")
    result = analyse(profiles, args.draws, args.seed)
    print(f"{result.skills} skills; default levels {result.level_counts}")
    _print("Random weights, same order", result)
    print("  level kept, by default level: " + ", ".join(
        f"{level} {share:.1%} (n={result.level_counts[level]})"
        for level, share in result.by_level.items()))

    certificate, portfolio = EVIDENCE_RANKING[0]
    print("\nAlternative orders for the top tier, compared with the tied default:")
    for label, top in (("certificate > portfolio", [[certificate], [portfolio]]),
                       ("portfolio > certificate", [[portfolio], [certificate]])):
        tiers = top + EVIDENCE_RANKING[1:]
        _print(f"Order: {label}", compare(profiles, FusionSettings(kind_strengths(tiers))))


if __name__ == "__main__":
    main()
