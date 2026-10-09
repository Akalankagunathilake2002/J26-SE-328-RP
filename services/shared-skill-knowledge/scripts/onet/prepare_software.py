import csv
import os
import hashlib
from typing import Dict, List, Any

OUTPUT_FIELDS = [
    'source',
    'source_version',
    'source_id',
    'onet_element_id',
    'preferred_name',
    'description',
    'associated_role_ids',
    'associated_role_names',
    'technology_example',
    'hot_technology',
    'in_demand',
    'review_status',
    'review_notes'
]

def load_existing_reviews(filepath: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(filepath):
        return {}
    reviews = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # For software, we use the combination of onet_element_id and technology_example to uniquely identify
            key = f"{row.get('onet_element_id', '')}::{row.get('technology_example', '')}"
            reviews[key] = {
                'review_status': row.get('review_status', 'PENDING_REVIEW'),
                'review_notes': row.get('review_notes', '')
            }
    return reviews

def load_roles(filepath: str) -> Dict[str, Dict[str, str]]:
    roles = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('review_status') in ('APPROVED', 'PENDING_REVIEW'):
                    code = row.get('source_id')
                    if code:
                        roles[code] = {
                            'name': row.get('preferred_name', ''),
                            'domain': row.get('suggested_domain_code', '')
                        }
    return roles

def process_software(input_dir: str, output_dir: str, report: Dict[str, Any], only_approved_roles: bool = True, source_version: str = "Unknown"):
    roles_approved_file = os.path.join(output_dir, 'onet_roles_approved.csv')
    candidates_file = os.path.join(output_dir, 'onet_software_candidates.csv')

    target_roles = load_roles(roles_approved_file)
    if not only_approved_roles:
        roles_cands_file = os.path.join(output_dir, 'onet_roles_candidates.csv')
        cands = load_roles(roles_cands_file)
        target_roles.update(cands)

    software_file = os.path.join(input_dir, 'software_skills.csv')
    
    # key -> { element_id, element_name, example, hot, in_demand, roles: { occ_code: role } }
    software_map = {}
    read_count = 0

    if os.path.exists(software_file):
        with open(software_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                read_count += 1
                occ_code = row.get('O*NET-SOC Code')
                if occ_code not in target_roles:
                    continue
                    
                element_id = row.get('Element ID', '')
                element_name = row.get('Element Name', '')
                example = row.get('Workplace Example', '')
                hot = row.get('Hot Technology', '')
                demand = row.get('In Demand', '')
                
                key = f"{element_id}::{example}"
                
                if key not in software_map:
                    software_map[key] = {
                        'element_id': element_id,
                        'element_name': element_name,
                        'example': example,
                        'hot': hot,
                        'in_demand': demand,
                        'roles': {}
                    }
                
                software_map[key]['roles'][occ_code] = target_roles[occ_code]
                
                # Update hot/demand if one role has it as Y
                if hot == 'Y':
                    software_map[key]['hot'] = 'Y'
                if demand == 'Y':
                    software_map[key]['in_demand'] = 'Y'

    existing_candidates = load_existing_reviews(candidates_file)
    candidates = []

    for key, data in software_map.items():
        role_ids = list(data['roles'].keys())
        role_names = [r['name'] for r in data['roles'].values()]
        
        existing = existing_candidates.get(key)
        review_status = 'PENDING_REVIEW'
        review_notes = ''

        if existing:
            review_status = existing['review_status']
            review_notes = existing['review_notes']

        candidates.append({
            'source': 'ONET',
            'source_version': source_version,
            'source_id': '', # O*NET doesn't provide a unique ID per product, only a category ID
            'onet_element_id': data['element_id'],
            'preferred_name': data['element_name'],
            'description': '', # usually blank for software categories unless joined with content model
            'associated_role_ids': '|'.join(role_ids),
            'associated_role_names': '|'.join(role_names),
            'technology_example': data['example'],
            'hot_technology': data['hot'],
            'in_demand': data['in_demand'],
            'review_status': review_status,
            'review_notes': review_notes
        })

    report['source_software_read'] = read_count
    report['unique_software_selected'] = len(candidates)
    
    approved = sum(1 for c in candidates if c['review_status'] == 'APPROVED')
    excluded = sum(1 for c in candidates if c['review_status'] == 'EXCLUDED')
    pending = sum(1 for c in candidates if c['review_status'] in ('PENDING', 'PENDING_REVIEW', 'NEEDS_REVIEW'))
    
    report['software_approved'] = approved
    report['software_excluded'] = excluded
    report['software_pending'] = pending

    with open(candidates_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(candidates)

    return candidates
