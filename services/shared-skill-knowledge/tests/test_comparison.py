import os
import unittest
import tempfile
from scripts.comparison.utils import normalize_text, is_fuzzy_match, get_match_level
from scripts.comparison.compare_roles import compare_roles
from scripts.comparison.compare_skills import compare_skills
from scripts.comparison.compare_software import compare_software

class TestComparison(unittest.TestCase):
    def test_normalize_text(self):
        self.assertEqual(normalize_text("  Software Engineer, Senior! "), "software engineer senior")
        self.assertEqual(normalize_text("C++ Developer"), "c developer") # note: punctuation removed
        self.assertEqual(normalize_text(""), "")

    def test_get_match_level(self):
        # Exact
        match_type, score = get_match_level(["Software Engineer"], ["software engineer"])
        self.assertEqual(match_type, "EXACT")
        self.assertEqual(score, 1.0)
        
        # Alternative
        match_type, score = get_match_level(["Coder", "Programmer"], ["Software Engineer", "programmer"])
        self.assertEqual(match_type, "ALTERNATIVE")
        self.assertEqual(score, 1.0)
        
        # Fuzzy
        match_type, score = get_match_level(["Human Resources Manager"], ["Human Resource Manager"])
        self.assertEqual(match_type, "FUZZY")
        self.assertGreaterEqual(score, 0.85)
        
        # None
        match_type, score = get_match_level(["Dog Walker"], ["Software Engineer"])
        self.assertIsNone(match_type)
        self.assertEqual(score, 0.0)

    def test_compare_roles(self):
        esco = [
            {'esco_uri': 'e1', 'preferred_name': 'IT Manager', 'alternative_labels': ''},
            {'esco_uri': 'e2', 'preferred_name': 'HR Director', 'alternative_labels': 'Chief HR Officer'},
            {'esco_uri': 'e3', 'preferred_name': 'Unmatched Role', 'alternative_labels': ''}
        ]
        
        onet = [
            {'source_id': 'o1', 'preferred_name': 'IT Manager', 'alternative_labels': ''},
            {'source_id': 'o2', 'preferred_name': 'Chief HR Officer', 'alternative_labels': ''},
            {'source_id': 'o3', 'preferred_name': 'Totally Different', 'alternative_labels': ''}
        ]
        
        matches, un_esco, un_onet, report = compare_roles(esco, onet)
        self.assertEqual(len(matches), 2)
        
        exact = next(m for m in matches if m['match_method'] == 'EXACT')
        self.assertEqual(exact['esco_uri'], 'e1')
        self.assertEqual(exact['onet_source_id'], 'o1')
        self.assertEqual(exact['review_status'], 'PENDING_REVIEW')
        
        alt = next(m for m in matches if m['match_method'] == 'ALTERNATIVE')
        self.assertEqual(alt['esco_uri'], 'e2')
        self.assertEqual(alt['onet_source_id'], 'o2')
        
        self.assertEqual(len(un_esco), 1)
        self.assertEqual(un_esco[0]['esco_uri'], 'e3')
        self.assertEqual(report['unmatched_esco'], 1)

    def test_compare_skills(self):
        esco = [
            {'esco_uri': 'es1', 'preferred_name': 'Python programming', 'skill_type': 'knowledge', 'suggested_domain_code': 'IT', 'alternative_labels': ''},
            {'esco_uri': 'es2', 'preferred_name': 'Communication', 'skill_type': 'skill/competence', 'suggested_domain_code': 'IT,HR', 'alternative_labels': ''}
        ]
        
        onet = [
            {'source_id': 'os1', 'preferred_name': 'Python programming', 'skill_type': 'Knowledge', 'suggested_domain_code': 'IT'},
            {'source_id': 'os2', 'preferred_name': 'Communication', 'skill_type': 'Skill (Essential)', 'suggested_domain_code': 'BUSINESS'}
        ]
        
        matches, un_esco, un_onet, report = compare_skills(esco, onet)
        self.assertEqual(len(matches), 2)
        
        python_match = next(m for m in matches if m['esco_uri'] == 'es1')
        self.assertEqual(python_match['domain_conflict'], 'NO')
        
        comm_match = next(m for m in matches if m['esco_uri'] == 'es2')
        self.assertEqual(comm_match['domain_conflict'], 'YES') # ESCO=IT,HR vs ONET=BUSINESS
        
        self.assertEqual(report['conflicting_domains'], 1)

    def test_compare_software(self):
        esco = [
            {'esco_uri': 'es1', 'preferred_name': 'Microsoft Excel', 'alternative_labels': 'Excel'}
        ]
        
        onet = [
            {'onet_element_id': 'o1', 'technology_example': 'Microsoft Excel', 'preferred_name': 'Spreadsheet software'},
            {'onet_element_id': 'o2', 'technology_example': 'Unmatched Software', 'preferred_name': 'Other software'}
        ]
        
        matches, report = compare_software(esco, onet)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['esco_uri'], 'es1')
        self.assertEqual(matches[0]['onet_element_id'], 'o1')
        self.assertEqual(matches[0]['onet_technology_example'], 'Microsoft Excel')
        
        self.assertEqual(report['unmatched_software'], 1)

if __name__ == '__main__':
    unittest.main()
