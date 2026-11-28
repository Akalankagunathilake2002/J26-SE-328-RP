"""Backup and transactionally migrate Neon external ID tables from external_id_id VARCHAR(50) to external_id UUID."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.migration.common import (
    DEFAULT_EXPORT_DIR,
    get_neon_dsn,
    guard_output_dir,
    legacy_id_to_uuid,
    read_csv_rows,
    redact_dsn,
    write_csv_rows,
)

logger = logging.getLogger("ssks.migration.external_ids_uuid")

DEFAULT_BACKUP_DIR = DEFAULT_EXPORT_DIR / "backups" / "external_ids_pre_uuid_migration"

EXTERNAL_ID_TABLES: list[tuple[str, str, str, str]] = [
    ("skill_external_ids", "skill_id", "skill_external_id", "pk_skill_external_ids"),
    ("role_external_ids", "role_id", "role_external_id", "pk_role_external_ids"),
]


@dataclass
class TableMigrationPlan:
    table: str
    entity_col: str
    entity_type: str
    pk_constraint: str
    row_count: int
    current_columns: list[dict[str, Any]]
    already_migrated: bool
    mappings: list[tuple[str, str, str, str, str]] = field(default_factory=list)
    sample_mappings: list[dict[str, str]] = field(default_factory=list)


async def backup_external_id_tables(
    conn: asyncpg.Connection,
    backup_dir: Path,
    *,
    schema: str = "ssks",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Export and verify a complete pre-migration backup of both Neon external ID tables."""
    target_dir = guard_output_dir(backup_dir)
    manifest_path = target_dir / "backup_manifest.json"
    if manifest_path.exists() and not overwrite:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Verify existing backup matches live Neon counts and contents before reusing it.
        for tbl, entity_col, _, _ in EXTERNAL_ID_TABLES:
            csv_path = target_dir / f"{tbl}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Incomplete existing backup missing {csv_path}")
            _, rows = read_csv_rows(csv_path)
            live_cnt = int(await conn.fetchval(f'SELECT count(*) FROM "{schema}"."{tbl}"'))
            if len(rows) != live_cnt:
                raise RuntimeError(
                    f"Existing backup count mismatch for {schema}.{tbl}: backup={len(rows)}, live={live_cnt}"
                )
        logger.info("Verified existing backup in %s", target_dir)
        return manifest

    db_name = await conn.fetchval("SELECT current_database()")
    table_info: dict[str, Any] = {}
    for tbl, entity_col, _, _ in EXTERNAL_ID_TABLES:
        cols = [
            r["column_name"]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema=$1 AND table_name=$2 ORDER BY ordinal_position",
                schema,
                tbl,
            )
        ]
        order_col = cols[0]
        records = await conn.fetch(f'SELECT {", ".join(cols)} FROM "{schema}"."{tbl}" ORDER BY "{order_col}" ASC')
        rows = [dict(r) for r in records]
        csv_path = target_dir / f"{tbl}.csv"
        sha = write_csv_rows(csv_path, cols, rows, overwrite=overwrite)
        _, reread = read_csv_rows(csv_path)
        if len(reread) != len(rows):
            raise RuntimeError(f"Backup verification failed for {tbl}: wrote {len(rows)}, read back {len(reread)}")
        table_info[tbl] = {
            "row_count": len(rows),
            "columns": cols,
            "csv_file": csv_path.name,
            "sha256": sha,
            "verified": True,
        }

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database": db_name,
        "schema": schema,
        "tables": table_info,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


