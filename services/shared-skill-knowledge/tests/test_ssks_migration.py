import tempfile
import unittest
import uuid
from pathlib import Path

from scripts.migration.common import (
    DEFAULT_EXPORT_DIR,
    LEGACY_NEON_SEED_DIR,
    PROTECTED_IMPORT_READY_DIR,
    decode_csv_value,
    encode_csv_value,
    guard_output_dir,
    legacy_id_to_uuid,
    read_csv_rows,
    redact_dsn,
    write_csv_rows,
)
from scripts.migration.generate_uuid_mapping import generate_mapping_and_transformed_csvs
from scripts.migration.import_ssks_neon import load_mapped_dataset


class MigrationHelpersTests(unittest.TestCase):
    def test_deterministic_uuidv5_and_distinct_entity_prefixes(self):
        u1 = legacy_id_to_uuid("skill_alias", "AL-000100")
        u2 = legacy_id_to_uuid("skill_alias", "AL-000100")
        u3 = legacy_id_to_uuid("role_alias", "AL-000100")
        self.assertEqual(u1, u2)
        self.assertNotEqual(u1, u3)

    def test_protected_directories_cannot_be_written(self):
        with self.assertRaises(PermissionError):
            guard_output_dir(PROTECTED_IMPORT_READY_DIR)
        with self.assertRaises(PermissionError):
            guard_output_dir(PROTECTED_IMPORT_READY_DIR / "nested")
        with self.assertRaises(PermissionError):
            guard_output_dir(LEGACY_NEON_SEED_DIR)

    def test_csv_null_marker_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            write_csv_rows(
                path,
                ["id", "note"],
                [{"id": "1", "note": None}, {"id": "2", "note": ""}, {"id": "3", "note": "ok"}],
            )
            headers, rows = read_csv_rows(path)
            self.assertEqual(headers, ["id", "note"])
            self.assertIsNone(rows[0]["note"])
            self.assertEqual(rows[1]["note"], "")
            self.assertEqual(rows[2]["note"], "ok")

    def test_encode_rejects_null_sentinel_collision(self):
        with self.assertRaises(ValueError):
            encode_csv_value("\\N")
        self.assertIsNone(decode_csv_value("\\N"))

    def test_dsn_redaction_hides_password(self):
        scrubbed = redact_dsn("postgresql://ssks_svc:super_secret_pw@db.neon.tech/skillaro?sslmode=require")
        self.assertNotIn("super_secret_pw", scrubbed)
        self.assertIn("ssks_svc:***@", scrubbed)

    def test_uuid_mapping_end_to_end_on_synthetic_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            exp = Path(tmp) / "export"
            exp.mkdir()
            datasets = {
                "domains": (["domain_id", "name", "code", "description", "status"], [{"domain_id": "DOM-IT", "name": "IT", "code": "IT", "description": None, "status": "ACTIVE"}]),
                "knowledge_sources": (["source_id", "source_code", "source_name", "source_version", "last_synced_at"], [{"source_id": "SRC-ESCO", "source_code": "ESCO", "source_name": "ESCO", "source_version": "1.2.1", "last_synced_at": None}]),
                "skills": (["skill_id", "preferred_name", "description", "skill_type", "status", "created_at", "updated_at", "skill_nature"], [
                    {"skill_id": "SK-000001", "preferred_name": "Python", "description": None, "skill_type": "PROGRAMMING_LANGUAGE", "status": "ACTIVE", "created_at": "2026-10-17T00:00:00+00:00", "updated_at": "2026-10-17T00:00:00+00:00", "skill_nature": "TECHNICAL"},
                    {"skill_id": "SK-000002", "preferred_name": "FastAPI", "description": "Web framework", "skill_type": "SOFTWARE_OR_TOOL", "status": "ACTIVE", "created_at": "2026-10-17T00:00:00+00:00", "updated_at": "2026-10-17T00:00:00+00:00", "skill_nature": "TECHNICAL"},
                ]),
                "roles": (["role_id", "preferred_name", "description", "status", "created_at", "updated_at"], [{"role_id": "RL-000001", "preferred_name": "Backend Engineer", "description": None, "status": "ACTIVE", "created_at": "2026-10-17T00:00:00+00:00", "updated_at": "2026-10-17T00:00:00+00:00"}]),
                "skill_domains": (["skill_id", "domain_id"], [{"skill_id": "SK-000001", "domain_id": "DOM-IT"}]),
                "role_domains": (["role_id", "domain_id"], [{"role_id": "RL-000001", "domain_id": "DOM-IT"}]),
                "skill_aliases": (["alias_id", "skill_id", "alias_text", "normalized_alias", "source_id", "verification_status"], [{"alias_id": "AL-000100", "skill_id": "SK-000001", "alias_text": "Py", "normalized_alias": "py", "source_id": "SRC-ESCO", "verification_status": "VERIFIED"}]),
                "role_aliases": (["alias_id", "role_id", "alias_text", "normalized_alias", "source_id", "verification_status"], [{"alias_id": "AL-000100", "role_id": "RL-000001", "alias_text": "BE", "normalized_alias": "be", "source_id": None, "verification_status": "VERIFIED"}]),
                "skill_relationships": (["relationship_id", "source_skill_id", "target_skill_id", "relationship_type", "verification_status", "source_id", "evidence_note", "created_at", "updated_at", "evidence_description", "evidence_url", "reviewed_by"], [{"relationship_id": "REL-000028", "source_skill_id": "SK-000002", "target_skill_id": "SK-000001", "relationship_type": "PART_OF", "verification_status": "VERIFIED", "source_id": "SRC-ESCO", "evidence_note": "note", "created_at": "2026-10-17T00:00:00+00:00", "updated_at": "2026-10-17T00:00:00+00:00", "evidence_description": None, "evidence_url": None, "reviewed_by": "e36ff966-a815-4cd1-a9a9-2cdfbf3faf1f"}]),
                "candidate_entities": (["candidate_entity_id", "entity_type", "submitted_name", "normalized_name", "description", "proposed_skill_type", "proposed_skill_nature", "source_component", "source_reference", "review_status", "review_note", "matched_entity_id", "created_at", "reviewed_at"], []),
                "candidate_skill_relationships": (["candidate_relationship_id", "source_skill_id", "target_skill_id", "proposed_relationship_type", "confidence_score", "review_status", "source_id", "review_note", "created_at", "reviewed_at", "evidence_description", "evidence_url", "reviewed_by", "canonical_relationship_id"], [{"candidate_relationship_id": "CR-000009", "source_skill_id": "SK-000002", "target_skill_id": "SK-000001", "proposed_relationship_type": "PART_OF", "confidence_score": 0.9, "review_status": "APPROVED", "source_id": "SRC-ESCO", "review_note": None, "created_at": "2026-10-17T00:00:00+00:00", "reviewed_at": None, "evidence_description": None, "evidence_url": None, "reviewed_by": "reviewer", "canonical_relationship_id": "REL-000028"}]),
                "skill_external_ids": (["external_id_id", "skill_id", "source_id", "external_identifier"], [{"external_id_id": "EXT-000001", "skill_id": "SK-000001", "source_id": "SRC-ESCO", "external_identifier": "esco-1"}]),
                "role_external_ids": (["external_id_id", "role_id", "source_id", "external_identifier"], [{"external_id_id": "EXT-000002", "role_id": "RL-000001", "source_id": "SRC-ESCO", "external_identifier": "esco-r1"}]),
            }
            for tbl, (cols, rows) in datasets.items():
                write_csv_rows(exp / f"{tbl}.csv", cols, rows)

            report = generate_mapping_and_transformed_csvs(exp)
            self.assertEqual(report.conversion_counts["skill_alias"], 1)
            self.assertEqual(report.conversion_counts["role_alias"], 1)
            self.assertEqual(report.conversion_counts["skill_external_id"], 1)
            self.assertEqual(report.conversion_counts["role_external_id"], 1)
            self.assertEqual(report.conversion_counts["candidate_entity"], 0)

            rows_by_table, blocking, _ = load_mapped_dataset(exp)
            self.assertEqual(blocking, [])
            self.assertNotEqual(
                rows_by_table["skill_aliases"][0]["alias_id"],
                rows_by_table["role_aliases"][0]["alias_id"],
            )
            self.assertEqual(
                rows_by_table["candidate_skill_relationships"][0]["canonical_relationship_id"],
                rows_by_table["skill_relationships"][0]["relationship_id"],
            )
            self.assertEqual(
                str(rows_by_table["skill_external_ids"][0]["external_id"]),
                legacy_id_to_uuid("skill_external_id", "EXT-000001"),
            )
            self.assertEqual(
                str(rows_by_table["role_external_ids"][0]["external_id"]),
                legacy_id_to_uuid("role_external_id", "EXT-000002"),
            )
            self.assertIsInstance(rows_by_table["skill_external_ids"][0]["external_id"], uuid.UUID)

    def test_current_export_and_mapped_dataset_loads_cleanly(self):
        if not (DEFAULT_EXPORT_DIR / "uuid_mapping.csv").exists():
            self.skipTest("Current export not generated")
        rows_by_table, blocking, _ = load_mapped_dataset(DEFAULT_EXPORT_DIR)
        self.assertEqual(blocking, [])
        self.assertEqual(len(rows_by_table["skills"]), 1847)
        self.assertEqual(len(rows_by_table["roles"]), 94)
        self.assertEqual(len(rows_by_table["domains"]), 3)
        self.assertEqual(len(rows_by_table["role_domains"]), 93)
        self.assertEqual(len(rows_by_table["candidate_entities"]), 0)
        self.assertEqual(len(rows_by_table["skill_relationships"]), 25)
        self.assertEqual(len(rows_by_table["candidate_skill_relationships"]), 12)
        self.assertEqual(len(rows_by_table["skill_external_ids"]), 1842)
        self.assertEqual(len(rows_by_table["role_external_ids"]), 35)


