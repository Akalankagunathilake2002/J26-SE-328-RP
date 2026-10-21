"""Compare dictionary-only extraction with the hybrid (dictionary + GLiNER) on real CVs (task 4).

Shows what the GLiNER layer adds: skills per CV, how its phrases were mapped to skill IDs, the
skills it adds most often, the phrases it found that have no skill ID (new-skill candidates),
and the time per CV. It does not say which added skills are correct; that needs hand-labelled
CVs (task 10). Use --examples to read added skills in context and judge them.

    python -m scripts.compare_extraction data/cvs --sample 40
    python -m scripts.compare_extraction data/cvs/INFORMATION-TECHNOLOGY --sample 10 --examples 15
"""
import argparse
import random
import time
from collections import Counter
from pathlib import Path

from app.extraction.neural import get_span_extractor
from app.extraction.pipeline import extract_from_document
from app.extraction.reader import SUPPORTED_EXTENSIONS, DocumentError
from app.normalisation.normaliser import get_normaliser


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--sample", type=int, default=40, help="CVs to use (0 = all)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--examples", type=int, default=0, help="added skills to show in context")
    args = parser.parse_args()

    paths = sorted(p for p in args.path.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    if args.sample and args.sample < len(paths):
        paths = sorted(random.Random(args.seed).sample(paths, args.sample))
    neural, normaliser = get_span_extractor(), get_normaliser()

    dictionary_counts, hybrid_counts = [], []
    methods: Counter[str] = Counter()
    added: Counter[str] = Counter()
    unlinked: Counter[str] = Counter()
    examples = []
    dictionary_time = hybrid_time = 0.0
    for path in paths:
        data = path.read_bytes()
        try:
            started = time.perf_counter()
            plain = extract_from_document(data, path.name, neural=None, normaliser=None)
            dictionary_time += time.perf_counter() - started
            started = time.perf_counter()
            hybrid = extract_from_document(data, path.name, neural=neural, normaliser=normaliser)
            hybrid_time += time.perf_counter() - started
        except DocumentError as error:
            print(f"  skipped {path.name}: {error}")
            continue
        dictionary_counts.append(len(plain.skills))
        hybrid_counts.append(len(hybrid.skills))
        known = {s.skill_id for s in plain.skills}
        for mention in hybrid.mentions:
            if mention.method == "gliner":
                methods[mention.match_method] += 1
                if mention.skill_id not in known:
                    added[mention.name] += 1
                    examples.append((path.name, mention))
        unlinked.update(u.text.lower() for u in hybrid.unlinked)

    n = len(dictionary_counts)
    if not n:
        parser.error("no readable CVs")
    print(f"CVs: {n}")
    print(f"Skills per CV   dictionary {sum(dictionary_counts) / n:.1f}   "
          f"hybrid {sum(hybrid_counts) / n:.1f}   "
          f"(+{(sum(hybrid_counts) - sum(dictionary_counts)) / n:.1f})")
    print(f"Seconds per CV  dictionary {dictionary_time / n:.2f}   hybrid {hybrid_time / n:.2f}")
    print("GLiNER mentions by mapping method: "
          + ", ".join(f"{method} {count}" for method, count in methods.most_common()))
    print(f"\nTop {args.top} skills added by GLiNER (CV mentions):")
    for name, count in added.most_common(args.top):
        print(f"  {count:>4}  {name}")
    print(f"\nTop {args.top} phrases with no skill ID (new-skill candidates):")
    for text, count in unlinked.most_common(args.top):
        print(f"  {count:>4}  {text}")
    if args.examples:
        print(f"\n{args.examples} added skills in context (random):")
        for cv, mention in random.Random(args.seed).sample(examples,
                                                           min(args.examples, len(examples))):
            print(f"  [{mention.match_method}, {mention.match_score:.2f}] "
                  f"{mention.matched_text!r} -> {mention.name}\n      {cv}: "
                  f"{mention.sentence[:110]}")


if __name__ == "__main__":
    main()
