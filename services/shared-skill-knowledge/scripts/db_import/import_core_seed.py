"""Import approved SSKS core seed data (skills, roles, aliases, domains, external IDs).
"""

import argparse
import asyncio
import csv
import logging
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import func, insert, select, text

from app.db.base import Base
from app.models import (
    Domain, KnowledgeSource, Role, RoleAlias, RoleDomain, RoleExternalId,
    Skill, SkillAlias, SkillDomain, SkillExternalId,
)

logger = logging.getLogger("ssks.import_core_seed")

DEFAULT_SEED_DIR = Path(__file__).resolve().parents[2] / "seed" / "import_ready"

SKILL_TYPES = {
    "PROGRAMMING_LANGUAGE", "PROGRAMMING_SKILL", "PROGRAMMING_PARADIGM",
    "SOFTWARE_OR_TOOL", "KNOWLEDGE", "OTHER_SKILL",
}
SKILL_NATURES = {"TECHNICAL", "BEHAVIOURAL", "OTHER"}

ID_PATTERNS = {
    "skills": re.compile(r"^SK-\d{6}$"),
    "roles": re.compile(r"^RL-\d{6}$"),
    "aliases": re.compile(r"^AL-\d{6}$"),
    "external_ids": re.compile(r"^EXT-\d{6}$"),
}

# Only used when knowledge_sources lacks a row that external IDs need (FK is NOT NULL)
SOURCE_NAMES = {
    "ESCO": "ESCO",
    "ONET": "O*NET",
    "ONET_SOFTWARE": "O*NET Software",
    "C02_CUSTOM": "C02 Custom Curation",
}

TABLES = [
    "knowledge_sources", "skills", "roles", "skill_aliases", "role_aliases",
    "skill_domains", "role_domains", "skill_external_ids", "role_external_ids",
]
MODEL_BY_TABLE = {
    "knowledge_sources": KnowledgeSource, "skills": Skill, "roles": Role,
    "skill_aliases": SkillAlias, "role_aliases": RoleAlias,
    "skill_domains": SkillDomain, "role_domains": RoleDomain,
    "skill_external_ids": SkillExternalId, "role_external_ids": RoleExternalId,
}


class ImportBlocked(Exception):
    pass


class VerificationFailed(Exception):
    pass


def normalize_alias(value: str) -> str:
    # Same whitespace collapsing as prepare_import.normalize_alias, plus case folding for lookups
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


@dataclass
class SeedData:
    entities: list[dict]
    aliases: list[dict]
    entity_domains: list[dict]
    external_ids: list[dict]


