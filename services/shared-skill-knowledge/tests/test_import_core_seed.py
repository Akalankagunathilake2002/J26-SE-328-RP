import os
import unittest
import uuid

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from scripts.db_import.import_core_seed import (
    ImportBlocked, SeedData, Snapshot, apply_plan, load_seed, normalize_alias,
    plan_import, run_import, DEFAULT_SEED_DIR,
)

DOMAINS = {"IT": "DOM-IT", "HR": "DOM-HR", "BUSINESS": "DOM-BUS"}


def entity(id_, type_="SKILL", name="python", kind="PROGRAMMING_LANGUAGE", nature="TECHNICAL", status="APPROVED"):
    return {"id": id_, "entity_type": type_, "name": name, "description": "d", "skill_type": "",
            "concept_kind": kind if type_ == "SKILL" else "ROLE", "skill_nature": nature, "review_status": status}


def alias(id_, parent, value, verified="True"):
    return {"id": id_, "canonical_entity_id": parent, "record_type": "ALIAS", "value": value, "is_verified": verified}


def ext(id_, parent, system="ESCO", identifier="uri-1", version="1.2.1"):
    return {"id": id_, "canonical_entity_id": parent, "source_system": system,
            "external_id": identifier, "source_version": version}


def make_data(**kwargs):
    base = dict(entities=[], aliases=[], entity_domains=[], external_ids=[])
    base.update(kwargs)
    return SeedData(**base)


def snapshot(**kwargs):
    return Snapshot(domains=dict(DOMAINS), **kwargs)


