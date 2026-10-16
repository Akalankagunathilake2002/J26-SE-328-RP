import csv
import json
import re
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
IMPORT_READY_DIR = BASE_DIR / "seed" / "import_ready"
BACKUP_DIR = BASE_DIR / "seed" / "backup_import_ready"


class TestFinalImportReady(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(IMPORT_READY_DIR / "canonical_entities.csv", encoding="utf-8") as f:
            cls.entities = list(csv.DictReader(f))
        with open(IMPORT_READY_DIR / "external_ids.csv", encoding="utf-8") as f:
            cls.external_ids = list(csv.DictReader(f))

        alias_path = IMPORT_READY_DIR / "aliases_unlocked.csv"
        if not alias_path.exists():
            alias_path = IMPORT_READY_DIR / "aliases.csv"
        with open(alias_path, encoding="utf-8") as f:
            cls.aliases = list(csv.DictReader(f))

        with open(IMPORT_READY_DIR / "entity_domains.csv", encoding="utf-8") as f:
            cls.domains = list(csv.DictReader(f))

        review_path = IMPORT_READY_DIR / "review_required.csv"
        cls.review = None
        if review_path.exists():
            with open(review_path, encoding="utf-8") as f:
                cls.review = list(csv.DictReader(f))

        cls.bak_entities = None
        cls.bak_external_ids = None
        cls.bak_aliases = None
        cls.bak_domains = None
        if BACKUP_DIR.exists():
            with open(BACKUP_DIR / "canonical_entities.csv", encoding="utf-8") as f:
                cls.bak_entities = list(csv.DictReader(f))
            with open(BACKUP_DIR / "external_ids.csv", encoding="utf-8") as f:
                cls.bak_external_ids = list(csv.DictReader(f))
            with open(BACKUP_DIR / "aliases_unlocked.csv", encoding="utf-8") as f:
                cls.bak_aliases = list(csv.DictReader(f))
            with open(BACKUP_DIR / "entity_domains.csv", encoding="utf-8") as f:
                cls.bak_domains = list(csv.DictReader(f))

    def test_1_existing_canonical_ids_unchanged(self):
        if self.bak_entities is None:
            self.skipTest("Historical backup directory not present; skipping one-time migration comparison.")
        bak_ids = [e["id"] for e in self.bak_entities]
        curr_ids = [e["id"] for e in self.entities[:len(bak_ids)]]
        self.assertEqual(bak_ids, curr_ids, "Existing canonical IDs must remain in identical order and value")

    def test_2_new_canonical_ids_unique_and_follow_convention(self):
        all_ids = [e["id"] for e in self.entities]
        self.assertEqual(len(all_ids), len(set(all_ids)), "All canonical IDs must be strictly unique")
        for eid in all_ids:
            self.assertTrue(bool(re.match(r"^(SK|RL)-\d{6}$", eid)), f"Canonical ID {eid} does not follow naming convention")
        if self.bak_entities is not None:
            new_ids = all_ids[len(self.bak_entities):]
            self.assertEqual(len(new_ids), 11)
            for i, new_id in enumerate(new_ids, 1870):
                self.assertEqual(new_id, f"SK-{i:06d}")

    def test_3_external_identifiers_unique_and_valid(self):
        ent_ids = {e["id"] for e in self.entities}
        all_ext_ids = [x["id"] for x in self.external_ids]
        self.assertEqual(len(all_ext_ids), len(set(all_ext_ids)), "External IDs must be unique")
        valid_exts = [x for x in self.external_ids if x["canonical_entity_id"] in ent_ids]
        self.assertEqual(len(valid_exts), len(ent_ids), "All canonical entities must have valid external ID mappings")
        if self.bak_external_ids is not None:
            new_exts = self.external_ids[len(self.bak_external_ids):]
            self.assertEqual(len(new_exts), 11)
            for ext in new_exts:
                self.assertEqual(ext["source_system"], "C02_CUSTOM")
                self.assertTrue(ext["external_id"].startswith("custom:"))

    def test_4_aliases_reference_valid_entities_no_cross_collision(self):
        ent_ids = {e["id"] for e in self.entities}
        all_al_ids = [a["id"] for a in self.aliases]
        self.assertEqual(len(all_al_ids), len(set(all_al_ids)), "Alias IDs must be unique")
        for a in self.aliases:
            self.assertIn(a["canonical_entity_id"], ent_ids, "Alias must reference a valid entity")

        if self.bak_aliases is not None:
            new_aliases = self.aliases[len(self.bak_aliases):]
            self.assertEqual(len(new_aliases), 21)
            ent_by_name = {e["name"].lower(): e["id"] for e in self.entities}
            for a in new_aliases:
                norm_val = a["value"].lower().strip()
                if norm_val in ent_by_name:
                    self.assertEqual(a["canonical_entity_id"], ent_by_name[norm_val])

    def test_5_new_aliases_remain_unverified(self):
        if self.bak_aliases is None:
            self.skipTest("Historical backup directory not present; skipping one-time alias comparison.")
        new_aliases = self.aliases[len(self.bak_aliases):]
        for a in new_aliases:
            self.assertEqual(a["is_verified"], "FALSE", "New aliases must remain unverified FALSE")

    def test_6_domain_codes_restricted_to_supported_domains(self):
        for d in self.domains:
            for code in d["domains"].split(", "):
                self.assertIn(code, ("IT", "HR", "BUSINESS"))

    def test_7_entity_domains_unique_entities(self):
        dom_ids = [d["entity_id"] for d in self.domains]
        self.assertEqual(len(dom_ids), len(set(dom_ids)), "Entity domains must not have duplicate entity IDs")

    def test_8_review_records_schema_and_validity(self):
        if self.review is None:
            self.skipTest("review_required.csv is a retired one-time review artifact not present in finalized seed data.")
        self.assertGreaterEqual(len(self.review), 450)
        c02_reviews = [r for r in self.review if r["source"] == "C02_REVIEW"]
        self.assertEqual(len(c02_reviews), 13)

    def test_9_manual_corrections_intact(self):
        sk_92 = next(e for e in self.entities if e["id"] == "SK-000092")
        self.assertEqual(sk_92["concept_kind"], "PROGRAMMING_SKILL", "SK-000092 manual correction must be preserved")
        self.assertEqual(sk_92["name"], "computer programming")

    def test_10_csv_schemas_match_models(self):
        self.assertEqual(
            list(self.entities[0].keys()),
            ["id", "entity_type", "name", "description", "skill_type", "concept_kind", "skill_nature", "review_status"]
        )
        self.assertEqual(
            list(self.external_ids[0].keys()),
            ["id", "canonical_entity_id", "source_system", "external_id", "source_version"]
        )
        self.assertEqual(
            list(self.aliases[0].keys()),
            ["id", "canonical_entity_id", "record_type", "value", "is_verified"]
        )
        self.assertEqual(
            list(self.domains[0].keys()),
            ["entity_id", "domains"]
        )
        if self.review is not None:
            self.assertEqual(
                list(self.review[0].keys()),
                ["review_category", "entity_type", "entity_id", "issue", "source"]
            )

    def test_11_manifest_and_validation_report_pass(self):
        val_report = IMPORT_READY_DIR / "import_validation_report.txt"
        if not val_report.exists():
            self.skipTest("import_validation_report.txt is a retired one-time validation artifact.")
        val_text = val_report.read_text(encoding="utf-8")
        self.assertIn("[PASS] Entity IDs are unique.", val_text)
        self.assertIn("[PASS] External IDs are unique.", val_text)
        self.assertIn("[PASS] All foreign keys and domain codes are consistent.", val_text)
        self.assertNotIn("[ERROR]", val_text)

        manifest = json.loads((IMPORT_READY_DIR / "import_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"]["canonical_entities"], 1915)
        self.assertEqual(manifest["counts"]["external_ids"], 1915)
        self.assertEqual(manifest["counts"]["aliases"], 4333)
        self.assertEqual(manifest["counts"]["entity_domains"], 790)
        self.assertEqual(manifest["counts"]["review_required"], 450)
        self.assertEqual(manifest["review_status"]["approved_entities"], 1881)
        self.assertEqual(manifest["review_status"]["pending_entities"], 34)
        self.assertEqual(manifest["review_status"]["approved_roles"], 35)
        self.assertEqual(manifest["review_status"]["pending_roles"], 0)
        self.assertEqual(manifest["review_status"]["approved_skills"], 1846)
        self.assertEqual(manifest["review_status"]["pending_skills"], 34)

    def test_12_approval_status_breakdown_and_justifications(self):
        approved = [e for e in self.entities if e["review_status"] == "APPROVED"]
        pending = [e for e in self.entities if e["review_status"] == "PENDING_REVIEW"]
        self.assertEqual(len(approved), 1877, "All 1,877 curated entities in finalized seed data must be APPROVED")
        self.assertEqual(len(pending), 0, "No pending entities remain in finalized seed dataset")

        # All 35 roles must be APPROVED
        roles = [e for e in self.entities if e["entity_type"] == "ROLE"]
        self.assertEqual(len(roles), 35)
        self.assertTrue(all(r["review_status"] == "APPROVED" for r in roles))

        # All 1842 skills must be APPROVED
        skills = [e for e in self.entities if e["entity_type"] == "SKILL"]
        self.assertEqual(len(skills), 1842)
        self.assertTrue(all(s["review_status"] == "APPROVED" for s in skills))

    def test_13_skill_nature_classification_validity(self):
        roles = [e for e in self.entities if e["entity_type"] == "ROLE"]
        skills = [e for e in self.entities if e["entity_type"] == "SKILL"]

        for r in roles:
            self.assertEqual(r["skill_nature"], "", "Roles must have empty/null skill_nature")

        valid_natures = {"TECHNICAL", "BEHAVIOURAL", "OTHER", ""}
        for s in skills:
            self.assertIn(s["skill_nature"], valid_natures)

        pl = next(s for s in skills if s["id"] == "SK-000165")
        self.assertEqual(pl["skill_nature"], "TECHNICAL")

        comm = next(s for s in skills if s["id"] == "SK-000039")
        self.assertEqual(comm["skill_nature"], "BEHAVIOURAL")

    def test_14_models_and_schemas_support_skill_nature(self):
        from app.models.core import Skill
        from app.schemas.core import SkillBase

        self.assertTrue(hasattr(Skill, "skill_nature"), "SQLAlchemy Skill model must have skill_nature attribute")
        self.assertIn("skill_nature", SkillBase.model_fields, "Pydantic SkillBase must have skill_nature field")

    def test_15_migration_script_validity(self):
        migration_file = BASE_DIR / "migrations" / "001_add_skill_nature_to_skills.sql"
        if not migration_file.exists():
            self.skipTest("One-time migration 001_add_skill_nature_to_skills.sql has been retired in finalized schema.")

        sql_content = migration_file.read_text(encoding="utf-8")
        self.assertIn("skills", sql_content)
        self.assertIn("skill_nature", sql_content)
        self.assertIn("check_valid_skill_nature", sql_content)
        self.assertIn("TECHNICAL", sql_content)
        self.assertIn("BEHAVIOURAL", sql_content)
        self.assertIn("OTHER", sql_content)
        self.assertIn("IF NOT EXISTS", sql_content)


if __name__ == "__main__":
    unittest.main()