def load_seed(seed_dir: Path) -> SeedData:
    def read(name: str, required: set[str]) -> list[dict]:
        with open(seed_dir / name, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{name} is missing columns: {sorted(missing)}")
            return list(reader)

    return SeedData(
        entities=read("canonical_entities.csv", {
            "id", "entity_type", "name", "description", "skill_type", "concept_kind",
            "skill_nature", "review_status"}),
        aliases=read("aliases_unlocked.csv", {"id", "canonical_entity_id", "value", "is_verified"}),
        entity_domains=read("entity_domains.csv", {"entity_id", "domains"}),
        external_ids=read("external_ids.csv", {
            "id", "canonical_entity_id", "source_system", "external_id", "source_version"}),
    )


@dataclass
class Snapshot:
    domains: dict = field(default_factory=dict)  # code -> domain_id
    sources: dict = field(default_factory=dict)  # code -> (source_id, version)
    skills: dict = field(default_factory=dict)  # id -> (name, skill_type)
    roles: dict = field(default_factory=dict)  # id -> name
    skill_aliases: dict = field(default_factory=dict)  # alias_id -> (skill_id, alias_text)
    role_aliases: dict = field(default_factory=dict)
    skill_domains: set = field(default_factory=set)
    role_domains: set = field(default_factory=set)
    skill_ext: dict = field(default_factory=dict)  # ext_id_id -> (skill_id, source_id, identifier)
    role_ext: dict = field(default_factory=dict)
    schema_problems: list = field(default_factory=list)


@dataclass
class Plan:
    inserts: dict = field(default_factory=lambda: {t: [] for t in TABLES})
    present: Counter = field(default_factory=Counter)
    skipped: list = field(default_factory=list)  # (table, record id, reason)
    conflicts: list = field(default_factory=list)
    blocking: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    skill_ids: set = field(default_factory=set)  # approved and valid, new or already present
    role_ids: set = field(default_factory=set)
    pending_ids: set = field(default_factory=set)
    alias_ids: dict = field(default_factory=lambda: {"skill_aliases": set(), "role_aliases": set()})

    @property
    def has_problems(self) -> bool:
        return bool(self.conflicts or self.blocking)

    def skip(self, table: str, record_id: str, reason: str) -> None:
        self.skipped.append((table, record_id, reason))

    def skip_summary(self) -> Counter:
        return Counter((t, reason.split(":")[0]) for t, _, reason in self.skipped)


def _clean(value) -> str:
    return (value or "").strip()


def plan_import(data: SeedData, snap: Snapshot, create_missing_sources: bool = False) -> Plan:
    plan = Plan()
    plan.blocking.extend(snap.schema_problems)
    _plan_entities(plan, data, snap)
    sources = _plan_sources(plan, data, snap, create_missing_sources)
    _plan_aliases(plan, data, snap)
    _plan_domains(plan, data, snap)
    _plan_external_ids(plan, data, snap, sources)
    plan.stats["csv_rows"] = {
        "canonical_entities": len(data.entities), "aliases": len(data.aliases),
        "entity_domains": len(data.entity_domains), "external_ids": len(data.external_ids),
    }
    return plan


def _plan_entities(plan: Plan, data: SeedData, snap: Snapshot) -> None:
    status_counts = Counter()
    seen = set()
    names_seen = defaultdict(list)

    for row in data.entities:
        entity_id = _clean(row["id"])
        entity_type = _clean(row["entity_type"]).upper()
        status = _clean(row["review_status"]).upper()
        status_counts[(entity_type, status)] += 1

        if entity_id in seen:
            plan.conflicts.append(f"duplicate canonical id in CSV: {entity_id}")
            continue
        seen.add(entity_id)

        if status != "APPROVED":
            plan.pending_ids.add(entity_id)
            plan.skip("entities", entity_id, f"not_approved:{status or 'EMPTY'}")
            continue

        name = _clean(row["name"])
        description = _clean(row["description"]) or None
        if entity_type == "SKILL":
            table, pattern_key = "skills", "skills"
        elif entity_type == "ROLE":
            table, pattern_key = "roles", "roles"
        else:
            plan.skip("entities", entity_id, f"invalid_entity_type:{entity_type}")
            continue

        if not ID_PATTERNS[pattern_key].match(entity_id):
            plan.conflicts.append(f"{table}: id {entity_id!r} has an unexpected format (remapping not supported)")
            continue
        if not name or len(name) > 255:
            plan.skip("entities", entity_id, "invalid_name")
            continue

        if table == "skills":
            skill_type = _clean(row["concept_kind"]).upper()
            nature = _clean(row["skill_nature"]).upper() or None
            if skill_type not in SKILL_TYPES:
                plan.skip("entities", entity_id, f"invalid_skill_type:{skill_type or 'EMPTY'}")
                continue
            if nature is not None and nature not in SKILL_NATURES:
                plan.skip("entities", entity_id, f"invalid_skill_nature:{nature}")
                continue
            existing = snap.skills.get(entity_id)
            if existing is not None:
                if existing != (name, skill_type):
                    plan.conflicts.append(
                        f"skills: {entity_id} exists as {existing!r} but CSV has {(name, skill_type)!r}")
                else:
                    plan.present["skills"] += 1
                    plan.skill_ids.add(entity_id)
                    names_seen[normalize_alias(name)].append(entity_id)
                continue
            plan.inserts["skills"].append({
                "skill_id": entity_id, "preferred_name": name, "description": description,
                "skill_type": skill_type, "skill_nature": nature, "status": "ACTIVE",
            })
            plan.skill_ids.add(entity_id)
            names_seen[normalize_alias(name)].append(entity_id)
        else:
            existing = snap.roles.get(entity_id)
            if existing is not None:
                if existing != name:
                    plan.conflicts.append(f"roles: {entity_id} exists as {existing!r} but CSV has {name!r}")
                else:
                    plan.present["roles"] += 1
                    plan.role_ids.add(entity_id)
                continue
            plan.inserts["roles"].append({
                "role_id": entity_id, "preferred_name": name, "description": description, "status": "ACTIVE",
            })
            plan.role_ids.add(entity_id)

    duplicates = {n: ids for n, ids in names_seen.items() if len(ids) > 1}
    if duplicates:
        plan.warnings.append(
            f"{len(duplicates)} skill names are shared by several approved skills (kept separate, not merged)")
    plan.stats["entity_status"] = {f"{t}:{s}": c for (t, s), c in sorted(status_counts.items())}


def _plan_sources(plan: Plan, data: SeedData, snap: Snapshot, create_missing: bool) -> dict:
    versions = defaultdict(set)
    for row in data.external_ids:
        versions[_clean(row["source_system"])].add(_clean(row["source_version"]))

    resolved = {code: source_id for code, (source_id, _) in snap.sources.items()}
    for code, found in sorted(versions.items()):
        if not code:
            continue
        if code in snap.sources:
            continue
        if len(found) != 1 or "" in found:
            plan.blocking.append(f"source {code}: needs exactly one non-empty version, found {sorted(found)}")
            continue
        if not create_missing:
            plan.blocking.append(
                f"source {code} not in knowledge_sources (external IDs need it; use --create-missing-sources)")
            continue
        source_id = f"SRC-{code}"
        plan.inserts["knowledge_sources"].append({
            "source_id": source_id, "source_code": code,
            "source_name": SOURCE_NAMES.get(code, code), "source_version": next(iter(found)),
        })
        resolved[code] = source_id
    return resolved


def _plan_aliases(plan: Plan, data: SeedData, snap: Snapshot) -> None:
    seen_ids = set()
    seen_keys = set()
    existing_keys = {
        "skill_aliases": {(p, normalize_alias(t)): a for a, (p, t) in snap.skill_aliases.items()},
        "role_aliases": {(p, normalize_alias(t)): a for a, (p, t) in snap.role_aliases.items()},
    }
    existing_by_id = {"skill_aliases": snap.skill_aliases, "role_aliases": snap.role_aliases}

    for row in data.aliases:
        alias_id = _clean(row["id"])
        parent = _clean(row["canonical_entity_id"])
        verified = _clean(row["is_verified"]).upper()
        text_value = _clean(row["value"])

        if alias_id in seen_ids:
            plan.conflicts.append(f"duplicate alias id in CSV: {alias_id}")
            continue
        seen_ids.add(alias_id)

        if verified != "TRUE":
            reason = "unverified" if verified == "FALSE" else f"invalid_verification:{verified or 'EMPTY'}"
            plan.skip("aliases", alias_id, reason)
            continue
        if parent in plan.skill_ids:
            table = "skill_aliases"
        elif parent in plan.role_ids:
            table = "role_aliases"
        else:
            plan.skip("aliases", alias_id, "entity_not_imported")
            continue
        if not text_value or len(text_value) > 255:
            plan.skip("aliases", alias_id, "invalid_alias_text")
            continue
        if not ID_PATTERNS["aliases"].match(alias_id):
            plan.conflicts.append(f"{table}: alias id {alias_id!r} has an unexpected format")
            continue

        normalized = normalize_alias(text_value)
        if not normalized:
            plan.skip("aliases", alias_id, "invalid_alias_text")
            continue
        key = (table, parent, normalized)
        if key in seen_keys:
            plan.skip("aliases", alias_id, "duplicate_alias_for_entity")
            continue
        seen_keys.add(key)
        plan.alias_ids[table].add(alias_id)

        existing = existing_by_id[table].get(alias_id)
        if existing is not None:
            if existing != (parent, text_value):
                plan.conflicts.append(f"{table}: {alias_id} exists as {existing!r} but CSV has {(parent, text_value)!r}")
            else:
                plan.present[table] += 1
            continue
        if (parent, normalized) in existing_keys[table]:
            plan.skip("aliases", alias_id, "duplicate_alias_for_entity")
            plan.alias_ids[table].discard(alias_id)
            continue

        parent_col = "skill_id" if table == "skill_aliases" else "role_id"
        plan.inserts[table].append({
            "alias_id": alias_id, parent_col: parent, "alias_text": text_value,
            "normalized_alias": normalized, "source_id": None, "verification_status": "VERIFIED",
        })


def _plan_domains(plan: Plan, data: SeedData, snap: Snapshot) -> None:
    seen = set()
    for row in data.entity_domains:
        entity_id = _clean(row["entity_id"])
        if entity_id in plan.skill_ids:
            table, parent_col, existing = "skill_domains", "skill_id", snap.skill_domains
        elif entity_id in plan.role_ids:
            table, parent_col, existing = "role_domains", "role_id", snap.role_domains
        else:
            plan.skip("domains", entity_id, "entity_not_imported")
            continue

        for code in {c.strip().upper() for c in _clean(row["domains"]).split(",") if c.strip()}:
            domain_id = snap.domains.get(code)
            if domain_id is None:
                plan.skip("domains", entity_id, f"unknown_domain:{code}")
                continue
            if (table, entity_id, domain_id) in seen:
                continue
            seen.add((table, entity_id, domain_id))
            if (entity_id, domain_id) in existing:
                plan.present[table] += 1
                continue
            plan.inserts[table].append({parent_col: entity_id, "domain_id": domain_id})


def _plan_external_ids(plan: Plan, data: SeedData, snap: Snapshot, sources: dict) -> None:
    seen_ids = set()
    seen_keys = {}
    existing_keys = {
        "skill_external_ids": {(s, i): (e, p) for e, (p, s, i) in snap.skill_ext.items()},
        "role_external_ids": {(s, i): (e, p) for e, (p, s, i) in snap.role_ext.items()},
    }
    existing_by_id = {"skill_external_ids": snap.skill_ext, "role_external_ids": snap.role_ext}

    for row in data.external_ids:
        ext_id = _clean(row["id"])
        parent = _clean(row["canonical_entity_id"])
        system = _clean(row["source_system"])
        identifier = _clean(row["external_id"])

        if ext_id in seen_ids:
            plan.conflicts.append(f"duplicate external id record in CSV: {ext_id}")
            continue
        seen_ids.add(ext_id)

        if parent in plan.skill_ids:
            table, parent_col = "skill_external_ids", "skill_id"
        elif parent in plan.role_ids:
            table, parent_col = "role_external_ids", "role_id"
        else:
            plan.skip("external_ids", ext_id, "entity_not_imported")
            continue
        source_id = sources.get(system)
        if source_id is None:
            plan.skip("external_ids", ext_id, f"unresolved_source:{system or 'EMPTY'}")
            continue
        if not identifier or len(identifier) > 255:
            plan.skip("external_ids", ext_id, "invalid_external_identifier")
            continue
        if not ID_PATTERNS["external_ids"].match(ext_id):
            plan.conflicts.append(f"{table}: id {ext_id!r} has an unexpected format")
            continue

        key = (table, source_id, identifier)
        if key in seen_keys:
            plan.conflicts.append(
                f"{table}: ({source_id}, {identifier}) appears in CSV for {seen_keys[key]} and {ext_id}")
            continue
        seen_keys[key] = ext_id

        existing = existing_by_id[table].get(ext_id)
        if existing is not None:
            if existing != (parent, source_id, identifier):
                plan.conflicts.append(f"{table}: {ext_id} exists as {existing!r} but CSV differs")
            else:
                plan.present[table] += 1
            continue
        clash = existing_keys[table].get((source_id, identifier))
        if clash is not None:
            plan.conflicts.append(
                f"{table}: ({source_id}, {identifier}) already stored as {clash[0]} for {clash[1]}")
            continue
        plan.inserts[table].append({
            "external_id_id": ext_id, parent_col: parent,
            "source_id": source_id, "external_identifier": identifier,
        })


async def check_schema(session) -> tuple[list[str], set[str]]:
    problems, absent = [], set()
    result = await session.execute(text(
        "select table_name, column_name from information_schema.columns where table_schema = current_schema()"))
    actual = defaultdict(set)
    for table, column in result:
        actual[table].add(column)
    for table_name in TABLES + ["domains"]:
        if table_name not in actual:
            absent.add(table_name)
        model_table = Base.metadata.tables[table_name]
        missing = {c.name for c in model_table.columns} - actual.get(table_name, set())
        if missing:
            problems.append(f"table {table_name} is missing columns/table: {sorted(missing)} (schema not changed by importer)")
    return problems, absent


async def fetch_snapshot(session) -> Snapshot:
    problems, absent = await check_schema(session)
    snap = Snapshot(schema_problems=problems)
    if absent:
        return snap
    snap.domains = {r.code: r.domain_id for r in await session.execute(select(Domain.code, Domain.domain_id))}
    snap.sources = {
        r.source_code: (r.source_id, r.source_version)
        for r in await session.execute(select(
            KnowledgeSource.source_code, KnowledgeSource.source_id, KnowledgeSource.source_version))}
    snap.skills = {r[0]: (r[1], r[2]) for r in await session.execute(
        select(Skill.skill_id, Skill.preferred_name, Skill.skill_type))}
    snap.roles = {r[0]: r[1] for r in await session.execute(select(Role.role_id, Role.preferred_name))}
    snap.skill_aliases = {r[0]: (r[1], r[2]) for r in await session.execute(
        select(SkillAlias.alias_id, SkillAlias.skill_id, SkillAlias.alias_text))}
    snap.role_aliases = {r[0]: (r[1], r[2]) for r in await session.execute(
        select(RoleAlias.alias_id, RoleAlias.role_id, RoleAlias.alias_text))}
    snap.skill_domains = {tuple(r) for r in await session.execute(select(SkillDomain.skill_id, SkillDomain.domain_id))}
    snap.role_domains = {tuple(r) for r in await session.execute(select(RoleDomain.role_id, RoleDomain.domain_id))}
    snap.skill_ext = {r[0]: tuple(r[1:]) for r in await session.execute(select(
        SkillExternalId.external_id_id, SkillExternalId.skill_id,
        SkillExternalId.source_id, SkillExternalId.external_identifier))}
    snap.role_ext = {r[0]: tuple(r[1:]) for r in await session.execute(select(
        RoleExternalId.external_id_id, RoleExternalId.role_id,
        RoleExternalId.source_id, RoleExternalId.external_identifier))}
    return snap


async def table_counts(session) -> dict:
    counts = {}
    for name in TABLES + ["domains"]:
        counts[name] = (await session.execute(select(func.count()).select_from(Base.metadata.tables[name]))).scalar_one()
    return counts


async def apply_plan(session, plan: Plan) -> None:
    for table in TABLES:
        rows = plan.inserts[table]
        if rows:
            await session.execute(insert(MODEL_BY_TABLE[table]), rows)
            logger.info("inserted %d rows into %s", len(rows), table)


async def _scalar(session, sql: str, **params):
    return (await session.execute(text(sql), params)).scalar_one()


async def verify_import(session, plan: Plan, expected_domains: dict) -> list[tuple[str, bool, str]]:
    results = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    skill_ids, role_ids = sorted(plan.skill_ids), sorted(plan.role_ids)
    n = await _scalar(session, "select count(*) from skills where skill_id = any(:ids)", ids=skill_ids)
    record("all planned skills present", n == len(skill_ids), f"{n}/{len(skill_ids)}")
    n = await _scalar(session, "select count(*) from roles where role_id = any(:ids)", ids=role_ids)
    record("all planned roles present", n == len(role_ids), f"{n}/{len(role_ids)}")

    pending = sorted(plan.pending_ids)
    n = await _scalar(session, "select (select count(*) from skills where skill_id = any(:p)) + "
                               "(select count(*) from roles where role_id = any(:p))", p=pending)
    record("no pending entities in database", n == 0, f"{n} found")

    fk_checks = {
        "skill_aliases.skill_id": "select count(*) from skill_aliases a left join skills s on s.skill_id = a.skill_id where s.skill_id is null",
        "role_aliases.role_id": "select count(*) from role_aliases a left join roles r on r.role_id = a.role_id where r.role_id is null",
        "skill_domains.skill_id": "select count(*) from skill_domains d left join skills s on s.skill_id = d.skill_id where s.skill_id is null",
        "skill_domains.domain_id": "select count(*) from skill_domains d left join domains x on x.domain_id = d.domain_id where x.domain_id is null",
        "role_domains.role_id": "select count(*) from role_domains d left join roles r on r.role_id = d.role_id where r.role_id is null",
        "role_domains.domain_id": "select count(*) from role_domains d left join domains x on x.domain_id = d.domain_id where x.domain_id is null",
        "skill_external_ids.skill_id": "select count(*) from skill_external_ids e left join skills s on s.skill_id = e.skill_id where s.skill_id is null",
        "skill_external_ids.source_id": "select count(*) from skill_external_ids e left join knowledge_sources k on k.source_id = e.source_id where k.source_id is null",
        "role_external_ids.role_id": "select count(*) from role_external_ids e left join roles r on r.role_id = e.role_id where r.role_id is null",
        "role_external_ids.source_id": "select count(*) from role_external_ids e left join knowledge_sources k on k.source_id = e.source_id where k.source_id is null",
    }
    for name, sql in fk_checks.items():
        n = await _scalar(session, sql)
        record(f"foreign key resolves: {name}", n == 0, f"{n} orphans")

    dup_alias = await _scalar(session, "select count(*) from (select 1 from skill_aliases group by skill_id, normalized_alias having count(*) > 1) t") \
        + await _scalar(session, "select count(*) from (select 1 from role_aliases group by role_id, normalized_alias having count(*) > 1) t")
    record("no duplicate aliases per entity", dup_alias == 0, f"{dup_alias} duplicate groups")
    dup_ext = await _scalar(session, "select count(*) from (select 1 from skill_external_ids group by source_id, external_identifier having count(*) > 1) t") \
        + await _scalar(session, "select count(*) from (select 1 from role_external_ids group by source_id, external_identifier having count(*) > 1) t")
    record("no duplicate external identifiers", dup_ext == 0, f"{dup_ext} duplicate groups")

    bad = 0
    for table, ids in plan.alias_ids.items():
        bad += await _scalar(
            session, f"select count(*) from {table} where alias_id = any(:ids) and verification_status <> 'VERIFIED'",
            ids=sorted(ids))
    record("all imported aliases are verified", bad == 0, f"{bad} not verified")

    rows = {r[0]: r[1] for r in await session.execute(text("select code, domain_id from domains"))}
    record("domains table unchanged", rows == expected_domains, f"{rows}")
    return results


@dataclass
class ImportResult:
    database: str
    plan: Plan
    before: dict
    after: dict | None = None
    checks: list = field(default_factory=list)
    applied: bool = False


async def run_import(sessionmaker, data: SeedData, *, apply: bool, create_missing_sources: bool,
                     confirm_database: str | None = None) -> ImportResult:
    async with sessionmaker() as session:
        database = await _scalar(session, "select current_database()")
        snap = await fetch_snapshot(session)
        before = await table_counts(session) if snap.domains else {}
        plan = plan_import(data, snap, create_missing_sources)
        await session.rollback()

    result = ImportResult(database=database, plan=plan, before=before)
    if not apply:
        return result
    if plan.has_problems:
        raise ImportBlocked("; ".join((plan.blocking + plan.conflicts)[:5]))
    if confirm_database != database:
        raise ImportBlocked(f"--confirm-database must equal the connected database ({database!r})")

    async with sessionmaker() as session:
        async with session.begin():
            snap = await fetch_snapshot(session)
            plan = plan_import(data, snap, create_missing_sources)
            if plan.has_problems:
                raise ImportBlocked("; ".join((plan.blocking + plan.conflicts)[:5]))
            await apply_plan(session, plan)
            checks = await verify_import(session, plan, snap.domains)
            failed = [c for c in checks if not c[1]]
            if failed:
                raise VerificationFailed(f"post-import checks failed, rolling back: {failed}")
            result.plan, result.checks = plan, checks
            logger.info("committing transaction")
    async with sessionmaker() as session:
        result.after = await table_counts(session)
    result.applied = True
    return result


def format_report(result: ImportResult) -> str:
    plan = result.plan
    lines = [f"Database: {result.database}", "", "CSV rows: " + str(plan.stats.get("csv_rows"))]
    lines.append("Entity status counts: " + str(plan.stats.get("entity_status")))
    lines.append("")
    lines.append("Rows to insert / already present:")
    for table in TABLES:
        lines.append(f"  {table:22} insert={len(plan.inserts[table]):5}  present={plan.present[table]}")
    lines.append("")
    lines.append("Skipped (table, reason): " + str(dict(plan.skip_summary())))
    for title, items in (("Blocking", plan.blocking), ("Conflicts", plan.conflicts), ("Warnings", plan.warnings)):
        lines.append(f"{title}: {len(items)}")
        lines.extend(f"  - {i}" for i in items[:20])
    if result.before:
        lines.append("")
        lines.append("Counts before: " + str(result.before))
    if result.after:
        lines.append("Counts after:  " + str(result.after))
    for name, ok, detail in result.checks:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name} ({detail})")
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--apply", action="store_true", help="write to the database (default is dry-run)")
    parser.add_argument("--confirm-database", help="database name that must match the connection")
    parser.add_argument("--create-missing-sources", action="store_true",
                        help="create knowledge_sources rows that external IDs need")
    return parser.parse_args(argv)


async def main_async(args) -> int:
    from app.db.session import dispose_engine, get_sessionmaker

    data = load_seed(args.seed_dir)
    try:
        result = await run_import(
            get_sessionmaker(), data, apply=args.apply,
            create_missing_sources=args.create_missing_sources, confirm_database=args.confirm_database)
    except (ImportBlocked, VerificationFailed) as exc:
        logger.error("import stopped: %s", exc)
        return 2
    finally:
        await dispose_engine()
    print(format_report(result))
    if not args.apply:
        logger.info("dry-run only, nothing written")
    return 1 if result.plan.has_problems else 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return asyncio.run(main_async(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
