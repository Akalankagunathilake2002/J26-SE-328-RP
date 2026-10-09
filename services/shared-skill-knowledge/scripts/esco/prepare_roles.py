import csv
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

import tempfile

# Define the expected fields for the output role candidates CSV
OUTPUT_FIELDS = [
    'esco_uri',
    'preferred_name',
    'alternative_labels',
    'hidden_labels',
    'description',
    'definition',
    'esco_status',
    'modified_date',
    'isco_group_code',
    'source',
    'source_version',
    'suggested_domain_code',
    'review_status',
    'review_notes'
]

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

def load_allowlist(config_dir: str) -> Dict[str, List[str]]:
    allowlist_path = os.path.join(config_dir, 'role_allowlist.json')
    if not os.path.exists(allowlist_path):
        return {}
    with open(allowlist_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_reviews(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Load existing reviewed roles to preserve their review status and notes.
    """
    if not os.path.exists(filepath):
        return {}
        
    reviews = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uri = row.get('esco_uri')
            if uri:
                reviews[uri] = {
                    'review_status': row.get('review_status', 'PENDING_REVIEW'),
                    'review_notes': row.get('review_notes', ''),
                    'suggested_domain_code': row.get('suggested_domain_code', '')
                }
    return reviews

def parse_date(date_str: str):
    """
    Parse the ESCO modifiedDate string to a comparable format.
    """
    min_date = datetime.min.replace(tzinfo=timezone.utc)
    if not date_str:
        return min_date
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return min_date

def process_roles(input_dir: str, output_dir: str, report: Dict[str, Any], config_dir: str = None):
    """
    Process ESCO occupations and generate candidate roles.
    """
    if config_dir is None:
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        
    occupations_file = os.path.join(input_dir, 'occupations_en.csv')
    candidates_file = os.path.join(output_dir, 'esco_roles_candidates.csv')
    approved_file = os.path.join(output_dir, 'esco_roles_approved.csv')
    
    if not os.path.exists(occupations_file):
        raise FileNotFoundError(f"Source file missing: {occupations_file}")

    allowlist_data = load_allowlist(config_dir)
    
    # Reverse mapping for allowlist (URI -> list of domains)
    allowed_uris = {}
    for domain, items in allowlist_data.items():
        for item in items:
            # We support URI or label matching, but assuming URIs for strict match
            if item not in allowed_uris:
                allowed_uris[item] = []
            allowed_uris[item].append(domain)

    # Load existing reviews if any
    existing_reviews = load_existing_reviews(approved_file)
    existing_candidates = load_existing_reviews(candidates_file)
    
    for k, v in existing_reviews.items():
        existing_candidates[k] = v

    occupations_map = {}
    duplicate_count = 0
    read_count = 0

    with open(occupations_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            read_count += 1
            uri = row.get('conceptUri')
            if not uri:
                continue

            current_date = parse_date(row.get('modifiedDate'))
            
            if uri in occupations_map:
                duplicate_count += 1
                existing_date = parse_date(occupations_map[uri].get('modifiedDate'))
                if current_date > existing_date:
                    occupations_map[uri] = row
            else:
                occupations_map[uri] = row

    report['source_occupations_read'] = read_count
    report['duplicate_role_uris_detected'] = duplicate_count

    candidates = []
    approved_records = []
    domain_counts = {"IT": 0, "HR": 0, "BUSINESS": 0, "NONE": 0}

    for uri, row in occupations_map.items():
        existing = existing_candidates.get(uri)
        
        is_allowed = uri in allowed_uris
        
        suggested_domains = allowed_uris.get(uri, [])
        suggested_domain_code = ','.join(suggested_domains)
        
        # Determine review status
        review_status = 'PENDING_REVIEW'
        review_notes = ''
        final_domain = suggested_domain_code

        if existing:
            review_status = existing['review_status']
            review_notes = existing['review_notes']
            if existing['review_status'] not in ('PENDING', 'PENDING_REVIEW') and existing['suggested_domain_code']:
                final_domain = existing['suggested_domain_code']

        # We only output roles that are allowed OR were previously reviewed by human
        if is_allowed or (existing and existing['review_status'] not in ('PENDING', 'PENDING_REVIEW')):
            record = {
                'esco_uri': uri,
                'preferred_name': row.get('preferredLabel', ''),
                'alternative_labels': row.get('altLabels', ''),
                'hidden_labels': row.get('hiddenLabels', ''),
                'description': row.get('description', ''),
                'definition': row.get('definition', ''),
                'esco_status': row.get('status', ''),
                'modified_date': row.get('modifiedDate', ''),
                'isco_group_code': row.get('iscoGroup', ''),
                'source': 'ESCO',
                'source_version': '1.2.1',
                'suggested_domain_code': final_domain,
                'review_status': review_status,
                'review_notes': review_notes
            }
            candidates.append(record)
            
            if review_status == 'APPROVED':
                approved_records.append(record)
                
            # Count domains based on final_domain assignment
            domains = final_domain.split(',') if final_domain else ["NONE"]
            for d in domains:
                if d in domain_counts:
                    domain_counts[d] += 1
                elif d:
                    # Ignore empty domains when counting
                    domain_counts["NONE"] += 1

    report['candidate_roles_generated'] = len(candidates)
    report['roles_by_domain'] = domain_counts
    
    approved = sum(1 for c in candidates if c['review_status'] == 'APPROVED')
    excluded = sum(1 for c in candidates if c['review_status'] == 'EXCLUDED')
    pending = sum(1 for c in candidates if c['review_status'] in ('PENDING', 'PENDING_REVIEW', 'NEEDS_REVIEW'))
    
    report['roles_approved'] = approved
    report['roles_excluded'] = excluded
    report['roles_pending'] = pending

    # Write candidates file
    safe_write_csv(candidates, candidates_file, OUTPUT_FIELDS)
        
    # Write approved file
    safe_write_csv(approved_records, approved_file, OUTPUT_FIELDS)

    return candidates
