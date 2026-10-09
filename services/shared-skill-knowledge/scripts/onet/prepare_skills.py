import csv
import os
from typing import Dict, List, Any

OUTPUT_FIELDS = [
    'source',
    'source_version',
    'source_id',
    'preferred_name',
    'description',
    'skill_type',
    'suggested_domain_code',
    'associated_role_ids',
    'associated_role_names',
    'review_status',
    'review_notes'
]

RATINGS_OUTPUT_FIELDS = [
    'onet_soc_code',
    'element_id',
    'scale_id',
    'data_value'
]

def load_existing_reviews(filepath: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(filepath):
        return {}
    reviews = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_id = row.get('source_id')
            if source_id:
                reviews[source_id] = {
                    'review_status': row.get('review_status', 'PENDING_REVIEW'),
                    'review_notes': row.get('review_notes', ''),
                    'suggested_domain_code': row.get('suggested_domain_code', '')
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

def process_skills(input_dir: str, output_dir: str, report: Dict[str, Any], only_approved_roles: bool = True, source_version: str = "Unknown"):
    roles_approved_file = os.path.join(output_dir, 'onet_roles_approved.csv')
    candidates_file = os.path.join(output_dir, 'onet_skills_candidates.csv')
    approved_file = os.path.join(output_dir, 'onet_skills_approved.csv')
    ratings_file = os.path.join(output_dir, 'onet_skills_ratings.csv')

    target_roles = load_roles(roles_approved_file)
    if not only_approved_roles:
        roles_cands_file = os.path.join(output_dir, 'onet_roles_candidates.csv')
        cands = load_roles(roles_cands_file)
        target_roles.update(cands)

    # Load descriptions from content model
    content_model_file = os.path.join(input_dir, 'content_model_reference.csv')
    descriptions = {}
    if os.path.exists(content_model_file):
        with open(content_model_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                element_id = row.get('Element ID')
                if element_id:
                    descriptions[element_id] = row.get('Description', '')

    skill_relations = {} # element_id -> { role_id: {name, domain} }
    skill_types = {} # element_id -> skill_type
    skill_names = {} # element_id -> element_name
    ratings = []
    
    files_to_process = [
        ('essential_skills.csv', 'Skill (Essential)'),
        ('transferable_skills.csv', 'Skill (Transferable)'),
        ('knowledge.csv', 'Knowledge')
    ]

    read_count = 0
    duplicate_count = 0
    
    for filename, stype in files_to_process:
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                read_count += 1
                occ_code = row.get('O*NET-SOC Code')
                if occ_code not in target_roles:
                    continue
                    
                element_id = row.get('Element ID')
                element_name = row.get('Element Name')
                if not element_id:
                    continue
                    
                # Track rating
                scale_id = row.get('Scale ID')
                data_val = row.get('Data Value')
                if scale_id and data_val:
                    ratings.append({
                        'onet_soc_code': occ_code,
                        'element_id': element_id,
                        'scale_id': scale_id,
                        'data_value': data_val
                    })

                if element_id not in skill_relations:
                    skill_relations[element_id] = {}
                    skill_types[element_id] = stype
                    skill_names[element_id] = element_name
                elif skill_types[element_id] != stype:
                    duplicate_count += 1 # Concept mapped across multiple types/files
                    
                # Documented Selection Rule: Only consider the skill/knowledge relevant to the occupation
                # if the Importance (IM) scale value is >= 3.0 out of 5.0.
                if scale_id == 'IM':
                    try:
                        if float(data_val) >= 3.0:
                            skill_relations[element_id][occ_code] = target_roles[occ_code]
                    except ValueError:
                        pass
    
    # Remove elements that ended up with no valid associated roles
    empty_elements = [k for k, v in skill_relations.items() if not v]
    for k in empty_elements:
        del skill_relations[k]

    # Generate candidates
    existing_reviews = load_existing_reviews(approved_file)
    existing_candidates = load_existing_reviews(candidates_file)
    for k, v in existing_reviews.items():
        existing_candidates[k] = v

    candidates = []
    missing_desc = 0
    
    for element_id, relations in skill_relations.items():
        role_ids = list(relations.keys())
        role_names = [r['name'] for r in relations.values()]
        domains = list(set(r['domain'] for r in relations.values() if r['domain']))
        
        # If it spans all 3 domains, it's considered ambiguous/too broad.
        if len(domains) >= 3:
            suggested_domain = ''
        else:
            suggested_domain = ','.join(sorted(domains))
        
        existing = existing_candidates.get(element_id)
        review_status = 'PENDING_REVIEW'
        review_notes = ''
        final_domain = suggested_domain

        if existing:
            review_status = existing['review_status']
            review_notes = existing['review_notes']
            # Only preserve existing domain if it was explicitly reviewed, otherwise use our newly derived one
            if existing['review_status'] not in ('PENDING', 'PENDING_REVIEW') and existing['suggested_domain_code']:
                final_domain = existing['suggested_domain_code']

        desc = descriptions.get(element_id, '')
        if not desc:
            missing_desc += 1

        candidates.append({
            'source': 'ONET',
            'source_version': source_version,
            'source_id': element_id,
            'preferred_name': skill_names[element_id],
            'description': desc,
            'skill_type': skill_types[element_id],
            'suggested_domain_code': final_domain,
            'associated_role_ids': '|'.join(role_ids),
            'associated_role_names': '|'.join(role_names),
            'review_status': review_status,
            'review_notes': review_notes
        })

    report['source_skills_knowledge_read'] = read_count
    report['duplicate_concept_ids_detected'] = duplicate_count
    report['unique_skill_knowledge_selected'] = len(candidates)
    report['missing_descriptions'] = missing_desc
    
    approved = sum(1 for c in candidates if c['review_status'] == 'APPROVED')
    excluded = sum(1 for c in candidates if c['review_status'] == 'EXCLUDED')
    pending = sum(1 for c in candidates if c['review_status'] in ('PENDING', 'PENDING_REVIEW', 'NEEDS_REVIEW'))
    
    report['skills_approved'] = approved
    report['skills_excluded'] = excluded
    report['skills_pending'] = pending

    with open(candidates_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(candidates)
        
    with open(ratings_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=RATINGS_OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(ratings)

    if not os.path.exists(approved_file):
        with open(approved_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
            writer.writeheader()

    return candidates
