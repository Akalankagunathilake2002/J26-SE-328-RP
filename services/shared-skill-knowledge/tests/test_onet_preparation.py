import os
import csv
import json
import tempfile
import unittest

from scripts.onet.prepare_roles import process_roles
from scripts.onet.prepare_skills import process_skills
from scripts.onet.prepare_software import process_software

class TestONETPreparation(unittest.TestCase):
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

    def test_process_roles(self):
        self.create_allowlist({
            "IT": ["15-1252.00"]
        })
        
        occ_headers = ['O*NET-SOC Code', 'Title', 'Description']
        occ_rows = [
            {'O*NET-SOC Code': '15-1252.00', 'Title': 'Software Developers', 'Description': 'Develops software.'},
            {'O*NET-SOC Code': '11-3121.00', 'Title': 'Human Resources Managers', 'Description': 'Manages HR.'}
        ]
        self.create_csv('occupation_data.csv', occ_headers, occ_rows)
        
        titles_headers = ['O*NET-SOC Code', 'Job Title']
        titles_rows = [
            {'O*NET-SOC Code': '15-1252.00', 'Job Title': 'Coder'},
            {'O*NET-SOC Code': '15-1252.00', 'Job Title': 'Software Engineer'}
        ]
        self.create_csv('job_titles.csv', titles_headers, titles_rows)
        
        report = {}
        candidates = process_roles(self.input_dir, self.output_dir, report, config_dir=self.config_dir)
        
        self.assertEqual(len(candidates), 1)
        role = candidates[0]
        self.assertEqual(role['source_id'], '15-1252.00')
        self.assertEqual(role['suggested_domain_code'], 'IT')
        self.assertEqual(role['review_status'], 'PENDING_REVIEW')
        self.assertEqual(role['alternative_labels'], 'Coder|Software Engineer')

    def test_process_skills_knowledge(self):
        # Setup roles approved
        roles_headers = ['source_id', 'preferred_name', 'suggested_domain_code', 'review_status']
        roles_rows = [
            {'source_id': '15-1252.00', 'preferred_name': 'Software Developers', 'suggested_domain_code': 'IT', 'review_status': 'APPROVED'},
            {'source_id': '11-3121.00', 'preferred_name': 'HR Managers', 'suggested_domain_code': 'HR', 'review_status': 'APPROVED'},
            {'source_id': '11-1021.00', 'preferred_name': 'General Managers', 'suggested_domain_code': 'BUSINESS', 'review_status': 'APPROVED'}
        ]
        roles_file = os.path.join(self.output_dir, 'onet_roles_approved.csv')
        with open(roles_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=roles_headers)
            writer.writeheader()
            writer.writerows(roles_rows)
            
        skills_headers = ['O*NET-SOC Code', 'Element ID', 'Element Name', 'Scale ID', 'Data Value']
        skills_rows = [
            # Reading is associated with IT
            {'O*NET-SOC Code': '15-1252.00', 'Element ID': '2.A.1.a', 'Element Name': 'Reading', 'Scale ID': 'IM', 'Data Value': '4.1'},
            # Listening is not associated with anything because IM < 3.0
            {'O*NET-SOC Code': '15-1252.00', 'Element ID': '2.A.1.b', 'Element Name': 'Listening', 'Scale ID': 'IM', 'Data Value': '2.5'},
            # Ambiguous skill associated with IT, HR, BUSINESS
            {'O*NET-SOC Code': '15-1252.00', 'Element ID': '2.A.1.c', 'Element Name': 'Writing', 'Scale ID': 'IM', 'Data Value': '3.5'},
            {'O*NET-SOC Code': '11-3121.00', 'Element ID': '2.A.1.c', 'Element Name': 'Writing', 'Scale ID': 'IM', 'Data Value': '3.5'},
            {'O*NET-SOC Code': '11-1021.00', 'Element ID': '2.A.1.c', 'Element Name': 'Writing', 'Scale ID': 'IM', 'Data Value': '3.5'}
        ]
        self.create_csv('essential_skills.csv', skills_headers, skills_rows)
        
        # Test content model join
        cm_headers = ['Element ID', 'Description']
        cm_rows = [
            {'Element ID': '2.A.1.a', 'Description': 'Understand written sentences.'},
            {'Element ID': '2.A.1.c', 'Description': 'Communicate effectively in writing.'}
        ]
        self.create_csv('content_model_reference.csv', cm_headers, cm_rows)
        
        report = {}
        candidates = process_skills(self.input_dir, self.output_dir, report)
        
        # Only 'Reading' and 'Writing' should be created
        self.assertEqual(len(candidates), 2)
        
        reading = next(c for c in candidates if c['source_id'] == '2.A.1.a')
        self.assertEqual(reading['description'], 'Understand written sentences.')
        self.assertEqual(reading['skill_type'], 'Skill (Essential)')
        self.assertEqual(reading['suggested_domain_code'], 'IT')
        
        writing = next(c for c in candidates if c['source_id'] == '2.A.1.c')
        self.assertEqual(writing['suggested_domain_code'], '')  # Ambiguous since it spans 3 domains
        
        # Ratings should be in a separate file
        ratings_file = os.path.join(self.output_dir, 'onet_skills_ratings.csv')
        self.assertTrue(os.path.exists(ratings_file))
        with open(ratings_file, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 5)

    def test_process_software(self):
        roles_headers = ['source_id', 'preferred_name', 'suggested_domain_code', 'review_status']
        roles_rows = [{'source_id': '15-1252.00', 'preferred_name': 'Software Developers', 'suggested_domain_code': 'IT', 'review_status': 'APPROVED'}]
        roles_file = os.path.join(self.output_dir, 'onet_roles_approved.csv')
        with open(roles_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=roles_headers)
            writer.writeheader()
            writer.writerows(roles_rows)
            
        soft_headers = ['O*NET-SOC Code', 'Element ID', 'Element Name', 'Workplace Example', 'Hot Technology', 'In Demand']
        soft_rows = [
            {'O*NET-SOC Code': '15-1252.00', 'Element ID': '2.E.5.b', 'Element Name': 'Doc software', 'Workplace Example': 'Acrobat', 'Hot Technology': 'Y', 'In Demand': 'N'}
        ]
        self.create_csv('software_skills.csv', soft_headers, soft_rows)
        
        report = {}
        candidates = process_software(self.input_dir, self.output_dir, report)
        
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['source_id'], '')
        self.assertEqual(candidates[0]['onet_element_id'], '2.E.5.b')
        self.assertEqual(candidates[0]['technology_example'], 'Acrobat')
        self.assertEqual(candidates[0]['hot_technology'], 'Y')

if __name__ == '__main__':
    unittest.main()
