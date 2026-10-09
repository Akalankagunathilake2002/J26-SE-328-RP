import csv
import os
from datetime import datetime, timezone
from typing import Dict, List, Any

OUTPUT_FIELDS = [
    'esco_uri',
    'preferred_name',
    'alternative_labels',
    'hidden_labels',
    'description',
    'definition',
    'skill_type',
    'reuse_level',
    'esco_status',
    'modified_date',
    'source',
    'source_version',
    'suggested_domain_code',
    'associated_role_uris',
    'associated_role_names',
    'relation_types',
    'review_status',
    'review_notes'
]

import tempfile

def safe_write_csv(data: List[Dict[str, Any]], filepath: str, fieldnames: List[str]):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', delete=False) as tf:
            writer = csv.DictWriter(tf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            temp_name = tf.name
        os.replace(temp_name, filepath)
    except PermissionError as e:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except:
                pass
        raise PermissionError(f"Permission denied writing to {filepath}. Is the file open in another program like Excel?") from e
    except Exception as e:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except:
                pass
        raise e

def load_existing_reviews(filepath: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(filepath):
        return {}
    reviews = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uri = row.get('esco_uri')
            if uri:
                reviews[uri] = {
                    'review_status': row.get('review_status', 'PENDING'),
                    'review_notes': row.get('review_notes', ''),
                    'suggested_domain_code': row.get('suggested_domain_code', '')
                }
    return reviews

def parse_date(date_str: str):
    min_date = datetime.min.replace(tzinfo=timezone.utc)
    if not date_str:
        return min_date
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return min_date

def load_roles(candidates_file: str, approved_file: str, only_approved: bool) -> Dict[str, Dict[str, str]]:
    """
    Load roles from candidate and/or approved files.
    Returns a dict mapping role URI to role data (name and domain).
    """
    roles = {}
    files_to_check = [approved_file] if only_approved else [candidates_file, approved_file]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if only_approved and row.get('review_status') != 'APPROVED':
                        continue
                    if not only_approved and row.get('review_status') == 'EXCLUDED':
                        continue
                        
                    uri = row.get('esco_uri')
                    if uri:
                        roles[uri] = {
                            'name': row.get('preferred_name', ''),
                            'domain': row.get('suggested_domain_code', '')
                        }
    return roles

def process_skills(input_dir: str, output_dir: str, report: Dict[str, Any], only_approved_roles: bool = False):
    """
    Process ESCO skills and generate candidate skills based on selected roles.
    """
    skills_file = os.path.join(input_dir, 'skills_en.csv')
    relations_file = os.path.join(input_dir, 'occupationSkillRelations_en.csv')
    candidates_file = os.path.join(output_dir, 'esco_skills_candidates.csv')
    approved_file = os.path.join(output_dir, 'esco_skills_approved.csv')
    
    roles_candidates_file = os.path.join(output_dir, 'esco_roles_candidates.csv')
    roles_approved_file = os.path.join(output_dir, 'esco_roles_approved.csv')

    # Load target roles
    target_roles = load_roles(roles_candidates_file, roles_approved_file, only_approved_roles)
    
    # Parse relations
    # Mapping skill_uri -> { role_uri: { 'name': name, 'type': relation_type } }
    skill_relations = {}
    missing_roles_refs = 0
    missing_skills_refs = 0
    
    essential_relations_count = 0
    optional_relations_count = 0
    
    with open(relations_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            occ_uri = row.get('occupationUri')
            skill_uri = row.get('skillUri')
            rel_type = row.get('relationType')
            occ_label = row.get('occupationLabel', '')
            
            if not occ_uri or not skill_uri:
                continue
                
            if occ_uri in target_roles:
                if skill_uri not in skill_relations:
                    skill_relations[skill_uri] = {}
                skill_relations[skill_uri][occ_uri] = {
                    'name': occ_label or target_roles[occ_uri]['name'],
                    'type': rel_type,
                    'domain': target_roles[occ_uri]['domain']
                }
                if rel_type == 'essential':
                    essential_relations_count += 1
                elif rel_type == 'optional':
                    optional_relations_count += 1

    # Deduplicate skills
    skills_map = {}
    duplicate_count = 0
    read_count = 0

    with open(skills_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            read_count += 1
            uri = row.get('conceptUri')
            if not uri:
                continue

            # Check if this skill is in our associated list
            if uri in skill_relations:
                current_date = parse_date(row.get('modifiedDate'))
                
                if uri in skills_map:
                    duplicate_count += 1
                    existing_date = parse_date(skills_map[uri].get('modifiedDate'))
                    if current_date > existing_date:
                        skills_map[uri] = row
                else:
                    skills_map[uri] = row

    # Find missing skill references (in relations but not in skills_en.csv)
    for skill_uri in skill_relations.keys():
        if skill_uri not in skills_map:
            missing_skills_refs += 1

    missing_skill_types = 0
    for uri, row in skills_map.items():
        if not row.get('skillType'):
            missing_skill_types += 1
            
    report['source_skills_read'] = read_count
    report['duplicate_skill_uris_detected'] = duplicate_count
    report['skills_associated_with_roles'] = len(skill_relations)
    report['unique_skill_uris_selected'] = len(skills_map)
    report['missing_skill_references'] = missing_skills_refs
    report['missing_skill_types'] = missing_skill_types
    report['essential_associations'] = essential_relations_count
    report['optional_associations'] = optional_relations_count

    # Generate candidates
    existing_reviews = load_existing_reviews(approved_file)
    existing_candidates = load_existing_reviews(candidates_file)
    for k, v in existing_reviews.items():
        existing_candidates[k] = v

    candidates = []
    
    for uri, row in skills_map.items():
        relations = skill_relations.get(uri, {})
        
        role_uris = list(relations.keys())
        role_names = [r['name'] for r in relations.values()]
        rel_types = [r['type'] for r in relations.values()]
        domains = list(set(r['domain'] for r in relations.values() if r['domain']))
        
        suggested_domain = ','.join(domains)
        
        existing = existing_candidates.get(uri)
        review_status = 'PENDING'
        review_notes = ''
        final_domain = suggested_domain

        if existing:
            review_status = existing['review_status']
            review_notes = existing['review_notes']
            if existing['suggested_domain_code']:
                final_domain = existing['suggested_domain_code']

        candidates.append({
            'esco_uri': uri,
            'preferred_name': row.get('preferredLabel', ''),
            'alternative_labels': row.get('altLabels', ''),
            'hidden_labels': row.get('hiddenLabels', ''),
            'description': row.get('description', ''),
            'definition': row.get('definition', ''),
            'skill_type': row.get('skillType', ''),
            'reuse_level': row.get('reuseLevel', ''),
            'esco_status': row.get('status', ''),
            'modified_date': row.get('modifiedDate', ''),
            'source': 'ESCO',
            'source_version': '1.2.1',
            'suggested_domain_code': final_domain,
            'associated_role_uris': '|'.join(role_uris),
            'associated_role_names': '|'.join(role_names),
            'relation_types': '|'.join(rel_types),
            'review_status': review_status,
            'review_notes': review_notes
        })

    # Track review stats
    approved = sum(1 for c in candidates if c['review_status'] == 'APPROVED')
    excluded = sum(1 for c in candidates if c['review_status'] == 'EXCLUDED')
    pending = sum(1 for c in candidates if c['review_status'] in ('PENDING', 'NEEDS_REVIEW'))
    
    report['skills_approved'] = approved
    report['skills_excluded'] = excluded
    report['skills_pending'] = pending

    safe_write_csv(candidates, candidates_file, OUTPUT_FIELDS)
        
    if not os.path.exists(approved_file):
        safe_write_csv([], approved_file, OUTPUT_FIELDS)

    return candidates
