"""Export C02's skill-list fixes as a handover for the SSKS owner.

Compares C02's hand-written dictionary files with the SSKS seed and writes, to
data/ssks_handover/:

    new_skill_candidates.csv  skills SSKS lacks, in the SSKS candidate format
    alias_additions.csv       aliases to add to an existing SSKS skill
    alias_removals.csv        aliases that point to the wrong skill, with the reason

C02 never edits SSKS files; the SSKS owner reviews these and imports what she accepts.

Usage:
    python -m scripts.export_for_ssks [--source DIR] [--custom DIR] [--output DIR]
"""
import argparse
from pathlib import Path

from scripts.build_dictionary import (
    DEFAULT_CUSTOM,
    DEFAULT_SOURCE,
    SERVICE_DIR,
    _load_seed,
    _read_csv,
    find_in_seed,
    write_csv,
)

DEFAULT_OUTPUT = SERVICE_DIR / "data" / "ssks_handover"

CANDIDATE_FIELDS = [
    "entity_type", "submitted_name", "aliases", "proposed_skill_type",
    "proposed_skill_nature", "domains", "source_component", "source_reference",
]
ADDITION_FIELDS = ["alias", "skill_id", "skill_name", "reason"]
REMOVAL_FIELDS = ["alias", "skill_id", "skill_name", "correct_skill_id", "correct_skill_name", "reason"]


def _has_alias(skill: dict, term: str) -> bool:
    return any(a.casefold() == term.casefold() for a in skill["aliases"])


def new_skill_candidates(seed: dict[str, dict], custom_dir: Path) -> list[dict[str, str]]:
    """C02 supplement skills SSKS does not have yet."""
    return [
        {
            "entity_type": "SKILL",
            "submitted_name": row["name"].strip(),
            "aliases": row.get("aliases", ""),
            "proposed_skill_type": row.get("concept_kind", ""),
            "proposed_skill_nature": row.get("skill_nature", ""),
            "domains": row.get("domains", ""),
            "source_component": "C02",
            "source_reference": row["skill_id"].strip(),
        }
        for row in _read_csv(custom_dir / "custom_skills_supplement.csv")
        if find_in_seed(seed, row["name"]) is None
    ]


def alias_additions(seed: dict[str, dict], custom_dir: Path) -> list[dict[str, str]]:
    rows = []
    for row in _read_csv(custom_dir / "alias_map.csv"):
        alias, target = row["alias"].strip(), row["skill_id"].strip()
        skill = seed.get(target)
        if skill is None or _has_alias(skill, alias) or alias.casefold() == skill["name"].casefold():
            continue
        rows.append({"alias": alias, "skill_id": target, "skill_name": skill["name"],
                     "reason": "How students write this skill in CVs"})
    return rows


def alias_removals(seed: dict[str, dict], custom_dir: Path) -> list[dict[str, str]]:
    rows = []

    def add(alias, skill_id, correct_id, reason):
        correct = seed.get(correct_id, {}) if correct_id else {}
        rows.append({
            "alias": alias,
            "skill_id": skill_id,
            "skill_name": seed[skill_id]["name"],
            "correct_skill_id": correct_id or "",
            "correct_skill_name": correct.get("name", ""),
            "reason": reason,
        })

    for row in _read_csv(custom_dir / "alias_blocklist.csv"):
        skill_id = row["skill_id"].strip()
        if skill_id in seed and _has_alias(seed[skill_id], row["alias"].strip()):
            add(row["alias"].strip(), skill_id, None, row.get("note", "") or "Wrong alias")

    names = {skill["name"].casefold(): skill_id for skill_id, skill in seed.items()}
    for skill_id, skill in seed.items():
        for alias in skill["aliases"]:
            owner = names.get(alias.casefold())
            if owner and owner != skill_id:
                add(alias, skill_id, owner, "Alias is the name of another skill: possible duplicate skill")

    for row in _read_csv(custom_dir / "alias_map.csv"):
        alias, target = row["alias"].strip(), row["skill_id"].strip()
        for skill_id, skill in seed.items():
            if skill_id != target and _has_alias(skill, alias) and names.get(alias.casefold()) != target:
                add(alias, skill_id, target, "Alias points to the wrong skill")

    return sorted(rows, key=lambda r: (r["alias"].casefold(), r["skill_id"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--custom", type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    seed = _load_seed(args.source)
    candidates = new_skill_candidates(seed, args.custom)
    additions = alias_additions(seed, args.custom)
    removals = alias_removals(seed, args.custom)

    write_csv(candidates, args.output / "new_skill_candidates.csv", CANDIDATE_FIELDS)
    write_csv(additions, args.output / "alias_additions.csv", ADDITION_FIELDS)
    write_csv(removals, args.output / "alias_removals.csv", REMOVAL_FIELDS)
    print(f"Wrote handover to {args.output}")
    print(f"  {len(candidates)} new skills, {len(additions)} aliases to add, "
          f"{len(removals)} aliases to remove or fix")


if __name__ == "__main__":
    main()
