"""Export all SSKS tables from the source ssks_db database to UTF-8 CSV files."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.migration.common import (
    DEFAULT_EXPORT_DIR,
    LEGACY_TABLES,
    TABLE_PRIMARY_KEYS,
    get_source_dsn,
    guard_output_dir,
    redact_dsn,
    write_csv_rows,
)

logger = logging.getLogger("ssks.migration.export")


async def fetch_table_columns(conn: asyncpg.Connection, schema: str, table: str) -> list[str]:
    rows = await conn.fetch(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
        """,
        schema,
        table,
    )
    return [r["column_name"] for r in rows]


async def export_from_connection(
    conn: asyncpg.Connection,
    output_dir: Path,
    *,
    schema: str = "public",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Export all 13 legacy SSKS tables in read-only mode and return an export summary."""
    guard_output_dir(output_dir)
    manifest_path = output_dir / "export_manifest.json"
    if manifest_path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing manifest without --overwrite: {manifest_path}")

    existing_tables = {
        r["table_name"]
        for r in await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = $1",
            schema,
        )
    }
    missing = [t for t in LEGACY_TABLES if t not in existing_tables]
    if missing:
        raise RuntimeError(f"Source schema {schema!r} is missing expected tables: {missing}")

    db_name = await conn.fetchval("SELECT current_database()")
    table_reports: dict[str, dict[str, Any]] = {}
    empty_tables: list[str] = []

    async with conn.transaction(readonly=True):
        for table in LEGACY_TABLES:
            columns = await fetch_table_columns(conn, schema, table)
            pk_cols = TABLE_PRIMARY_KEYS[table]
            order_clause = ", ".join(f'"{c}" ASC' for c in pk_cols)
            col_clause = ", ".join(f'"{c}"' for c in columns)
            records = await conn.fetch(f'SELECT {col_clause} FROM "{schema}"."{table}" ORDER BY {order_clause}')
            rows = [dict(rec) for rec in records]

            csv_path = output_dir / f"{table}.csv"
            sha256 = write_csv_rows(csv_path, columns, rows, overwrite=overwrite)
            if not rows:
                empty_tables.append(table)

            table_reports[table] = {
                "row_count": len(rows),
                "columns": columns,
                "csv_file": csv_path.name,
                "sha256": sha256,
            }
            logger.info("Exported %-30s %5d rows -> %s", table, len(rows), csv_path.name)

    manifest = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_database": db_name,
        "source_schema": schema,
        "output_directory": str(output_dir),
        "tables": table_reports,
        "empty_tables": empty_tables,
        "notes": [
            "skill_embeddings does not exist in legacy ssks_db and must be regenerated for Neon v2 (vector(384)).",
            "NULL values are encoded as \\N in UTF-8 CSVs to distinguish SQL NULL from empty strings.",
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


async def run_export(
    output_dir: Path,
    *,
    env_file: Path | None = None,
    schema: str = "public",
    overwrite: bool = False,
) -> dict[str, Any]:
    dsn = get_source_dsn(env_file)
    try:
        conn = await asyncpg.connect(dsn, timeout=10)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to source ssks_db: {redact_dsn(exc)}") from None
    try:
        return await export_from_connection(conn, output_dir, schema=schema, overwrite=overwrite)
    finally:
        await conn.close()


def format_export_report(manifest: dict[str, Any]) -> str:
    lines = [
        f"Source Database : {manifest['source_database']} (schema: {manifest['source_schema']})",
        f"Export Directory: {manifest['output_directory']}",
        f"Exported At     : {manifest['exported_at']}",
        "",
        "Exported Table Counts:",
    ]
    total_rows = 0
    for table, info in manifest["tables"].items():
        cnt = info["row_count"]
        total_rows += cnt
        marker = " (empty)" if cnt == 0 else ""
        lines.append(f"  {table:32} {cnt:6}{marker}")
    lines.append("")
    lines.append(f"Total Exported Rows: {total_rows}")
    lines.append(f"Empty Tables       : {manifest['empty_tables']}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPORT_DIR, help="Directory to write exported CSVs.")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional path to .env file.")
    parser.add_argument("--schema", default="public", help="Source schema in ssks_db (default: public).")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing files in output-dir.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        manifest = asyncio.run(
            run_export(args.output_dir, env_file=args.env_file, schema=args.schema, overwrite=args.overwrite)
        )
    except Exception as exc:
        logger.error("Export failed: %s", redact_dsn(exc))
        return 1
    print(format_export_report(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
