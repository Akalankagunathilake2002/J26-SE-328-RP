import os
import csv
import json
import tempfile
import unittest
from datetime import datetime

from scripts.esco.prepare_roles import process_roles
from scripts.esco.prepare_skills import process_skills

class TestESCOPreparation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.test_dir.name, "input")
        self.output_dir = os.path.join(self.test_dir.name, "output")
        self.config_dir = os.path.join(self.test_dir.name, "config")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)
        os.makedirs(self.config_dir)

    def tearDown(self):
        self.test_dir.cleanup()

    def create_csv(self, filename, headers, rows):
        path = os.path.join(self.input_dir, filename)
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def create_allowlist(self, data):
        path = os.path.join(self.config_dir, 'role_allowlist.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return path

    def test_process_roles_parsing_and_deduplication(self):
        self.create_allowlist({
            "IT": ["uri1"],
            "HR": ["uri2"]
        })
        
        headers = ['conceptUri', 'preferredLabel', 'iscoGroup', 'modifiedDate', 'status', 'description', 'definition', 'altLabels', 'hiddenLabels']
        rows = [
            {'conceptUri': 'uri1', 'preferredLabel': 'Software "Engineer", Senior', 'iscoGroup': '2511', 'modifiedDate': '2023-01-01T00:00:00.000Z'},
            {'conceptUri': 'uri1', 'preferredLabel': 'Software "Engineer", Senior', 'iscoGroup': '2511', 'modifiedDate': '2023-02-01T00:00:00.000Z'}, # Duplicate, newer
            {'conceptUri': 'uri2', 'preferredLabel': 'HR Manager', 'iscoGroup': '1212', 'modifiedDate': 'invalid_date'}, # Valid via URI
            {'conceptUri': 'uri3', 'preferredLabel': 'Unknown Role', 'iscoGroup': '9999'} # Not in allowlist
        ]
        self.create_csv('occupations_en.csv', headers, rows)
        
        report = {}
        candidates = process_roles(self.input_dir, self.output_dir, report, config_dir=self.config_dir)
        
        self.assertEqual(len(candidates), 2)
        
        uri1_cand = next(c for c in candidates if c['esco_uri'] == 'uri1')
        self.assertEqual(uri1_cand['modified_date'], '2023-02-01T00:00:00.000Z') # Deduplicated to newer
        self.assertEqual(uri1_cand['preferred_name'], 'Software "Engineer", Senior') 
        self.assertEqual(uri1_cand['suggested_domain_code'], 'IT')
        self.assertEqual(uri1_cand['review_status'], 'PENDING_REVIEW') 
        
        uri2_cand = next(c for c in candidates if c['esco_uri'] == 'uri2')
        self.assertEqual(uri2_cand['suggested_domain_code'], 'HR')
        self.assertEqual(uri2_cand['review_status'], 'PENDING_REVIEW') 
        
        self.assertEqual(report['duplicate_role_uris_detected'], 1)

    def test_process_skills_joining_and_missing_refs(self):
        roles_headers = ['esco_uri', 'preferred_name', 'suggested_domain_code', 'review_status']
        roles_rows = [
            {'esco_uri': 'occ1', 'preferred_name': 'IT Pro', 'suggested_domain_code': 'IT', 'review_status': 'APPROVED'},
            {'esco_uri': 'occ2', 'preferred_name': 'HR Pro', 'suggested_domain_code': 'HR', 'review_status': 'EXCLUDED'}
        ]
        roles_file = os.path.join(self.output_dir, 'esco_roles_approved.csv')
        with open(roles_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=roles_headers)
            writer.writeheader()
            writer.writerows(roles_rows)
            
        rel_headers = ['occupationUri', 'skillUri', 'relationType', 'occupationLabel']
        rel_rows = [
            {'occupationUri': 'occ1', 'skillUri': 'skill1', 'relationType': 'essential'},
            {'occupationUri': 'occ1', 'skillUri': 'skill1', 'relationType': 'optional'}, 
            {'occupationUri': 'occ2', 'skillUri': 'skill1', 'relationType': 'essential'}, # occ2 is excluded, skill should not register this occ
            {'occupationUri': 'occ1', 'skillUri': 'missing_skill', 'relationType': 'essential'}, 
            {'occupationUri': 'missing_occ', 'skillUri': 'skill2', 'relationType': 'essential'}
        ]
        self.create_csv('occupationSkillRelations_en.csv', rel_headers, rel_rows)
        
        skills_headers = ['conceptUri', 'preferredLabel', 'skillType', 'modifiedDate']
        skills_rows = [
            {'conceptUri': 'skill1', 'preferredLabel': 'Python', 'skillType': ''},
            {'conceptUri': 'skill2', 'preferredLabel': 'Communication'} 
        ]
        self.create_csv('skills_en.csv', skills_headers, skills_rows)
        
        report = {}
        # Simulate the only-approved-roles=True flag
        candidates = process_skills(self.input_dir, self.output_dir, report, only_approved_roles=True)
        
        self.assertEqual(len(candidates), 1)
        skill1 = candidates[0]
        self.assertEqual(skill1['esco_uri'], 'skill1')
        
        # Test association merging
        associated_roles = set(skill1['associated_role_uris'].split('|'))
        self.assertEqual(associated_roles, {'occ1'}) # occ2 should not be there
        
        # Test domains mapped back from associated roles
        domains = set(skill1['suggested_domain_code'].split(','))
        self.assertEqual(domains, {'IT'})
        
        # Test missing skill types
        self.assertEqual(report['missing_skill_types'], 1)

    def test_review_status_preservation(self):
        self.create_allowlist({})
        
        # Create an existing reviewed record
        app_file = os.path.join(self.output_dir, 'esco_roles_approved.csv')
        app_headers = ['esco_uri', 'preferred_name', 'review_status', 'review_notes', 'suggested_domain_code']
        app_rows = [{'esco_uri': 'occ1', 'preferred_name': 'Old Title', 'review_status': 'APPROVED', 'review_notes': 'Looks good', 'suggested_domain_code': 'BUSINESS'}]
        with open(app_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=app_headers)
            writer.writeheader()
            writer.writerows(app_rows)
            
        occ_headers = ['conceptUri', 'preferredLabel', 'iscoGroup']
        occ_rows = [{'conceptUri': 'occ1', 'preferredLabel': 'New Title', 'iscoGroup': '2511'}]
        self.create_csv('occupations_en.csv', occ_headers, occ_rows)
        
        report = {}
        candidates = process_roles(self.input_dir, self.output_dir, report, config_dir=self.config_dir)
        
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['review_status'], 'APPROVED')
        self.assertEqual(candidates[0]['review_notes'], 'Looks good')
        self.assertEqual(candidates[0]['suggested_domain_code'], 'BUSINESS')
        self.assertEqual(candidates[0]['preferred_name'], 'New Title')

if __name__ == '__main__':
    unittest.main()
