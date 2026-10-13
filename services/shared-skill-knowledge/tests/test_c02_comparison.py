import os
import unittest
from scripts.comparison.compare_c02_skills import (
    SsksIndex,
    ConflictLog,
    compare_entities,
    compare_aliases,
    suggest_domains,
    violates_ssks_alias_rules,
    is_custom,
    norm_label,
    loose_key,
)


class TestC02Comparison(unittest.TestCase):
    def setUp(self):
        self.entities = [
            {
                "id": "SK-000001",
                "entity_type": "SKILL",
                "name": "Python programming",
                "description": "Python dev",
                "skill_type": "knowledge",
                "concept_kind": "PROGRAMMING_LANGUAGE",
                "review_status": "APPROVED",
            },
            {
                "id": "SK-000002",
                "entity_type": "SKILL",
                "name": "JavaScript",
                "description": "JS dev",
                "skill_type": "knowledge",
                "concept_kind": "PROGRAMMING_LANGUAGE",
                "review_status": "APPROVED",
            },
            {
                "id": "SK-000003",
                "entity_type": "SKILL",
                "name": "computer programming",
                "description": "General programming",
                "skill_type": "knowledge",
                "concept_kind": "PROGRAMMING_SKILL",
                "review_status": "PENDING_REVIEW",
            },
            {
                "id": "SK-000004",
                "entity_type": "SKILL",
                "name": "C",
                "description": "C language",
                "skill_type": "knowledge",
                "concept_kind": "PROGRAMMING_LANGUAGE",
                "review_status": "APPROVED",
            },
        ]
        self.external_ids = [
            {
                "id": "EXT-000001",
                "canonical_entity_id": "SK-000001",
                "source_system": "ESCO",
                "external_id": "http://data.europa.eu/esco/skill/python-uri",
                "source_version": "1.2.1",
            },
            {
                "id": "EXT-000002",
                "canonical_entity_id": "SK-000002",
                "source_system": "ESCO",
                "external_id": "http://data.europa.eu/esco/skill/js-uri",
                "source_version": "1.2.1",
            },
        ]
        self.aliases = [
            {
                "id": "AL-000001",
                "canonical_entity_id": "SK-000001",
                "record_type": "ALIAS",
                "value": "Python",
                "is_verified": "TRUE",
            },
            {
                "id": "AL-000002",
                "canonical_entity_id": "SK-000002",
                "record_type": "ALIAS",
                "value": "JS",
                "is_verified": "TRUE",
            },
        ]
        self.domains = [
            {"entity_id": "SK-000001", "domains": "IT"},
            {"entity_id": "SK-000002", "domains": "IT"},
        ]
        self.index = SsksIndex(self.entities, self.external_ids, self.aliases, self.domains)

    def test_uri_matching_and_id_reuse(self):
        c02_skills = [
            {
                "skill_id": "http://data.europa.eu/esco/skill/python-uri",
                "preferred_label": "Python programming",
                "skill_type": "knowledge",
                "merged_skill_ids": "",
            }
        ]
        conflicts = ConflictLog()
        matches, unmatched, resolution = compare_entities(c02_skills, self.index, conflicts)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["canonical_entity_id"], "SK-000001")
        self.assertEqual(matches[0]["match_method"], "URI_EXACT")
        self.assertEqual(matches[0]["external_id_status"], "ALREADY_PRESENT")
        self.assertEqual(matches[0]["recommendation"], "REUSE_EXISTING_ID")
        self.assertTrue(resolution["http://data.europa.eu/esco/skill/python-uri"]["confirmed"])
        self.assertEqual(len(unmatched), 0)

    def test_custom_skill_handling(self):
        self.assertTrue(is_custom("custom:react"))
        self.assertFalse(is_custom("http://data.europa.eu/esco/skill/react"))

        c02_skills = [
            {
                "skill_id": "custom:react",
                "preferred_label": "React",
                "skill_type": "knowledge",
                "merged_skill_ids": "",
            },
            {
                "skill_id": "custom:python-programming",
                "preferred_label": "Python programming",
                "skill_type": "knowledge",
                "merged_skill_ids": "",
            },
        ]
        conflicts = ConflictLog()
        matches, unmatched, resolution = compare_entities(c02_skills, self.index, conflicts)

        # custom:react has no match in index
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]["skill_id"], "custom:react")

        # custom:python-programming matches by label to SK-000001, but not confirmed by URI
        custom_match = next(m for m in matches if m["c02_skill_id"] == "custom:python-programming")
        self.assertEqual(custom_match["canonical_entity_id"], "SK-000001")
        self.assertEqual(custom_match["match_method"], "LABEL_EXACT")
        self.assertEqual(custom_match["external_id_status"], "NOT_APPLICABLE_CUSTOM_ID")
        self.assertFalse(resolution["custom:python-programming"]["confirmed"])

    def test_alias_duplicate_and_matching_canonical_name(self):
        alias_rows = [
            {"skill_id": "http://data.europa.eu/esco/skill/python-uri", "name": "python", "match_type": "alias"},
            {"skill_id": "http://data.europa.eu/esco/skill/python-uri", "name": "python programming", "match_type": "preferred"},
            {"skill_id": "http://data.europa.eu/esco/skill/python-uri", "name": "py3", "match_type": "alias"},
        ]
        c02_by_id = {
            "http://data.europa.eu/esco/skill/python-uri": {
                "skill_id": "http://data.europa.eu/esco/skill/python-uri",
                "preferred_label": "Python programming",
            }
        }
        resolution = {
            "http://data.europa.eu/esco/skill/python-uri": {
                "method": "URI_EXACT",
                "canonical_ids": ["SK-000001"],
                "confirmed": True,
            }
        }
        conflicts = ConflictLog()
        candidates, stats, _ = compare_aliases(
            alias_rows, c02_by_id, resolution, self.index, conflicts, {}, set(), {}
        )

        statuses = {c["alias_normalized"]: c["alias_status"] for c in candidates}
        self.assertEqual(statuses["python"], "DUPLICATE_EXACT")
        self.assertEqual(statuses["python programming"], "MATCHES_CANONICAL_NAME")
        self.assertEqual(statuses["py3"], "PROPOSED_ALIAS")

    def test_conflicting_mappings_and_rules(self):
        # 1. Computer programming cannot have 'python' as an alias
        rule_violation = violates_ssks_alias_rules("computer programming", "python", self.index.pl_names)
        self.assertIn("must not take programming-language", rule_violation)

        # 2. C cannot alias C++
        c_violation = violates_ssks_alias_rules("C", "c++", self.index.pl_names)
        self.assertIn("must not alias each other", c_violation)

        # 3. Alias collision across entities
        alias_rows = [
            # C02 maps 'JS' (already alias of SK-000002) to Python (SK-000001)
            {"skill_id": "http://data.europa.eu/esco/skill/python-uri", "name": "js", "match_type": "alias"},
        ]
        c02_by_id = {
            "http://data.europa.eu/esco/skill/python-uri": {
                "skill_id": "http://data.europa.eu/esco/skill/python-uri",
                "preferred_label": "Python programming",
            }
        }
        resolution = {
            "http://data.europa.eu/esco/skill/python-uri": {
                "method": "URI_EXACT",
                "canonical_ids": ["SK-000001"],
                "confirmed": True,
            }
        }
        conflicts = ConflictLog()
        candidates, stats, _ = compare_aliases(
            alias_rows, c02_by_id, resolution, self.index, conflicts, {}, set(), {}
        )
        self.assertEqual(candidates[0]["alias_status"], "CONFLICT")
        self.assertEqual(len(conflicts.rows), 1)
        self.assertEqual(conflicts.rows[0]["conflict_type"], "ALIAS_POINTS_TO_DIFFERENT_ENTITY")

    def test_domain_suggestions_conservative(self):
        # 1. Digital skill -> IT
        rec_digital = {
            "domain_tag": "IT/Digital",
            "is_digital": "True",
            "is_transversal": "False",
            "is_language": "False",
            "preferred_label": "Cloud computing",
        }
        res = suggest_domains(rec_digital)
        self.assertEqual(res, [("IT", "SUPPORTED", "ESCO digital skill collection / IT/Digital tag")])

        # 2. Language skill -> No suggestion
        rec_lang = {
            "domain_tag": "Language",
            "is_digital": "False",
            "is_transversal": "False",
            "is_language": "True",
            "preferred_label": "German",
        }
        self.assertEqual(suggest_domains(rec_lang), [])

        # 3. Pure transversal skill -> No suggestion
        rec_trans = {
            "domain_tag": "Soft skill / Transversal",
            "is_digital": "False",
            "is_transversal": "True",
            "is_language": "False",
            "preferred_label": "Teamwork",
        }
        self.assertEqual(suggest_domains(rec_trans), [])

        # 4. Business/Finance tag -> BUSINESS
        rec_biz = {
            "domain_tag": "Business/Finance",
            "is_digital": "False",
            "is_transversal": "False",
            "is_language": "False",
            "preferred_label": "Financial auditing",
        }
        res_biz = suggest_domains(rec_biz)
        self.assertEqual(res_biz, [("BUSINESS", "SUPPORTED", "C02 custom tag Business/Finance")])

        # 5. Non-digital generic skill does not infer HR/BUSINESS automatically
        rec_other = {
            "domain_tag": "handling and moving",
            "is_digital": "False",
            "is_transversal": "False",
            "is_language": "False",
            "preferred_label": "forklift operation",
        }
        self.assertEqual(suggest_domains(rec_other), [])


if __name__ == "__main__":
    unittest.main()
