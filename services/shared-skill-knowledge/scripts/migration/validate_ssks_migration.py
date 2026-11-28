"""Validate post-migration data integrity between exported SSKS data and Neon v2."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

import asyncpg

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.migration.common import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_REVISION,
    DEFAULT_EXPORT_DIR,
    EMBEDDING_TEXT_METHOD,
    EXPECTED_EMBEDDING_DIMENSION,
    LEGACY_TABLES,
    NEON_IMPORT_ORDER,
    TABLE_PRIMARY_KEYS,
    UUID_PK_ENTITY_BY_TABLE,
    compute_text_hash,
    construct_embedding_text,
    get_neon_dsn,
    read_csv_rows,
    redact_dsn,
)

logger = logging.getLogger("ssks.migration.validate")


async def validate_neon_migration(
    *,
    export_dir: Path,
    env_file: Path | None = None,
    schema: str = "ssks",
    expected_embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> dict[str, Any]:
    """Run comprehensive integrity comparisons between exported SSKS CSVs and Neon ssks tables."""
    mapping_path = export_dir / "uuid_mapping.csv"
    if not mapping_path.exists():
        raise FileNotFoundError(f"Missing uuid_mapping.csv in {export_dir}")

    _, mapping_rows = read_csv_rows(mapping_path)
    source_rows: dict[str, list[dict[str, str | None]]] = {}
    for table in LEGACY_TABLES:
        csv_path = export_dir / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing exported CSV: {csv_path}")
        _, rows = read_csv_rows(csv_path)
        source_rows[table] = rows

    dsn = get_neon_dsn(env_file)
    try:
        conn = await asyncpg.connect(dsn, timeout=12)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Neon: {redact_dsn(exc)}") from None

    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    try:
        db_name = await conn.fetchval("SELECT current_database()")

        # 1. Row counts per table
        neon_counts: dict[str, int] = {}
        for table in NEON_IMPORT_ORDER:
            neon_counts[table] = int(await conn.fetchval(f'SELECT count(*) FROM "{schema}"."{table}"'))

        for table in LEGACY_TABLES:
            src_cnt = len(source_rows[table])
            dst_cnt = neon_counts[table]
            record(f"row_count:{table}", src_cnt == dst_cnt, f"source={src_cnt}, neon={dst_cnt}")

        # 2. Primary key uniqueness in Neon
        for table in NEON_IMPORT_ORDER:
            pk_cols = ", ".join(f'"{c}"' for c in TABLE_PRIMARY_KEYS[table])
            dup_cnt = int(
                await conn.fetchval(
                    f'SELECT count(*) FROM (SELECT 1 FROM "{schema}"."{table}" GROUP BY {pk_cols} HAVING count(*) > 1) t'
                )
            )
            record(f"pk_unique:{table}", dup_cnt == 0, f"duplicate_groups={dup_cnt}")

        # 3. Foreign-key integrity inside Neon ssks
        fk_queries = {
            "skill_domains.skill_id": f'SELECT count(*) FROM "{schema}".skill_domains c LEFT JOIN "{schema}".skills p ON p.skill_id = c.skill_id WHERE p.skill_id IS NULL',
            "skill_domains.domain_id": f'SELECT count(*) FROM "{schema}".skill_domains c LEFT JOIN "{schema}".domains p ON p.domain_id = c.domain_id WHERE p.domain_id IS NULL',
            "role_domains.role_id": f'SELECT count(*) FROM "{schema}".role_domains c LEFT JOIN "{schema}".roles p ON p.role_id = c.role_id WHERE p.role_id IS NULL',
            "role_domains.domain_id": f'SELECT count(*) FROM "{schema}".role_domains c LEFT JOIN "{schema}".domains p ON p.domain_id = c.domain_id WHERE p.domain_id IS NULL',
            "skill_aliases.skill_id": f'SELECT count(*) FROM "{schema}".skill_aliases c LEFT JOIN "{schema}".skills p ON p.skill_id = c.skill_id WHERE p.skill_id IS NULL',
            "skill_aliases.source_id": f'SELECT count(*) FROM "{schema}".skill_aliases c LEFT JOIN "{schema}".knowledge_sources p ON p.source_id = c.source_id WHERE c.source_id IS NOT NULL AND p.source_id IS NULL',
            "role_aliases.role_id": f'SELECT count(*) FROM "{schema}".role_aliases c LEFT JOIN "{schema}".roles p ON p.role_id = c.role_id WHERE p.role_id IS NULL',
            "role_aliases.source_id": f'SELECT count(*) FROM "{schema}".role_aliases c LEFT JOIN "{schema}".knowledge_sources p ON p.source_id = c.source_id WHERE c.source_id IS NOT NULL AND p.source_id IS NULL',
            "skill_relationships.source_skill_id": f'SELECT count(*) FROM "{schema}".skill_relationships c LEFT JOIN "{schema}".skills p ON p.skill_id = c.source_skill_id WHERE p.skill_id IS NULL',
            "skill_relationships.target_skill_id": f'SELECT count(*) FROM "{schema}".skill_relationships c LEFT JOIN "{schema}".skills p ON p.skill_id = c.target_skill_id WHERE p.skill_id IS NULL',
            "skill_relationships.source_id": f'SELECT count(*) FROM "{schema}".skill_relationships c LEFT JOIN "{schema}".knowledge_sources p ON p.source_id = c.source_id WHERE c.source_id IS NOT NULL AND p.source_id IS NULL',
            "candidate_skill_relationships.source_skill_id": f'SELECT count(*) FROM "{schema}".candidate_skill_relationships c LEFT JOIN "{schema}".skills p ON p.skill_id = c.source_skill_id WHERE p.skill_id IS NULL',
            "candidate_skill_relationships.target_skill_id": f'SELECT count(*) FROM "{schema}".candidate_skill_relationships c LEFT JOIN "{schema}".skills p ON p.skill_id = c.target_skill_id WHERE p.skill_id IS NULL',
            "candidate_skill_relationships.source_id": f'SELECT count(*) FROM "{schema}".candidate_skill_relationships c LEFT JOIN "{schema}".knowledge_sources p ON p.source_id = c.source_id WHERE c.source_id IS NOT NULL AND p.source_id IS NULL',
            "candidate_skill_relationships.canonical_relationship_id": f'SELECT count(*) FROM "{schema}".candidate_skill_relationships c LEFT JOIN "{schema}".skill_relationships p ON p.relationship_id = c.canonical_relationship_id WHERE c.canonical_relationship_id IS NOT NULL AND p.relationship_id IS NULL',
            "skill_external_ids.skill_id": f'SELECT count(*) FROM "{schema}".skill_external_ids c LEFT JOIN "{schema}".skills p ON p.skill_id = c.skill_id WHERE p.skill_id IS NULL',
            "skill_external_ids.source_id": f'SELECT count(*) FROM "{schema}".skill_external_ids c LEFT JOIN "{schema}".knowledge_sources p ON p.source_id = c.source_id WHERE p.source_id IS NULL',
            "role_external_ids.role_id": f'SELECT count(*) FROM "{schema}".role_external_ids c LEFT JOIN "{schema}".roles p ON p.role_id = c.role_id WHERE p.role_id IS NULL',
            "role_external_ids.source_id": f'SELECT count(*) FROM "{schema}".role_external_ids c LEFT JOIN "{schema}".knowledge_sources p ON p.source_id = c.source_id WHERE p.source_id IS NULL',
            "skill_embeddings.skill_id": f'SELECT count(*) FROM "{schema}".skill_embeddings c LEFT JOIN "{schema}".skills p ON p.skill_id = c.skill_id WHERE p.skill_id IS NULL',
        }
        for fk_name, sql in fk_queries.items():
            orphans = int(await conn.fetchval(sql))
            record(f"fk_integrity:{fk_name}", orphans == 0, f"orphans={orphans}")

        # 4. UUID mapping completeness against Neon tables
        map_by_type: dict[str, dict[str, str]] = {}
        for row in mapping_rows:
            map_by_type.setdefault(row["entity_type"], {})[row["legacy_id"]] = row["generated_uuid"]

        for table, (etype, pk_col) in UUID_PK_ENTITY_BY_TABLE.items():
            neon_ids = {
                str(r[0]) for r in await conn.fetch(f'SELECT "{pk_col}" FROM "{schema}"."{table}"')
            }
            expected_uuids = set(map_by_type.get(etype, {}).values())
            record(
                f"uuid_mapping:{table}",
                neon_ids == expected_uuids,
                f"expected={len(expected_uuids)}, neon={len(neon_ids)}, missing={len(expected_uuids - neon_ids)}",
            )

        # 5. Canonical skill, role, and domain ID preservation
        for table, col in [
            ("skills", "skill_id"),
            ("roles", "role_id"),
            ("domains", "domain_id"),
        ]:
            src_ids = {r[col] for r in source_rows[table]}
            dst_ids = {r[0] for r in await conn.fetch(f'SELECT "{col}" FROM "{schema}"."{table}"')}
            record(
                f"canonical_ids:{table}.{col}",
                src_ids == dst_ids,
                f"source={len(src_ids)}, neon={len(dst_ids)}, diff={len(src_ids ^ dst_ids)}",
            )

        # 5b. External ID data preservation (UUID PK + parent entity + source + external_identifier)
        source_uuid_map = map_by_type.get("knowledge_source", {})
        for table, entity_col, ext_type in [
            ("skill_external_ids", "skill_id", "skill_external_id"),
            ("role_external_ids", "role_id", "role_external_id"),
        ]:
            ext_uuid_map = map_by_type.get(ext_type, {})
            src_records = {
                (
                    ext_uuid_map[r.get("external_id") or r["external_id_id"]],
                    r[entity_col],
                    source_uuid_map[r["source_id"]],
                    r["external_identifier"],
                )
                for r in source_rows[table]
            }
            dst_records = {
                (
                    str(r["external_id"]),
                    r[entity_col],
                    str(r["source_id"]),
                    r["external_identifier"],
                )
                for r in await conn.fetch(
                    f'SELECT external_id, "{entity_col}", source_id, external_identifier FROM "{schema}"."{table}"'
                )
            }
            record(
                f"external_id_records:{table}",
                src_records == dst_records,
                f"matched={len(src_records & dst_records)}/{len(src_records)}",
            )

        # 6. Relationship directionality preservation
        rel_uuid_map = map_by_type.get("skill_relationship", {})
        src_edges = {
            rel_uuid_map[r["relationship_id"]]: (r["source_skill_id"], r["target_skill_id"], r["relationship_type"])
            for r in source_rows["skill_relationships"]
        }
        dst_edges = {
            str(r["relationship_id"]): (r["source_skill_id"], r["target_skill_id"], r["relationship_type"])
            for r in await conn.fetch(
                f'SELECT relationship_id, source_skill_id, target_skill_id, relationship_type FROM "{schema}".skill_relationships'
            )
        }
        record(
            "relationship_directionality",
            src_edges == dst_edges,
            f"matched={sum(1 for k, v in src_edges.items() if dst_edges.get(k) == v)}/{len(src_edges)}",
        )

        # 6b. Approved candidate relationship canonical links
        cand_rel_map = map_by_type.get("candidate_skill_relationship", {})
        expected_approved_links = {
            cand_rel_map[r["candidate_relationship_id"]]: rel_uuid_map[r["canonical_relationship_id"]]
            for r in source_rows["candidate_skill_relationships"]
            if r["canonical_relationship_id"] is not None
        }
        actual_approved_links = {
            str(r["candidate_relationship_id"]): str(r["canonical_relationship_id"])
            for r in await conn.fetch(
                f'SELECT candidate_relationship_id, canonical_relationship_id FROM "{schema}".candidate_skill_relationships WHERE canonical_relationship_id IS NOT NULL'
            )
        }
        record(
            "approved_candidate_relationship_links",
            expected_approved_links == actual_approved_links,
            f"matched={sum(1 for k, v in expected_approved_links.items() if actual_approved_links.get(k) == v)}/{len(expected_approved_links)}",
        )

        # 6c. Unexpected duplicate checks across natural keys
        dup_domains_code = int(await conn.fetchval(f'SELECT count(*) FROM (SELECT 1 FROM "{schema}".domains GROUP BY code HAVING count(*) > 1) t'))
        dup_sources_code = int(await conn.fetchval(f'SELECT count(*) FROM (SELECT 1 FROM "{schema}".knowledge_sources GROUP BY source_code HAVING count(*) > 1) t'))
        dup_rel_dir = int(await conn.fetchval(f'SELECT count(*) FROM (SELECT 1 FROM "{schema}".skill_relationships GROUP BY source_skill_id, target_skill_id, relationship_type HAVING count(*) > 1) t'))
        dup_skill_alias = int(await conn.fetchval(f'SELECT count(*) FROM (SELECT 1 FROM "{schema}".skill_aliases GROUP BY skill_id, normalized_alias HAVING count(*) > 1) t'))
        dup_role_alias = int(await conn.fetchval(f'SELECT count(*) FROM (SELECT 1 FROM "{schema}".role_aliases GROUP BY role_id, normalized_alias HAVING count(*) > 1) t'))
        total_nat_dups = dup_domains_code + dup_sources_code + dup_rel_dir + dup_skill_alias + dup_role_alias
        record(
            "no_unexpected_duplicates",
            total_nat_dups == 0,
            f"domains.code={dup_domains_code}, sources.code={dup_sources_code}, rel_dir={dup_rel_dir}, skill_alias={dup_skill_alias}, role_alias={dup_role_alias}",
        )

        # 7. Skill embeddings validation (384-dim + model + hash coverage)
        emb_rows = await conn.fetch(
            f"""
            SELECT e.skill_id, e.embedding_model, e.embedding_dimension, e.embedding_text_hash,
                   vector_dims(e.embedding) AS actual_dims, s.preferred_name, s.description
            FROM "{schema}".skill_embeddings e
            JOIN "{schema}".skills s ON s.skill_id = e.skill_id
            WHERE e.embedding_model = $1
            """,
            expected_embedding_model,
        )
        skill_count = neon_counts["skills"]
        bad_dims = sum(
            1
            for r in emb_rows
            if r["embedding_dimension"] != EXPECTED_EMBEDDING_DIMENSION or r["actual_dims"] != EXPECTED_EMBEDDING_DIMENSION
        )
        stale_hashes = sum(
            1
            for r in emb_rows
            if compute_text_hash(construct_embedding_text(r["preferred_name"], r["description"]))
            != r["embedding_text_hash"]
        )
        record(
            "skill_embeddings_coverage",
            len(emb_rows) == skill_count and bad_dims == 0 and stale_hashes == 0,
            f"embeddings={len(emb_rows)}/{skill_count}, model={expected_embedding_model}, bad_dims={bad_dims}, stale_hashes={stale_hashes}",
        )

        passed = sum(1 for c in checks if c["passed"])
        return {
            "database": db_name,
            "schema": schema,
            "embedding_metadata": {
                "model_id": expected_embedding_model,
                "model_revision": DEFAULT_EMBEDDING_REVISION,
                "dimension": EXPECTED_EMBEDDING_DIMENSION,
                "normalize_embeddings": True,
                "text_generation_method": EMBEDDING_TEXT_METHOD,
            },
            "source_counts": {t: len(source_rows[t]) for t in LEGACY_TABLES},
            "neon_counts": neon_counts,
            "checks": checks,
            "passed": passed,
            "failed": len(checks) - passed,
        }
    finally:
        await conn.close()


def format_validation_report(report: dict[str, Any]) -> str:
    lines = [
        f"Database : {report['database']} (schema: {report['schema']})",
        f"Checks   : {report['passed']} passed, {report['failed']} failed",
        "",
    ]
    for item in report["checks"]:
        tag = "PASS" if item["passed"] else "FAIL"
        lines.append(f"  [{tag}] {item['check']:52} ({item['detail']})")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--schema", default="ssks")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--report-file", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        report = asyncio.run(
            validate_neon_migration(
                export_dir=args.export_dir,
                env_file=args.env_file,
                schema=args.schema,
                expected_embedding_model=args.embedding_model,
            )
        )
    except Exception as exc:
        logger.error("Validation failed: %s", redact_dsn(exc))
        return 2

    print(format_validation_report(report))
    if args.report_file:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