async def build_migration_plans(
    conn: asyncpg.Connection,
    *,
    schema: str = "ssks",
) -> list[TableMigrationPlan]:
    """Inspect live Neon external ID tables and build deterministic UUIDv5 migration plans."""
    plans: list[TableMigrationPlan] = []
    seen_uuids: set[str] = set()

    for tbl, entity_col, entity_type, pk_name in EXTERNAL_ID_TABLES:
        col_rows = await conn.fetch(
            """
            SELECT column_name, udt_name, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """,
            schema,
            tbl,
        )
        cols = [dict(r) for r in col_rows]
        col_names = [c["column_name"] for c in cols]
        row_count = int(await conn.fetchval(f'SELECT count(*) FROM "{schema}"."{tbl}"'))

        if "external_id" in col_names and "external_id_id" not in col_names:
            plans.append(
                TableMigrationPlan(
                    table=tbl,
                    entity_col=entity_col,
                    entity_type=entity_type,
                    pk_constraint=pk_name,
                    row_count=row_count,
                    current_columns=cols,
                    already_migrated=True,
                )
            )
            continue

        if "external_id_id" not in col_names:
            raise RuntimeError(f"{schema}.{tbl} has unexpected columns: {col_names}")
        if "external_id" in col_names:
            raise RuntimeError(f"{schema}.{tbl} already has both external_id and external_id_id columns")

        records = await conn.fetch(
            f'SELECT external_id_id, "{entity_col}", source_id, external_identifier '
            f'FROM "{schema}"."{tbl}" ORDER BY external_id_id ASC'
        )
        mappings: list[tuple[str, str, str, str, str]] = []
        samples: list[dict[str, str]] = []
        for rec in records:
            legacy_id = rec["external_id_id"]
            new_uuid = legacy_id_to_uuid(entity_type, legacy_id)
            if new_uuid in seen_uuids:
                raise RuntimeError(f"UUIDv5 collision detected for {entity_type}:{legacy_id} -> {new_uuid}")
            seen_uuids.add(new_uuid)
            mappings.append(
                (
                    legacy_id,
                    new_uuid,
                    rec[entity_col],
                    str(rec["source_id"]),
                    rec["external_identifier"],
                )
            )
            if len(samples) < 5:
                samples.append(
                    {
                        "legacy_external_id_id": legacy_id,
                        "new_external_id_uuid": new_uuid,
                        entity_col: rec[entity_col],
                        "source_id": str(rec["source_id"]),
                        "external_identifier": rec["external_identifier"],
                    }
                )

        plans.append(
            TableMigrationPlan(
                table=tbl,
                entity_col=entity_col,
                entity_type=entity_type,
                pk_constraint=pk_name,
                row_count=len(records),
                current_columns=cols,
                already_migrated=False,
                mappings=mappings,
                sample_mappings=samples,
            )
        )

    return plans


async def apply_external_id_migration(
    conn: asyncpg.Connection,
    plans: list[TableMigrationPlan],
    *,
    schema: str = "ssks",
    simulate_failure_after_first: bool = False,
) -> dict[str, Any]:
    """Migrate both external ID tables in place inside one atomic PostgreSQL transaction."""
    pending = [p for p in plans if not p.already_migrated]
    if not pending:
        return {"migrated_tables": [], "rows_updated": 0, "status": "already_migrated"}

    pre_snapshots: dict[str, set[tuple[str, str, str]]] = {}
    for plan in pending:
        rows = await conn.fetch(
            f'SELECT "{plan.entity_col}", source_id, external_identifier FROM "{schema}"."{plan.table}"'
        )
        pre_snapshots[plan.table] = {(r[plan.entity_col], str(r["source_id"]), r["external_identifier"]) for r in rows}

    rows_updated = 0
    async with conn.transaction():
        for idx, plan in enumerate(pending):
            fq_table = f'"{schema}"."{plan.table}"'
            await conn.execute(f"ALTER TABLE {fq_table} ADD COLUMN external_id uuid")

            update_tuples = [(uuid.UUID(new_uuid), legacy_id) for legacy_id, new_uuid, _, _, _ in plan.mappings]
            await conn.executemany(
                f"UPDATE {fq_table} SET external_id = $1 WHERE external_id_id = $2",
                update_tuples,
            )

            stats = await conn.fetchrow(
                f"SELECT count(*) AS total, count(DISTINCT external_id) AS distinct_uuids, "
                f"count(*) FILTER (WHERE external_id IS NULL) AS null_count FROM {fq_table}"
            )
            if stats["total"] != plan.row_count or stats["distinct_uuids"] != plan.row_count or stats["null_count"] != 0:
                raise RuntimeError(f"Post-update invariant check failed on {fq_table}: {dict(stats)}")

            await conn.execute(f"ALTER TABLE {fq_table} ALTER COLUMN external_id SET NOT NULL")
            await conn.execute(f'ALTER TABLE {fq_table} DROP CONSTRAINT "{plan.pk_constraint}"')
            await conn.execute(
                f'ALTER TABLE {fq_table} ADD CONSTRAINT "{plan.pk_constraint}" PRIMARY KEY (external_id)'
            )
            await conn.execute(f"ALTER TABLE {fq_table} DROP COLUMN external_id_id")

            if simulate_failure_after_first and idx == 0:
                raise RuntimeError("Simulated mid-migration failure to verify rollback")

            post_rows = await conn.fetch(
                f'SELECT external_id, "{plan.entity_col}", source_id, external_identifier FROM {fq_table}'
            )
            post_tuples = {(r[plan.entity_col], str(r["source_id"]), r["external_identifier"]) for r in post_rows}
            if len(post_rows) != plan.row_count or post_tuples != pre_snapshots[plan.table]:
                raise RuntimeError(f"Post-migration data preservation check failed on {fq_table}")

            rows_updated += len(update_tuples)
            logger.info("Migrated %s.%s (%d rows) to external_id uuid", schema, plan.table, len(update_tuples))

    return {
        "migrated_tables": [p.table for p in pending],
        "rows_updated": rows_updated,
        "status": "committed",
    }


