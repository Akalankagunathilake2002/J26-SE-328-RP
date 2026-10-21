"""Build the C02 reference skill dictionary (TAF task 1).

Starts from the SSKS import-ready seed (skills from ESCO and O*NET with SK- IDs,
aliases and domains) and applies C02's hand-written files in data/dictionary/:

    custom_skills_supplement.csv  skills SSKS lacks, with C02- IDs
    alias_blocklist.csv           aliases removed from a skill (alias, skill_id)
    alias_map.csv                 aliases added to a skill (alias, skill_id); the
                                  alias is removed from every other skill

When a term is one skill's name and another skill's alias, the name wins. Terms
still shared by several skills are written to alias_conflicts.csv for review.

Output: data/dictionary/clean_skills.csv, one row per skill:

    skill_id, name, aliases, domains, skill_type, concept_kind, skill_nature, description

aliases and domains are separated by "|". The description (from ESCO/O*NET via SSKS, or the
supplement) is what the semantic skill index embeds, so meaning can be matched, not only words.

Usage:
    python -m scripts.build_dictionary [--source DIR] [--custom DIR] [--output FILE]
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = SERVICE_DIR.parent / "shared-skill-knowledge" / "seed" / "import_ready"
DEFAULT_CUSTOM = SERVICE_DIR / "data" / "dictionary"
DEFAULT_OUTPUT = DEFAULT_CUSTOM / "clean_skills.csv"
CONFLICTS_FILE = "alias_conflicts.csv"

FIELDS = [
    "skill_id", "name", "aliases", "domains", "skill_type", "concept_kind", "skill_nature",
    "description",
]
SEPARATOR = "|"


class DictionaryError(ValueError):
    pass


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(SEPARATOR) if part.strip()]


def _load_seed(source_dir: Path) -> dict[str, dict]:
    entities = _read_csv(source_dir / "canonical_entities.csv")
    if not entities:
        raise DictionaryError(f"No canonical_entities.csv found in {source_dir}")
    aliases_and_domains = _read_csv(source_dir / "aliases_and_domains.csv")

    skills = {
        row["id"]: {
            "skill_id": row["id"],
            "name": row["name"].strip(),
            "aliases": [],
            "domains": [],
            "skill_type": row["skill_type"],
            "concept_kind": row["concept_kind"],
            "skill_nature": row.get("skill_nature", ""),
            "description": " ".join(row.get("description", "").split()),
        }
        for row in entities
        if row["entity_type"] == "SKILL" and row["review_status"] == "APPROVED"
    }
    for row in aliases_and_domains:
        skill = skills.get(row["canonical_entity_id"])
        value = row["value"].strip()
        if skill is None or not value or SEPARATOR in value:
            continue
        if row["record_type"] == "ALIAS":
            skill["aliases"].append(value)
        elif row["record_type"] == "DOMAIN":
            skill["domains"].append(value)
    return skills


def find_in_seed(seed: dict[str, dict], name: str) -> str | None:
    """The seed skill whose name or alias is `name`, if any."""
    term = name.strip().casefold()
    for skill_id, skill in seed.items():
        if skill["name"].casefold() == term or any(a.casefold() == term for a in skill["aliases"]):
            return skill_id
    return None


def _add_supplement(skills: dict[str, dict], rows: list[dict[str, str]]) -> dict[str, str]:
    """Add C02 skills; skip those SSKS now has. Returns {C02 ID: SSKS ID} for skipped ones."""
    seed = dict(skills)
    replaced = {}
    for row in rows:
        skill_id = row["skill_id"].strip()
        if skill_id in skills:
            raise DictionaryError(f"Supplement skill {skill_id} already exists")
        ssks_id = find_in_seed(seed, row["name"])
        if ssks_id is not None:
            replaced[skill_id] = ssks_id
            continue
        skills[skill_id] = {
            "skill_id": skill_id,
            "name": row["name"].strip(),
            "aliases": _split(row.get("aliases", "")),
            "domains": _split(row.get("domains", "")),
            "skill_type": row.get("skill_type", ""),
            "concept_kind": row.get("concept_kind", ""),
            "skill_nature": row.get("skill_nature", ""),
            "description": " ".join(row.get("description", "").split()),
        }
    return replaced


def _remove_alias(skill: dict, term: str) -> None:
    skill["aliases"] = [a for a in skill["aliases"] if a.casefold() != term.casefold()]


def _apply_blocklist(
    skills: dict[str, dict], rows: list[dict[str, str]], replaced: dict[str, str]
) -> None:
    for row in rows:
        skill_id = row["skill_id"].strip()
        skill = skills.get(replaced.get(skill_id, skill_id))
        if skill is None:
            raise DictionaryError(f"Blocklist refers to unknown skill {row['skill_id']}")
        _remove_alias(skill, row["alias"].strip())


def _names_win(skills: dict[str, dict]) -> None:
    names = {skill["name"].casefold(): skill_id for skill_id, skill in skills.items()}
    for skill_id, skill in skills.items():
        skill["aliases"] = [
            a for a in skill["aliases"] if names.get(a.casefold(), skill_id) == skill_id
        ]


def _apply_alias_map(
    skills: dict[str, dict], rows: list[dict[str, str]], replaced: dict[str, str]
) -> None:
    for row in rows:
        alias, target = row["alias"].strip(), row["skill_id"].strip()
        target = replaced.get(target, target)
        if target not in skills:
            raise DictionaryError(f"Alias map refers to unknown skill {target}")
        for skill_id, skill in skills.items():
            if skill_id != target:
                _remove_alias(skill, alias)
        _remove_alias(skills[target], alias)
        if alias.casefold() != skills[target]["name"].casefold():
            skills[target]["aliases"].append(alias)


def _dedupe_aliases(skill: dict) -> list[str]:
    seen = {skill["name"].casefold()}
    unique = []
    for alias in skill["aliases"]:
        if alias.casefold() not in seen:
            seen.add(alias.casefold())
            unique.append(alias)
    return unique


def find_conflicts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Terms (names or aliases) that still point to more than one skill."""
    owners: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        for term in [row["name"], *_split(row["aliases"])]:
            owners[term.casefold()][row["skill_id"]] = row["name"]
    return [
        {
            "term": term,
            "skill_ids": SEPARATOR.join(sorted(ids)),
            "names": SEPARATOR.join(ids[i] for i in sorted(ids)),
        }
        for term, ids in sorted(owners.items())
        if len(ids) > 1
    ]


