"""Verify Neon v2 SSKS schema and idempotently import mapped data in parent-first order."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.migration.common import (
    DEFAULT_EXPORT_DIR,
    EXPECTED_EMBEDDING_DIMENSION,
    EXPECTED_NEON_V2_SCHEMA,
    LEGACY_TABLES,
    NEON_IMPORT_ORDER,
    TABLE_PRIMARY_KEYS,
    UUID_FK_ENTITY_MAP,
    UUID_PK_ENTITY_BY_TABLE,
    get_neon_dsn,
    read_csv_rows,
    redact_dsn,
)

logger = logging.getLogger("ssks.migration.import_neon")


@dataclass
class SchemaCheckResult:
    database: str
    current_user: str
    schema: str
    schema_exists: bool
    extensions: dict[str, bool] = field(default_factory=dict)
    missing_tables: list[str] = field(default_factory=list)
    extra_tables: list[str] = field(default_factory=list)
    table_mismatches: dict[str, list[str]] = field(default_factory=dict)
    existing_counts: dict[str, int] = field(default_factory=dict)
    permissions: dict[str, bool] = field(default_factory=dict)

    @property
    def is_compatible(self) -> bool:
        return (
            self.schema_exists
            and all(self.extensions.values())
            and not self.missing_tables
            and not self.table_mismatches
        )


@dataclass
class ImportPlan:
    schema_check: SchemaCheckResult
    rows_by_table: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    inserts_by_table: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    already_present: Counter = field(default_factory=Counter)
    conflicts: list[str] = field(default_factory=list)
    blocking: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    applied_counts: dict[str, int] = field(default_factory=dict)

    @property
    def has_problems(self) -> bool:
        return bool(self.conflicts or self.blocking or not self.schema_check.is_compatible)


def _parse_vector_text(raw: str) -> list[float]:
    cleaned = raw.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    if len(parts) != EXPECTED_EMBEDDING_DIMENSION:
        raise ValueError(f"Expected {EXPECTED_EMBEDDING_DIMENSION} vector elements, got {len(parts)}")
    vals = [float(p) for p in parts]
    if not all(math.isfinite(v) for v in vals):
        raise ValueError("Vector contains non-finite float values")
    return vals


def coerce_field_value(raw: str | None, udt_name: str, *, table: str, column: str) -> Any:
    """Convert decoded CSV string values into exact asyncpg parameter types."""
    if raw is None:
        return None
    if udt_name == "uuid":
        return uuid.UUID(raw)
    if udt_name == "timestamptz":
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    if udt_name == "float8":
        return float(raw)
    if udt_name == "int2":
        return int(raw)
    if udt_name == "vector":
        vec = _parse_vector_text(raw)
        return "[" + ",".join(repr(v) for v in vec) + "]"
    return raw


def _normalize_for_compare(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, datetime):
        dt = val if val.tzinfo else val.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    if isinstance(val, float):
        return round(val, 10)
    return val


def _rows_match(incoming: dict[str, Any], existing: dict[str, Any], columns: list[str]) -> bool:
    for col in columns:
        if _normalize_for_compare(incoming.get(col)) != _normalize_for_compare(existing.get(col)):
            return False
    return True


async def check_neon_schema(conn: asyncpg.Connection, *, schema: str = "ssks") -> SchemaCheckResult:
    """Inspect live Neon schema, tables, column contracts, extensions, and row counts."""
    db_name = await conn.fetchval("SELECT current_database()")
    cur_user = await conn.fetchval("SELECT current_user")
    schema_exists = bool(
        await conn.fetchval("SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = $1)", schema)
    )
    ext_rows = await conn.fetch("SELECT extname FROM pg_extension WHERE extname = ANY($1)", ["vector", "uuid-ossp"])
    installed_exts = {r["extname"] for r in ext_rows}
    extensions = {name: (name in installed_exts) for name in ("vector", "uuid-ossp")}

    result = SchemaCheckResult(
        database=db_name,
        current_user=cur_user,
        schema=schema,
        schema_exists=schema_exists,
        extensions=extensions,
    )
    if not schema_exists:
        result.missing_tables = list(NEON_IMPORT_ORDER)
        return result

    actual_tables = {
        r["table_name"]
        for r in await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 AND table_type = 'BASE TABLE'",
            schema,
        )
    }
    expected_set = set(NEON_IMPORT_ORDER)
    result.missing_tables = [t for t in NEON_IMPORT_ORDER if t not in actual_tables]
    result.extra_tables = sorted(actual_tables - expected_set)

    col_rows = await conn.fetch(
        """
        SELECT table_name, column_name, udt_name, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_schema = $1
        ORDER BY table_name, ordinal_position
        """,
        schema,
    )
    actual_cols: dict[str, dict[str, dict[str, Any]]] = {}
    for r in col_rows:
        actual_cols.setdefault(r["table_name"], {})[r["column_name"]] = dict(r)

    for table in NEON_IMPORT_ORDER:
        if table in result.missing_tables:
            continue
        expected_cols = EXPECTED_NEON_V2_SCHEMA[table]
        actual_map = actual_cols.get(table, {})
        issues: list[str] = []

        for col_spec in expected_cols:
            actual = actual_map.get(col_spec.name)
            if actual is None:
                issues.append(f"missing column {col_spec.name}")
                continue
            if actual["udt_name"] != col_spec.udt_name:
                issues.append(f"{col_spec.name}: expected type {col_spec.udt_name}, got {actual['udt_name']}")
            if col_spec.max_length is not None and actual["character_maximum_length"] != col_spec.max_length:
                issues.append(
                    f"{col_spec.name}: expected max_length {col_spec.max_length}, got {actual['character_maximum_length']}"
                )
            actual_nullable = actual["is_nullable"] == "YES"
            if actual_nullable != col_spec.nullable:
                issues.append(f"{col_spec.name}: expected nullable={col_spec.nullable}, got {actual_nullable}")

        extra_cols = sorted(set(actual_map) - {c.name for c in expected_cols})
        if extra_cols:
            issues.append(f"unexpected extra columns: {extra_cols}")

        if issues:
            result.table_mismatches[table] = issues

        cnt = await conn.fetchval(f'SELECT count(*) FROM "{schema}"."{table}"')
        result.existing_counts[table] = int(cnt)
        has_insert = await conn.fetchval(
            "SELECT has_table_privilege($1, $2, 'INSERT')",
            cur_user,
            f"{schema}.{table}",
        )
        result.permissions[table] = bool(has_insert)

    return result


def load_mapped_dataset(
    export_dir: Path,
    mapped_dir: Path | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]:
    """Load mapped Neon-ready CSVs, validate uuid_mapping consistency, and coerce types."""
    resolved_mapped = mapped_dir or (export_dir / "mapped")
    mapping_path = export_dir / "uuid_mapping.csv"
    blocking: list[str] = []
    warnings: list[str] = []

    if not mapping_path.exists():
        blocking.append(f"Missing uuid_mapping.csv at {mapping_path}; run generate_uuid_mapping.py first.")
        return {}, blocking, warnings

    _, mapping_rows = read_csv_rows(mapping_path)
    mapped_uuid_sets: dict[str, set[str]] = {}
    for row in mapping_rows:
        etype = row.get("entity_type") or ""
        gen_uuid = row.get("generated_uuid") or ""
        mapped_uuid_sets.setdefault(etype, set()).add(gen_uuid)

    rows_by_table: dict[str, list[dict[str, Any]]] = {}
    for table in NEON_IMPORT_ORDER:
        csv_path = resolved_mapped / f"{table}.csv"
        if table == "skill_embeddings" and not csv_path.exists():
            alt_path = export_dir / "skill_embeddings.csv"
            if alt_path.exists():
                csv_path = alt_path
            else:
                rows_by_table[table] = []
                warnings.append(
                    "skill_embeddings.csv not present; skipping embeddings import (regenerate via generate_skill_embeddings.py)."
                )
                continue

        if not csv_path.exists():
            blocking.append(f"Missing mapped CSV for table {table}: {csv_path}")
            rows_by_table[table] = []
            continue

        headers, raw_rows = read_csv_rows(csv_path)
        expected_specs = EXPECTED_NEON_V2_SCHEMA[table]
        expected_cols = [c.name for c in expected_specs]
        if headers != expected_cols:
            blocking.append(f"{table}.csv header mismatch: expected {expected_cols}, got {headers}")
            rows_by_table[table] = []
            continue

        spec_by_col = {c.name: c for c in expected_specs}
        coerced_rows: list[dict[str, Any]] = []
        for idx, raw_row in enumerate(raw_rows, start=1):
            coerced: dict[str, Any] = {}
            for col in expected_cols:
                spec = spec_by_col[col]
                raw_val = raw_row.get(col)
                if raw_val is None and not spec.nullable:
                    blocking.append(f"{table} row {idx}: NULL in NOT NULL column {col}")
                    continue
                try:
                    coerced[col] = coerce_field_value(raw_val, spec.udt_name, table=table, column=col)
                except Exception as exc:
                    blocking.append(f"{table} row {idx} col {col}: invalid {spec.udt_name} value ({exc})")
            coerced_rows.append(coerced)

        # Confirm converted UUID PKs and FKs match uuid_mapping.csv entries.
        if table in UUID_PK_ENTITY_BY_TABLE:
            etype, pk_col = UUID_PK_ENTITY_BY_TABLE[table]
            expected_set = mapped_uuid_sets.get(etype, set())
            for idx, r in enumerate(coerced_rows, start=1):
                if str(r.get(pk_col)) not in expected_set:
                    blocking.append(f"{table} row {idx}: PK {r.get(pk_col)} missing from uuid_mapping.csv")

        for fk_col, ref_etype in UUID_FK_ENTITY_MAP.get(table, []):
            expected_set = mapped_uuid_sets.get(ref_etype, set())
            for idx, r in enumerate(coerced_rows, start=1):
                val = r.get(fk_col)
                if val is not None and str(val) not in expected_set:
                    blocking.append(f"{table} row {idx}: FK {fk_col}={val} missing from uuid_mapping.csv")

        rows_by_table[table] = coerced_rows

    # Verify canonical parent FKs across loaded dataset before touching Neon.
    skill_ids = {r["skill_id"] for r in rows_by_table.get("skills", [])}
    role_ids = {r["role_id"] for r in rows_by_table.get("roles", [])}
    domain_ids = {r["domain_id"] for r in rows_by_table.get("domains", [])}
    source_ids = {r["source_id"] for r in rows_by_table.get("knowledge_sources", [])}
    rel_ids = {r["relationship_id"] for r in rows_by_table.get("skill_relationships", [])}

    for tbl in ("skill_domains", "skill_aliases", "skill_external_ids", "skill_embeddings"):
        for r in rows_by_table.get(tbl, []):
            if r["skill_id"] not in skill_ids:
                blocking.append(f"{tbl}: unresolved skill_id {r['skill_id']!r}")
    for tbl in ("role_domains", "role_aliases", "role_external_ids"):
        for r in rows_by_table.get(tbl, []):
            if r["role_id"] not in role_ids:
                blocking.append(f"{tbl}: unresolved role_id {r['role_id']!r}")
    for tbl in ("skill_domains", "role_domains"):
        for r in rows_by_table.get(tbl, []):
            if r["domain_id"] not in domain_ids:
                blocking.append(f"{tbl}: unresolved domain_id {r['domain_id']!r}")
    for tbl in ("skill_relationships", "candidate_skill_relationships"):
        for r in rows_by_table.get(tbl, []):
            if r["source_skill_id"] not in skill_ids or r["target_skill_id"] not in skill_ids:
                blocking.append(f"{tbl}: unresolved relationship skill endpoint")
            if r["source_skill_id"] == r["target_skill_id"]:
                blocking.append(f"{tbl}: self-referencing skill relationship")
    for tbl in (
        "skill_aliases",
        "role_aliases",
        "skill_relationships",
        "candidate_skill_relationships",
        "skill_external_ids",
        "role_external_ids",
    ):
        for r in rows_by_table.get(tbl, []):
            if r["source_id"] is not None and r["source_id"] not in source_ids:
                blocking.append(f"{tbl}: unresolved source_id {r['source_id']}")
    for r in rows_by_table.get("candidate_skill_relationships", []):
        if r["canonical_relationship_id"] is not None and r["canonical_relationship_id"] not in rel_ids:
            blocking.append(f"candidate_skill_relationships: unresolved canonical_relationship_id")

    return rows_by_table, blocking, warnings


async def plan_neon_import(
    conn: asyncpg.Connection,
    export_dir: Path,
    *,
    mapped_dir: Path | None = None,
    schema: str = "ssks",
) -> ImportPlan:
    """Inspect Neon schema + existing rows and compute a conflict-free idempotent import plan."""
    schema_check = await check_neon_schema(conn, schema=schema)
    rows_by_table, blocking, warnings = load_mapped_dataset(export_dir, mapped_dir)
    plan = ImportPlan(
        schema_check=schema_check,
        rows_by_table=rows_by_table,
        blocking=blocking,
        warnings=warnings,
    )

    if not schema_check.is_compatible:
        return plan

    for table in NEON_IMPORT_ORDER:
        incoming_rows = rows_by_table.get(table, [])
        if not incoming_rows:
            plan.inserts_by_table[table] = []
            continue

        if not schema_check.permissions.get(table, False):
            plan.blocking.append(f"Current role lacks INSERT privilege on {schema}.{table}")
            continue

        cols = [c.name for c in EXPECTED_NEON_V2_SCHEMA[table]]
        pk_cols = TABLE_PRIMARY_KEYS[table]
        select_clause = ", ".join(
            f'"{c}"::text AS "{c}"' if c == "embedding" else f'"{c}"' for c in cols
        )
        existing_records = await conn.fetch(f'SELECT {select_clause} FROM "{schema}"."{table}"')
        existing_by_pk = {
            tuple(_normalize_for_compare(rec[pk]) for pk in pk_cols): dict(rec)
            for rec in existing_records
        }

        to_insert: list[dict[str, Any]] = []
        for row in incoming_rows:
            pk_key = tuple(_normalize_for_compare(row[pk]) for pk in pk_cols)
            existing = existing_by_pk.get(pk_key)
            if existing is None:
                to_insert.append(row)
            elif _rows_match(row, existing, cols):
                plan.already_present[table] += 1
            else:
                plan.conflicts.append(
                    f"{schema}.{table} PK {pk_key} already exists in Neon with different values; refusing to overwrite."
                )

        # Check secondary unique constraints in v2 setup.sql (domains.code, knowledge_sources.source_code, skill_relationships directional tuple).
        if table == "domains":
            existing_codes = {r["code"]: r["domain_id"] for r in existing_records}
            for row in to_insert:
                if row["code"] in existing_codes and existing_codes[row["code"]] != row["domain_id"]:
                    plan.conflicts.append(
                        f"{schema}.domains unique code {row['code']!r} already used by {existing_codes[row['code']]!r}"
                    )
        elif table == "knowledge_sources":
            existing_codes = {r["source_code"]: str(r["source_id"]) for r in existing_records}
            for row in to_insert:
                if row["source_code"] in existing_codes and existing_codes[row["source_code"]] != str(row["source_id"]):
                    plan.conflicts.append(
                        f"{schema}.knowledge_sources unique source_code {row['source_code']!r} already used by {existing_codes[row['source_code']]}"
                    )
        elif table == "skill_relationships":
            existing_edges = {
                (r["source_skill_id"], r["target_skill_id"], r["relationship_type"]): str(r["relationship_id"])
                for r in existing_records
            }
            for row in to_insert:
                edge = (row["source_skill_id"], row["target_skill_id"], row["relationship_type"])
                if edge in existing_edges and existing_edges[edge] != str(row["relationship_id"]):
                    plan.conflicts.append(
                        f"{schema}.skill_relationships directional edge {edge} already exists under {existing_edges[edge]}"
                    )

        plan.inserts_by_table[table] = to_insert

    return plan


async def apply_neon_import(conn: asyncpg.Connection, plan: ImportPlan, *, schema: str = "ssks") -> dict[str, int]:
    """Execute parent-first inserts inside a single database transaction."""
    if plan.has_problems:
        raise RuntimeError("Cannot apply import while schema mismatches, blocking errors, or conflicts exist.")

    applied: dict[str, int] = {}
    async with conn.transaction():
        for table in NEON_IMPORT_ORDER:
            rows = plan.inserts_by_table.get(table, [])
            if not rows:
                applied[table] = 0
                continue

            specs = EXPECTED_NEON_V2_SCHEMA[table]
            cols = [c.name for c in specs]
            pk_cols = TABLE_PRIMARY_KEYS[table]
            col_sql = ", ".join(f'"{c}"' for c in cols)
            placeholders = ", ".join(
                f"${i}::vector" if specs[i - 1].udt_name == "vector" else f"${i}"
                for i in range(1, len(cols) + 1)
            )
            pk_sql = ", ".join(f'"{c}"' for c in pk_cols)
            stmt = (
                f'INSERT INTO "{schema}"."{table}" ({col_sql}) VALUES ({placeholders}) '
                f"ON CONFLICT ({pk_sql}) DO NOTHING"
            )
            tuples = [tuple(row[c] for c in cols) for row in rows]
            await conn.executemany(stmt, tuples)
            applied[table] = len(rows)
            logger.info("Inserted %5d rows into %s.%s", len(rows), schema, table)

    plan.applied_counts = applied
    return applied


async def run_import(
    *,
    export_dir: Path,
    mapped_dir: Path | None = None,
    env_file: Path | None = None,
    schema: str = "ssks",
    check_schema_only: bool = False,
    apply: bool = False,
    confirm_database: str | None = None,
    use_owner: bool = False,
) -> tuple[SchemaCheckResult, ImportPlan | None]:
    dsn = get_neon_dsn(env_file, use_owner=use_owner)
    try:
        conn = await asyncpg.connect(dsn, timeout=12)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Neon: {redact_dsn(exc)}") from None

    try:
        schema_check = await check_neon_schema(conn, schema=schema)
        if check_schema_only:
            return schema_check, None

        plan = await plan_neon_import(conn, export_dir, mapped_dir=mapped_dir, schema=schema)
        if not apply:
            return schema_check, plan

        if plan.has_problems:
            raise RuntimeError("Dry-run checks failed; aborting apply without writing to Neon.")
        if confirm_database != schema_check.database:
            raise RuntimeError(
                f"--confirm-database must equal the connected Neon database ({schema_check.database!r})"
            )

        await apply_neon_import(conn, plan, schema=schema)
        return schema_check, plan
    finally:
        await conn.close()


def format_schema_report(sc: SchemaCheckResult) -> str:
    lines = [
        f"Neon Database   : {sc.database} (user: {sc.current_user})",
        f"Target Schema   : {sc.schema} (exists={sc.schema_exists})",
        f"Extensions      : {sc.extensions}",
        f"Schema Match    : {'PASS' if sc.is_compatible else 'FAIL'}",
    ]
    if sc.missing_tables:
        lines.append(f"Missing Tables  : {sc.missing_tables}")
    if sc.extra_tables:
        lines.append(f"Extra Tables    : {sc.extra_tables}")
    if sc.table_mismatches:
        lines.append("Table Mismatches:")
        for tbl, issues in sc.table_mismatches.items():
            lines.append(f"  - {tbl}: {issues}")
    if sc.existing_counts:
        lines.append("")
        lines.append("Current Neon Row Counts:")
        for tbl in NEON_IMPORT_ORDER:
            if tbl in sc.existing_counts:
                lines.append(f"  {tbl:32} {sc.existing_counts[tbl]:6}")
    return "\n".join(lines)


def format_import_report(plan: ImportPlan, *, applied: bool) -> str:
    lines = [format_schema_report(plan.schema_check), "", "Import Plan (Parent-First Order):"]
    for tbl in NEON_IMPORT_ORDER:
        to_ins = len(plan.inserts_by_table.get(tbl, []))
        present = plan.already_present[tbl]
        loaded = len(plan.rows_by_table.get(tbl, []))
        lines.append(f"  {tbl:32} csv={loaded:5}  insert={to_ins:5}  already_present={present:5}")
    lines.append("")
    lines.append(f"Blocking Errors : {len(plan.blocking)}")
    lines.extend(f"  - {b}" for b in plan.blocking[:20])
    lines.append(f"Data Conflicts  : {len(plan.conflicts)}")
    lines.extend(f"  - {c}" for c in plan.conflicts[:20])
    lines.append(f"Warnings        : {len(plan.warnings)}")
    lines.extend(f"  - {w}" for w in plan.warnings[:20])
    if applied:
        lines.append("")
        lines.append("Applied Inserts :")
        for tbl in NEON_IMPORT_ORDER:
            lines.append(f"  {tbl:32} {plan.applied_counts.get(tbl, 0):6}")
    else:
        lines.append("")
        lines.append("Mode: DRY-RUN ONLY (no rows written to Neon)")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--mapped-dir", type=Path, default=None)
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--schema", default="ssks")
    parser.add_argument("--check-schema-only", action="store_true", help="Only inspect Neon schema and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan without writing (default).")
    parser.add_argument("--apply", action="store_true", help="Write planned rows to Neon inside a transaction.")
    parser.add_argument("--confirm-database", help="Must match the connected Neon database name when using --apply.")
    parser.add_argument("--use-owner", action="store_true", help="Use NEON_OWNER_URL instead of ssks_svc (read checks only recommended).")
    parser.add_argument("--report-file", type=Path, default=None, help="Optional path to write JSON summary report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        sc, plan = asyncio.run(
            run_import(
                export_dir=args.export_dir,
                mapped_dir=args.mapped_dir,
                env_file=args.env_file,
                schema=args.schema,
                check_schema_only=args.check_schema_only,
                apply=args.apply,
                confirm_database=args.confirm_database,
                use_owner=args.use_owner,
            )
        )
    except Exception as exc:
        logger.error("Neon migration step stopped: %s", redact_dsn(exc))
        return 2

    if args.check_schema_only or plan is None:
        print(format_schema_report(sc))
        return 0 if sc.is_compatible else 1

    print(format_import_report(plan, applied=args.apply))
    if args.report_file:
        payload = {
            "database": sc.database,
            "schema": sc.schema,
            "schema_compatible": sc.is_compatible,
            "missing_tables": sc.missing_tables,
            "table_mismatches": sc.table_mismatches,
            "existing_counts": sc.existing_counts,
            "planned_inserts": {t: len(plan.inserts_by_table.get(t, [])) for t in NEON_IMPORT_ORDER},
            "already_present": dict(plan.already_present),
            "blocking": plan.blocking,
            "conflicts": plan.conflicts,
            "warnings": plan.warnings,
            "applied": args.apply,
            "applied_counts": plan.applied_counts,
        }
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return 1 if plan.has_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