class PlanTests(unittest.TestCase):
    def test_pending_entities_and_their_records_are_excluded(self):
        data = make_data(
            entities=[entity("SK-000001"), entity("SK-000002", name="java", status="PENDING_REVIEW")],
            aliases=[alias("AL-000001", "SK-000002", "j2se")],
            entity_domains=[{"entity_id": "SK-000002", "domains": "IT"}],
            external_ids=[ext("EXT-000001", "SK-000002")],
        )
        plan = plan_import(data, snapshot(), create_missing_sources=True)
        self.assertEqual([r["skill_id"] for r in plan.inserts["skills"]], ["SK-000001"])
        for table in ("skill_aliases", "skill_domains", "skill_external_ids"):
            self.assertEqual(plan.inserts[table], [])
        self.assertIn("SK-000002", plan.pending_ids)

    def test_only_explicit_true_aliases_are_imported(self):
        data = make_data(
            entities=[entity("SK-000001")],
            aliases=[alias("AL-000001", "SK-000001", "py", "TRUE"), alias("AL-000002", "SK-000001", "py2", "False"),
                     alias("AL-000003", "SK-000001", "py3", ""), alias("AL-000004", "SK-000001", "py4", "yes")],
        )
        plan = plan_import(data, snapshot())
        self.assertEqual([r["alias_id"] for r in plan.inserts["skill_aliases"]], ["AL-000001"])
        self.assertEqual(plan.inserts["skill_aliases"][0]["verification_status"], "VERIFIED")
        reasons = {s[1]: s[2] for s in plan.skipped}
        self.assertEqual(reasons["AL-000003"], "invalid_verification:EMPTY")
        self.assertEqual(reasons["AL-000004"], "invalid_verification:YES")

    def test_non_sequential_ids_are_preserved_and_shared_by_dependents(self):
        data = make_data(
            entities=[entity("SK-000007"), entity("RL-000042", "ROLE", "analyst")],
            aliases=[alias("AL-000100", "SK-000007", "py"), alias("AL-000300", "RL-000042", "data analyst")],
            entity_domains=[{"entity_id": "SK-000007", "domains": "IT, BUSINESS"}, {"entity_id": "RL-000042", "domains": "HR"}],
            external_ids=[ext("EXT-000005", "SK-000007"), ext("EXT-000009", "RL-000042", identifier="soc-1")],
        )
        plan = plan_import(data, snapshot(), create_missing_sources=True)
        self.assertEqual(plan.inserts["skill_aliases"][0]["skill_id"], "SK-000007")
        self.assertEqual(plan.inserts["role_aliases"][0]["role_id"], "RL-000042")
        self.assertEqual({r["domain_id"] for r in plan.inserts["skill_domains"]}, {"DOM-IT", "DOM-BUS"})
        self.assertEqual(plan.inserts["role_domains"], [{"role_id": "RL-000042", "domain_id": "DOM-HR"}])
        self.assertEqual(plan.inserts["skill_external_ids"][0]["skill_id"], "SK-000007")
        self.assertEqual(plan.inserts["role_external_ids"][0]["role_id"], "RL-000042")

    def test_invalid_type_and_nature_are_skipped_with_dependents(self):
        data = make_data(
            entities=[entity("SK-000001", kind="BOGUS"), entity("SK-000002", nature="WEIRD"), entity("SK-000003", nature="")],
            aliases=[alias("AL-000001", "SK-000001", "x")],
        )
        plan = plan_import(data, snapshot())
        self.assertEqual([r["skill_id"] for r in plan.inserts["skills"]], ["SK-000003"])
        self.assertIsNone(plan.inserts["skills"][0]["skill_nature"])
        self.assertEqual(plan.inserts["skill_aliases"], [])

    def test_unknown_domain_and_missing_source_are_handled(self):
        data = make_data(
            entities=[entity("SK-000001")],
            entity_domains=[{"entity_id": "SK-000001", "domains": "IT,LEGAL"}],
            external_ids=[ext("EXT-000001", "SK-000001")],
        )
        plan = plan_import(data, snapshot())
        self.assertEqual(len(plan.inserts["skill_domains"]), 1)
        self.assertTrue(any("unknown_domain" in s[2] for s in plan.skipped))
        self.assertTrue(any("source ESCO" in b for b in plan.blocking))

    def test_existing_sources_are_reused(self):
        snap = snapshot(sources={"ESCO": ("SRC-X", "1.0")})
        data = make_data(entities=[entity("SK-000001")], external_ids=[ext("EXT-000001", "SK-000001")])
        plan = plan_import(data, snap)
        self.assertEqual(plan.inserts["knowledge_sources"], [])
        self.assertEqual(plan.inserts["skill_external_ids"][0]["source_id"], "SRC-X")

    def test_conflicting_existing_id_is_reported_not_overwritten(self):
        snap = snapshot(skills={"SK-000001": ("other concept", "KNOWLEDGE")})
        plan = plan_import(make_data(entities=[entity("SK-000001")]), snap)
        self.assertTrue(plan.conflicts)
        self.assertEqual(plan.inserts["skills"], [])

    def test_external_identifier_clash_is_a_conflict(self):
        snap = snapshot(sources={"ESCO": ("SRC-ESCO", "1")}, skill_ext={"EXT-000099": ("SK-000009", "SRC-ESCO", "uri-1")})
        data = make_data(entities=[entity("SK-000001")], external_ids=[ext("EXT-000001", "SK-000001")])
        plan = plan_import(data, snap)
        self.assertTrue(any("already stored" in c for c in plan.conflicts))

    def test_duplicate_csv_ids_and_names_are_not_merged(self):
        data = make_data(entities=[entity("SK-000001"), entity("SK-000001"), entity("SK-000002", name="Python")])
        plan = plan_import(data, snapshot())
        self.assertTrue(any("duplicate canonical id" in c for c in plan.conflicts))
        self.assertEqual(len(plan.inserts["skills"]), 2)
        self.assertTrue(plan.warnings)

    def test_rerun_against_imported_state_plans_nothing(self):
        data = make_data(
            entities=[entity("SK-000001")],
            aliases=[alias("AL-000001", "SK-000001", "Py")],
            entity_domains=[{"entity_id": "SK-000001", "domains": "IT"}],
            external_ids=[ext("EXT-000001", "SK-000001")],
        )
        snap = snapshot(
            sources={"ESCO": ("SRC-ESCO", "1.2.1")}, skills={"SK-000001": ("python", "PROGRAMMING_LANGUAGE")},
            skill_aliases={"AL-000001": ("SK-000001", "Py")}, skill_domains={("SK-000001", "DOM-IT")},
            skill_ext={"EXT-000001": ("SK-000001", "SRC-ESCO", "uri-1")})
        plan = plan_import(data, snap, create_missing_sources=True)
        self.assertEqual(sum(len(v) for v in plan.inserts.values()), 0)
        self.assertFalse(plan.has_problems)
        self.assertEqual(plan.present["skills"], 1)

    def test_normalization_collapses_whitespace_and_case(self):
        self.assertEqual(normalize_alias("  Project   Manager "), "project manager")

    def test_real_seed_files_load_and_have_no_pending_inserts(self):
        data = load_seed(DEFAULT_SEED_DIR)
        plan = plan_import(data, snapshot(), create_missing_sources=True)
        inserted = {r["skill_id"] for r in plan.inserts["skills"]} | {r["role_id"] for r in plan.inserts["roles"]}
        self.assertFalse(inserted & plan.pending_ids)
        self.assertFalse(plan.conflicts)