def build_dictionary(
    source_dir: Path,
    custom_dir: Path | None = None,
    replaced: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Build the dictionary rows.

    C02 supplement skills that SSKS now has are left out and recorded in `replaced`
    as {C02 ID: SSKS ID}; alias-map and blocklist rows for them follow to the SSKS skill.
    """
    replaced = {} if replaced is None else replaced
    skills = _load_seed(source_dir)
    if custom_dir is not None:
        replaced.update(_add_supplement(skills, _read_csv(custom_dir / "custom_skills_supplement.csv")))
        _apply_blocklist(skills, _read_csv(custom_dir / "alias_blocklist.csv"), replaced)
    _names_win(skills)
    if custom_dir is not None:
        _apply_alias_map(skills, _read_csv(custom_dir / "alias_map.csv"), replaced)

    return [
        {
            "skill_id": skill_id,
            "name": skill["name"],
            "aliases": SEPARATOR.join(_dedupe_aliases(skill)),
            "domains": SEPARATOR.join(sorted(set(skill["domains"]))),
            "skill_type": skill["skill_type"],
            "concept_kind": skill["concept_kind"],
            "skill_nature": skill["skill_nature"],
            "description": skill["description"],
        }
        for skill_id, skill in sorted(skills.items())
    ]


def write_csv(rows: list[dict[str, str]], output: Path, fields: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_dictionary(rows: list[dict[str, str]], output: Path) -> None:
    write_csv(rows, output, FIELDS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--custom", type=Path, default=DEFAULT_CUSTOM)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    replaced: dict[str, str] = {}
    rows = build_dictionary(args.source, args.custom, replaced)
    write_dictionary(rows, args.output)
    conflicts = find_conflicts(rows)
    conflicts_path = args.output.parent / CONFLICTS_FILE
    write_csv(conflicts, conflicts_path, ["term", "skill_ids", "names"])

    custom = sum(1 for row in rows if row["skill_id"].startswith("C02-"))
    print(f"Wrote {len(rows)} skills ({custom} C02 custom) to {args.output}")
    print(f"  {sum(1 for row in rows if row['aliases'])} with aliases, "
          f"{sum(1 for row in rows if row['domains'])} with domain tags")
    print(f"  {sum(1 for row in rows if row['description'])} with descriptions")
    print(f"  {len(conflicts)} terms shared by several skills -> {conflicts_path}")
    for c02_id, ssks_id in replaced.items():
        print(f"  Skipped {c02_id}: SSKS now has it as {ssks_id}. "
              "You can delete it from custom_skills_supplement.csv.")


if __name__ == "__main__":
    main()