class ExternalIdMigrationPostgresTests(unittest.IsolatedAsyncioTestCase):
    """Verify in-place DDL, rollback preservation, and data preservation on a throwaway Postgres DB."""

    async def asyncSetUp(self):
        import asyncpg
        from scripts.migration.common import get_source_dsn

        try:
            base_dsn = get_source_dsn()
            admin_dsn = base_dsn.rsplit("/", 1)[0] + "/postgres"
            self.admin = await asyncpg.connect(admin_dsn, timeout=3)
        except Exception as exc:
            self.skipTest(f"Local Postgres unavailable for rollback test: {exc}")

        self.db_name = f"ssks_ext_test_{uuid.uuid4().hex[:8]}"
        await self.admin.execute(f'CREATE DATABASE "{self.db_name}"')
        test_dsn = base_dsn.rsplit("/", 1)[0] + f"/{self.db_name}"
        self.conn = await asyncpg.connect(test_dsn, timeout=5)
        await self.conn.execute("CREATE SCHEMA ssks")
        await self.conn.execute(
            """
            CREATE TABLE ssks.skills (skill_id varchar(50) PRIMARY KEY);
            CREATE TABLE ssks.roles (role_id varchar(50) PRIMARY KEY);
            CREATE TABLE ssks.knowledge_sources (source_id uuid PRIMARY KEY);
            CREATE TABLE ssks.skill_external_ids (
                external_id_id varchar(50) NOT NULL,
                skill_id varchar(50) NOT NULL REFERENCES ssks.skills(skill_id),
                source_id uuid NOT NULL REFERENCES ssks.knowledge_sources(source_id),
                external_identifier varchar(255) NOT NULL,
                CONSTRAINT pk_skill_external_ids PRIMARY KEY (external_id_id)
            );
            CREATE TABLE ssks.role_external_ids (
                external_id_id varchar(50) NOT NULL,
                role_id varchar(50) NOT NULL REFERENCES ssks.roles(role_id),
                source_id uuid NOT NULL REFERENCES ssks.knowledge_sources(source_id),
                external_identifier varchar(255) NOT NULL,
                CONSTRAINT pk_role_external_ids PRIMARY KEY (external_id_id)
            );
            """
        )
        src_id = uuid.uuid4()
        await self.conn.execute("INSERT INTO ssks.skills VALUES ('SK-000001')")
        await self.conn.execute("INSERT INTO ssks.roles VALUES ('RL-000001')")
        await self.conn.execute("INSERT INTO ssks.knowledge_sources VALUES ($1)", src_id)
        await self.conn.execute(
            "INSERT INTO ssks.skill_external_ids VALUES ('EXT-000036', 'SK-000001', $1, 'esco:sk:1')",
            src_id,
        )
        await self.conn.execute(
            "INSERT INTO ssks.role_external_ids VALUES ('EXT-000001', 'RL-000001', $1, 'esco:rl:1')",
            src_id,
        )

    async def asyncTearDown(self):
        if getattr(self, "conn", None):
            await self.conn.close()
        if getattr(self, "admin", None):
            await self.admin.execute(f'DROP DATABASE IF EXISTS "{self.db_name}" WITH (FORCE)')
            await self.admin.close()

    async def test_rollback_preserves_original_tables_on_failure(self):
        from scripts.migration.migrate_external_ids_uuid import (
            apply_external_id_migration,
            build_migration_plans,
        )

        plans = await build_migration_plans(self.conn, schema="ssks")
        with self.assertRaises(RuntimeError):
            await apply_external_id_migration(
                self.conn, plans, schema="ssks", simulate_failure_after_first=True
            )

        for tbl in ("skill_external_ids", "role_external_ids"):
            cols = [
                r["column_name"]
                for r in await self.conn.fetch(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='ssks' AND table_name=$1 ORDER BY ordinal_position",
                    tbl,
                )
            ]
            self.assertIn("external_id_id", cols)
            self.assertNotIn("external_id", cols)

        sk_row = await self.conn.fetchrow("SELECT * FROM ssks.skill_external_ids")
        rl_row = await self.conn.fetchrow("SELECT * FROM ssks.role_external_ids")
        self.assertEqual(sk_row["external_id_id"], "EXT-000036")
        self.assertEqual(rl_row["external_id_id"], "EXT-000001")

    async def test_transactional_migration_converts_both_tables_and_preserves_data(self):
        from scripts.migration.migrate_external_ids_uuid import (
            apply_external_id_migration,
            build_migration_plans,
        )

        plans = await build_migration_plans(self.conn, schema="ssks")
        res = await apply_external_id_migration(self.conn, plans, schema="ssks")
        self.assertEqual(res["status"], "committed")
        self.assertEqual(res["rows_updated"], 2)

        sk_row = await self.conn.fetchrow("SELECT * FROM ssks.skill_external_ids")
        rl_row = await self.conn.fetchrow("SELECT * FROM ssks.role_external_ids")
        self.assertEqual(str(sk_row["external_id"]), legacy_id_to_uuid("skill_external_id", "EXT-000036"))
        self.assertEqual(str(rl_row["external_id"]), legacy_id_to_uuid("role_external_id", "EXT-000001"))
        self.assertEqual(sk_row["external_identifier"], "esco:sk:1")
        self.assertEqual(rl_row["external_identifier"], "esco:rl:1")

        # Rebuilding plans afterwards reports already_migrated=True.
        post_plans = await build_migration_plans(self.conn, schema="ssks")
        self.assertTrue(all(p.already_migrated for p in post_plans))


if __name__ == "__main__":
    unittest.main()
