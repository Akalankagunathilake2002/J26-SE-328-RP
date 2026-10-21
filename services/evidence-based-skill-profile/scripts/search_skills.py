"""Find the skills closest in meaning to a phrase (demo of the semantic skill index).

    python -m scripts.search_skills "made neural networks" "handled staff hiring"
    python -m scripts.search_skills --index esco "composing film music"
"""
import argparse

from app.config.settings import get_settings
from app.semantic.encoder import get_encoder
from app.semantic.skill_index import SkillIndex


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("phrases", nargs="+")
    parser.add_argument("--index", default="ssks", choices=["ssks", "esco"])
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()

    settings = get_settings()
    index = SkillIndex.load(settings.index_dir, args.index, settings.embedding_model)
    for phrase, hits in zip(args.phrases, index.search(args.phrases, get_encoder(), args.top)):
        print(f'"{phrase}"')
        for hit in hits:
            print(f"  {hit.score:.3f}  {hit.skill_id[-36:]:<36} {hit.name[:40]:<40} "
                  f"(via {hit.matched_kind})")


if __name__ == "__main__":
    main()