def _test_db_url():
    if os.environ.get("SSKS_SKIP_DB_TESTS"):
        return None
    return make_url(get_settings().database_url)


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    """Run against a throwaway database, never the real one."""

    async def asyncSetUp(self):
        base_url = _test_db_url()
        if base_url is None:
            self.skipTest("database tests disabled")
        self.admin = create_async_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        self.db_name = f"ssks_import_test_{uuid.uuid4().hex[:8]}"
        try:
            async with self.admin.connect() as conn:
                await conn.execute(text(f'create database "{self.db_name}"'))
        except Exception as exc:
            await self.admin.dispose()
            self.skipTest(f"cannot create test database: {exc}")

        import app.models  # noqa: F401
        from app.db.base import Base
        self.engine = create_async_engine(base_url.set(database=self.db_name))
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            for code, domain_id in DOMAINS.items():
                await conn.execute(text("insert into domains (domain_id, name, code, status) values (:i, :n, :c, 'ACTIVE')"),
                                   {"i": domain_id, "n": code, "c": code})
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)
        self.data = make_data(
            entities=[entity("SK-000001"), entity("RL-000001", "ROLE", "analyst"),
                      entity("SK-000002", name="java", status="PENDING_REVIEW")],
            aliases=[alias("AL-000001", "SK-000001", "py"), alias("AL-000002", "SK-000001", "py2", "False"),
                     alias("AL-000003", "RL-000001", "data analyst")],
            entity_domains=[{"entity_id": "SK-000001", "domains": "IT"}, {"entity_id": "RL-000001", "domains": "BUSINESS, HR"}],
            external_ids=[ext("EXT-000001", "SK-000001"), ext("EXT-000002", "RL-000001", "ONET", "15-1", "29.0")],
        )

    async def asyncTearDown(self):
        if getattr(self, "engine", None):
            await self.engine.dispose()
            async with self.admin.connect() as conn:
                await conn.execute(text(f'drop database if exists "{self.db_name}" with (force)'))
        await self.admin.dispose()

    async def count(self, table):
        async with self.sessionmaker() as s:
            return (await s.execute(text(f"select count(*) from {table}"))).scalar_one()

    async def run_apply(self, data=None):
        return await run_import(self.sessionmaker, data or self.data, apply=True,
                                create_missing_sources=True, confirm_database=self.db_name)

    async def test_apply_is_idempotent_and_verified(self):
        first = await self.run_apply()
        self.assertTrue(all(ok for _, ok, _ in first.checks))
        counts = {t: await self.count(t) for t in first.after}
        self.assertEqual((counts["skills"], counts["roles"], counts["skill_aliases"], counts["role_aliases"]), (1, 1, 1, 1))
        self.assertEqual((counts["skill_domains"], counts["role_domains"], counts["knowledge_sources"]), (1, 2, 2))
        self.assertEqual(counts["domains"], 3)

        second = await self.run_apply()
        self.assertEqual(sum(len(v) for v in second.plan.inserts.values()), 0)
        self.assertEqual({t: await self.count(t) for t in counts}, counts)

    async def test_dry_run_writes_nothing(self):
        result = await run_import(self.sessionmaker, self.data, apply=False, create_missing_sources=True)
        self.assertGreater(len(result.plan.inserts["skills"]), 0)
        self.assertEqual(await self.count("skills"), 0)

    async def test_wrong_database_confirmation_blocks_write(self):
        with self.assertRaises(ImportBlocked):
            await run_import(self.sessionmaker, self.data, apply=True, create_missing_sources=True,
                             confirm_database="not_this_one")
        self.assertEqual(await self.count("skills"), 0)

    async def test_conflict_blocks_and_does_not_overwrite(self):
        await self.run_apply()
        changed = make_data(entities=[entity("SK-000001", name="a different concept")])
        with self.assertRaises(ImportBlocked):
            await self.run_apply(changed)
        async with self.sessionmaker() as s:
            name = (await s.execute(text("select preferred_name from skills where skill_id='SK-000001'"))).scalar_one()
        self.assertEqual(name, "python")

    async def test_failure_midway_rolls_everything_back(self):
        plan = plan_import(self.data, Snapshot(domains=dict(DOMAINS)), create_missing_sources=True)
        plan.inserts["skill_aliases"].append({
            "alias_id": "AL-999999", "skill_id": "SK-404040", "alias_text": "x",
            "normalized_alias": "x", "source_id": None, "verification_status": "VERIFIED"})
        with self.assertRaises(Exception):
            async with self.sessionmaker() as session:
                async with session.begin():
                    await apply_plan(session, plan)
        for table in ("skills", "roles", "knowledge_sources", "skill_aliases"):
            self.assertEqual(await self.count(table), 0)

    async def test_foreign_keys_resolve_after_import(self):
        result = await self.run_apply()
        fk = [c for c in result.checks if c[0].startswith("foreign key")]
        self.assertTrue(fk and all(ok for _, ok, _ in fk))


if __name__ == "__main__":
    unittest.main()
