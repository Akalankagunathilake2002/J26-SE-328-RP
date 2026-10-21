"""Map written skill terms to standard skill IDs (demo of the normalisation engine).

    python -m scripts.normalise_terms "Javascrpit" "Python3" "made neural networks"
"""
import argparse

from app.normalisation.normaliser import get_normaliser


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("terms", nargs="+")
    args = parser.parse_args()

    for result in get_normaliser().normalise(args.terms):
        found = f"{result.skill_id} {result.name}" if result.skill_id else "-"
        print(f"{result.term[:40]:<40} {result.method:<15} {result.score:.2f}  {found}")


if __name__ == "__main__":
    main()