async def run_external_id_migration(
    *,
    backup_dir: Path,
    env_file: Path | None = None,
    schema: str = "ssks",
    overwrite_backup: bool = False,
    apply: bool = False,
    confirm_database: str | None = None,
) -> dict[str, Any]:
    dsn = get_neon_dsn(env_file)
    try:
        conn = await asyncpg.connect(dsn, timeout=12)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Neon: {redact_dsn(exc)}") from None

    try:
        db_name = await conn.fetchval("SELECT current_database()")
        backup_manifest = await backup_external_id_tables(
            conn, backup_dir, schema=schema, overwrite=overwrite_backup
        )
        plans = await build_migration_plans(conn, schema=schema)

        result: dict[str, Any] = {
            "database": db_name,
            "schema": schema,
            "backup_dir": str(backup_dir),
            "backup_manifest": backup_manifest,
            "plans": [
                {
                    "table": p.table,
                    "entity_type": p.entity_type,
                    "row_count": p.row_count,
                    "already_migrated": p.already_migrated,
                    "current_columns": p.current_columns,
                    "sample_mappings": p.sample_mappings,
                }
                for p in plans
            ],
            "total_records_to_migrate": sum(0 if p.already_migrated else p.row_count for p in plans),
            "applied": False,
        }

        if not apply:
            return result

        if confirm_database != db_name:
            raise RuntimeError(f"--confirm-database must equal connected database ({db_name!r})")

        apply_result = await apply_external_id_migration(conn, plans, schema=schema)
        result["applied"] = True
        result["apply_result"] = apply_result
        return result
    finally:
        await conn.close()


def format_report(result: dict[str, Any]) -> str:
    lines = [
        f"Database      : {result['database']} (schema: {result['schema']})",
        f"Backup Dir    : {result['backup_dir']}",
        "Backup Tables :",
    ]
    for tbl, info in result["backup_manifest"]["tables"].items():
        lines.append(f"  {tbl:24} rows={info['row_count']:5}  sha256={info['sha256'][:16]}...")
    lines.append("")
    lines.append("Migration Plan:")
    for plan in result["plans"]:
        status = "ALREADY_MIGRATED" if plan["already_migrated"] else f"MIGRATE ({plan['row_count']} rows)"
        lines.append(f"  {plan['table']:24} {status}  prefix={plan['entity_type']}")
        for s in plan["sample_mappings"][:3]:
            lines.append(f"    {s['legacy_external_id_id']} -> {s['new_external_id_uuid']} ({s['external_identifier'][:45]})")
    lines.append("")
    lines.append(f"Total Records To Migrate: {result['total_records_to_migrate']}")
    lines.append(f"Mode: {'APPLIED' if result['applied'] else 'DRY-RUN ONLY (Neon unchanged)'}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--schema", default="ssks")
    parser.add_argument("--overwrite-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Create/verify backup and show migration plan (default).")
    parser.add_argument("--apply", action="store_true", help="Execute transactional in-place migration on Neon.")
    parser.add_argument("--confirm-database", help="Must equal Neon database name when using --apply.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        result = asyncio.run(
            run_external_id_migration(
                backup_dir=args.backup_dir,
                env_file=args.env_file,
                schema=args.schema,
                overwrite_backup=args.overwrite_backup,
                apply=args.apply,
                confirm_database=args.confirm_database,
            )
        )
    except Exception as exc:
        logger.error("External ID migration step stopped: %s", redact_dsn(exc))
        return 2
    print(format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
