"""Generate deterministic UUIDv5 mappings and Neon-ready mapped CSVs from exported SSKS data."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.migration.common import (
    CANONICAL_ID_PATTERNS,
    DEFAULT_EXPORT_DIR,
    EXPECTED_NEON_V2_SCHEMA,
    LEGACY_PK_ALIAS_BY_TABLE,
    LEGACY_TABLES,
    TABLE_PRIMARY_KEYS,
    UUID_FK_ENTITY_MAP,
    UUID_PK_ENTITY_BY_TABLE,
    guard_output_dir,
    legacy_id_to_uuid,
    read_csv_rows,
    write_csv_rows,
)

logger = logging.getLogger("ssks.migration.uuid_mapping")


@dataclass
class MappingReport:
    export_dir: str
    output_dir: str
    mapped_dir: str
    conversion_counts: dict[str, int] = field(default_factory=dict)
    preserved_counts: dict[str, int] = field(default_factory=dict)
    table_row_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    files_written: dict[str, str] = field(default_factory=dict)


def _validate_uuid_or_none(value: str | None, context: str, errors: list[str]) -> str | None:
    if value is None:
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        errors.append(f"{context}: expected valid UUID or NULL, got {value!r}")
        return None


def generate_mapping_and_transformed_csvs(
    export_dir: Path,
    output_dir: Path | None = None,
    *,
    overwrite: bool = False,
) -> MappingReport:
    """Build deterministic UUIDv5 mappings, validate all references, and write Neon-ready CSVs."""
    target_root = guard_output_dir(output_dir or export_dir)
    mapped_dir = guard_output_dir(target_root / "mapped")
    mapping_csv_path = target_root / "uuid_mapping.csv"
    manifest_path = target_root / "mapping_manifest.json"

    if not overwrite:
        for check_path in [mapping_csv_path, manifest_path]:
            if check_path.exists():
                raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {check_path}")

    report = MappingReport(
        export_dir=str(export_dir),
        output_dir=str(target_root),
        mapped_dir=str(mapped_dir),
    )

    loaded_headers: dict[str, list[str]] = {}
    loaded_rows: dict[str, list[dict[str, str | None]]] = {}
    for table in LEGACY_TABLES:
        csv_path = export_dir / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing exported CSV file: {csv_path}")
        headers, rows = read_csv_rows(csv_path)
        loaded_headers[table] = headers
        loaded_rows[table] = rows
        report.table_row_counts[table] = len(rows)

    # Track legacy_id -> generated_uuid per entity type and enforce global UUID uniqueness.
    uuid_maps: dict[str, dict[str, str]] = {cfg[0]: {} for cfg in UUID_PK_ENTITY_BY_TABLE.values()}
    seen_uuids: dict[str, tuple[str, str]] = {}
    mapping_rows: list[dict[str, str]] = []

    for table, (entity_type, pk_col) in UUID_PK_ENTITY_BY_TABLE.items():
        legacy_col = LEGACY_PK_ALIAS_BY_TABLE.get(table)
        count = 0
        for idx, row in enumerate(loaded_rows[table], start=1):
            legacy_id = row.get(pk_col) or (row.get(legacy_col) if legacy_col else None)
            if not legacy_id:
                report.errors.append(f"{table} row {idx}: missing primary key {pk_col}")
                continue
            if legacy_id in uuid_maps[entity_type]:
                report.errors.append(f"{table}: duplicate legacy PK {legacy_id!r}")
                continue
            new_uuid = legacy_id_to_uuid(entity_type, legacy_id)
            if new_uuid in seen_uuids:
                prev_type, prev_id = seen_uuids[new_uuid]
                report.errors.append(
                    f"UUID collision for {new_uuid}: ({entity_type}, {legacy_id}) vs ({prev_type}, {prev_id})"
                )
                continue
            seen_uuids[new_uuid] = (entity_type, legacy_id)
            uuid_maps[entity_type][legacy_id] = new_uuid
            mapping_rows.append(
                {
                    "entity_type": entity_type,
                    "legacy_id": legacy_id,
                    "generated_uuid": new_uuid,
                }
            )
            count += 1
        report.conversion_counts[entity_type] = count

    # Collect preserved canonical ID sets and validate PK uniqueness and formats.
    canonical_sets: dict[str, set[str]] = {}
    for table, col in [
        ("domains", "domain_id"),
        ("skills", "skill_id"),
        ("roles", "role_id"),
    ]:
        seen_vals: set[str] = set()
        pattern = CANONICAL_ID_PATTERNS[col]
        for idx, row in enumerate(loaded_rows[table], start=1):
            val = row.get(col)
            if not val:
                report.errors.append(f"{table} row {idx}: missing {col}")
                continue
            if not pattern.match(val):
                report.errors.append(f"{table} row {idx}: unexpected {col} format {val!r}")
            if val in seen_vals:
                report.errors.append(f"{table}: duplicate {col} {val!r}")
            seen_vals.add(val)
        canonical_sets[f"{table}.{col}"] = seen_vals
        report.preserved_counts[f"{table}.{col}"] = len(seen_vals)

    # Check composite PK uniqueness on junction tables.
    for jtable in ("skill_domains", "role_domains"):
        pk_cols = TABLE_PRIMARY_KEYS[jtable]
        seen_pairs: set[tuple[str | None, ...]] = set()
        for idx, row in enumerate(loaded_rows[jtable], start=1):
            pair = tuple(row.get(c) for c in pk_cols)
            if any(v is None for v in pair):
                report.errors.append(f"{jtable} row {idx}: NULL in composite primary key {pair}")
            elif pair in seen_pairs:
                report.errors.append(f"{jtable} row {idx}: duplicate composite primary key {pair}")
            seen_pairs.add(pair)

    skill_ids = canonical_sets["skills.skill_id"]
    role_ids = canonical_sets["roles.role_id"]
    domain_ids = canonical_sets["domains.domain_id"]

    # Transform rows into Neon v2 column layout without altering original exported CSVs.
    transformed_tables: dict[str, tuple[list[str], list[dict[str, Any]]]] = {}
    for table in LEGACY_TABLES:
        v2_cols = [c.name for c in EXPECTED_NEON_V2_SCHEMA[table]]
        out_rows: list[dict[str, Any]] = []
        fk_uuid_specs = UUID_FK_ENTITY_MAP.get(table, [])
        pk_conv = UUID_PK_ENTITY_BY_TABLE.get(table)

        for idx, raw_row in enumerate(loaded_rows[table], start=1):
            new_row: dict[str, Any] = {}
            for col in v2_cols:
                if table == "candidate_entities" and col == "reviewed_by" and col not in raw_row:
                    new_row[col] = None
                else:
                    new_row[col] = raw_row.get(col)

            if pk_conv is not None:
                entity_type, pk_col = pk_conv
                legacy_col = LEGACY_PK_ALIAS_BY_TABLE.get(table)
                legacy_pk = raw_row.get(pk_col) or (raw_row.get(legacy_col) if legacy_col else None)
                if legacy_pk:
                    new_row[pk_col] = uuid_maps[entity_type][legacy_pk]

            for fk_col, ref_entity_type in fk_uuid_specs:
                legacy_fk = raw_row.get(fk_col)
                if legacy_fk is not None:
                    mapped_fk = uuid_maps[ref_entity_type].get(legacy_fk)
                    if mapped_fk is None:
                        report.errors.append(
                            f"{table} row {idx}: unresolved {fk_col}={legacy_fk!r} for {ref_entity_type}"
                        )
                    else:
                        new_row[fk_col] = mapped_fk

            # Validate preserved canonical FKs.
            if "skill_id" in new_row and new_row["skill_id"] not in skill_ids:
                report.errors.append(f"{table} row {idx}: unresolved skill_id={new_row['skill_id']!r}")
            if "role_id" in new_row and new_row["role_id"] not in role_ids:
                report.errors.append(f"{table} row {idx}: unresolved role_id={new_row['role_id']!r}")
            if "domain_id" in new_row and new_row["domain_id"] not in domain_ids:
                report.errors.append(f"{table} row {idx}: unresolved domain_id={new_row['domain_id']!r}")
            if "source_skill_id" in new_row and new_row["source_skill_id"] not in skill_ids:
                report.errors.append(f"{table} row {idx}: unresolved source_skill_id={new_row['source_skill_id']!r}")
            if "target_skill_id" in new_row and new_row["target_skill_id"] not in skill_ids:
                report.errors.append(f"{table} row {idx}: unresolved target_skill_id={new_row['target_skill_id']!r}")
            if (
                "source_skill_id" in new_row
                and "target_skill_id" in new_row
                and new_row["source_skill_id"] == new_row["target_skill_id"]
            ):
                report.errors.append(f"{table} row {idx}: self-referencing skill relationship")

            if table in ("skill_relationships", "candidate_entities") and new_row.get("reviewed_by") is not None:
                new_row["reviewed_by"] = _validate_uuid_or_none(
                    new_row["reviewed_by"], f"{table} row {idx} reviewed_by", report.errors
                )

            out_rows.append(new_row)

        transformed_tables[table] = (v2_cols, out_rows)

    if report.errors:
        raise ValueError("UUID mapping validation failed:\n  - " + "\n  - ".join(report.errors[:25]))

    sha_map = write_csv_rows(
        mapping_csv_path,
        ["entity_type", "legacy_id", "generated_uuid"],
        mapping_rows,
        overwrite=overwrite,
    )
    report.files_written["uuid_mapping.csv"] = sha_map

    for table, (cols, rows) in transformed_tables.items():
        out_path = mapped_dir / f"{table}.csv"
        sha = write_csv_rows(out_path, cols, rows, overwrite=overwrite)
        report.files_written[f"mapped/{table}.csv"] = sha

    manifest_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_dir": report.export_dir,
        "mapped_dir": report.mapped_dir,
        "conversion_counts": report.conversion_counts,
        "total_converted_ids": sum(report.conversion_counts.values()),
        "preserved_counts": report.preserved_counts,
        "table_row_counts": report.table_row_counts,
        "files_written": report.files_written,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")
    return report


def format_mapping_report(report: MappingReport) -> str:
    lines = [
        f"Export Directory : {report.export_dir}",
        f"UUID Mapping File: {Path(report.output_dir) / 'uuid_mapping.csv'}",
        f"Mapped CSV Dir   : {report.mapped_dir}",
        "",
        "Converted Legacy IDs -> Deterministic UUIDv5:",
    ]
    for entity_type, cnt in report.conversion_counts.items():
        lines.append(f"  {entity_type:30} {cnt:6}")
    lines.append(f"  {'TOTAL':30} {sum(report.conversion_counts.values()):6}")
    lines.append("")
    lines.append("Preserved Canonical / External Identifiers:")
    for key, cnt in report.preserved_counts.items():
        lines.append(f"  {key:30} {cnt:6}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR, help="Directory containing exported CSVs.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (defaults to --export-dir).")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing mapping and mapped CSVs.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        report = generate_mapping_and_transformed_csvs(
            args.export_dir,
            args.output_dir,
            overwrite=args.overwrite,
        )
    except Exception as exc:
        logger.error("UUID mapping failed: %s", exc)
        return 1
    print(format_mapping_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
