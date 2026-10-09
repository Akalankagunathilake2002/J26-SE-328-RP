import csv
import os
import json
from typing import Dict, List, Any

OUTPUT_FIELDS = [
    'source',
    'source_version',
    'source_id',
    'onet_soc_code',
    'preferred_name',
    'description',
    'alternative_labels',
    'suggested_domain_code',
    'review_status',
    'review_notes'
]

def load_allowlist(config_dir: str) -> Dict[str, List[str]]:
    allowlist_path = os.path.join(config_dir, 'role_allowlist.json')
    if not os.path.exists(allowlist_path):
        return {}
    with open(allowlist_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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

def process_roles(input_dir: str, output_dir: str, report: Dict[str, Any], config_dir: str = None, source_version: str = "Unknown"):
    if config_dir is None:
        config_dir = os.path.dirname(os.path.abspath(__file__))
        
    occupations_file = os.path.join(input_dir, 'occupation_data.csv')
    titles_file = os.path.join(input_dir, 'job_titles.csv')
    candidates_file = os.path.join(output_dir, 'onet_roles_candidates.csv')
    approved_file = os.path.join(output_dir, 'onet_roles_approved.csv')

    if not os.path.exists(occupations_file):
        raise FileNotFoundError(f"Source file missing: {occupations_file}")

    allowlist_data = load_allowlist(config_dir)
    allowed_ids = {}
    for domain, items in allowlist_data.items():
        for item in items:
            if item not in allowed_ids:
                allowed_ids[item] = []
            allowed_ids[item].append(domain)

    # Load alternative titles
    alt_titles = {}
    if os.path.exists(titles_file):
        with open(titles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('O*NET-SOC Code')
                if not code:
                    continue
                title = row.get('Job Title', '').strip()
                if not title:
                    title = row.get('Title', '').strip()
                if title:
                    if code not in alt_titles:
                        alt_titles[code] = []
                    if title not in alt_titles[code]:
                        alt_titles[code].append(title)

    existing_reviews = load_existing_reviews(approved_file)
    existing_candidates = load_existing_reviews(candidates_file)
    for k, v in existing_reviews.items():
        existing_candidates[k] = v

    candidates = []
    approved_records = []
    domain_counts = {"IT": 0, "HR": 0, "BUSINESS": 0, "NONE": 0}

    read_count = 0
    with open(occupations_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            read_count += 1
            code = row.get('O*NET-SOC Code')
            if not code:
                continue

            existing = existing_candidates.get(code)
            
            is_allowed = code in allowed_ids or row.get('Title') in allowed_ids
            
            suggested_domains = allowed_ids.get(code, [])
            if not suggested_domains and row.get('Title') in allowed_ids:
                suggested_domains = allowed_ids[row.get('Title')]
                
            suggested_domain_code = ','.join(suggested_domains)
            
            review_status = 'PENDING_REVIEW'
            review_notes = ''
            final_domain = suggested_domain_code

            if existing:
                review_status = existing['review_status']
                review_notes = existing['review_notes']
                if existing['review_status'] not in ('PENDING', 'PENDING_REVIEW') and existing['suggested_domain_code']:
                    final_domain = existing['suggested_domain_code']

            # Only output candidates that are in the allowlist or were explicitly reviewed before
            if is_allowed or (existing and existing['review_status'] not in ('PENDING', 'PENDING_REVIEW')):
                record = {
                    'source': 'ONET',
                    'source_version': source_version,
                    'source_id': code,
                    'onet_soc_code': code,
                    'preferred_name': row.get('Title', ''),
                    'description': row.get('Description', ''),
                    'alternative_labels': '|'.join(alt_titles.get(code, [])),
                    'suggested_domain_code': final_domain,
                    'review_status': review_status,
                    'review_notes': review_notes
                }
                candidates.append(record)
                
                if review_status == 'APPROVED':
                    approved_records.append(record)
                    
                domains = final_domain.split(',') if final_domain else ["NONE"]
                for d in domains:
                    if d in domain_counts:
                        domain_counts[d] += 1
                    elif d:
                        domain_counts["NONE"] += 1

    report['source_occupations_read'] = read_count
    report['candidate_roles_generated'] = len(candidates)
    report['roles_by_domain'] = domain_counts
    
    approved = sum(1 for c in candidates if c['review_status'] == 'APPROVED')
    excluded = sum(1 for c in candidates if c['review_status'] == 'EXCLUDED')
    pending = sum(1 for c in candidates if c['review_status'] in ('PENDING', 'PENDING_REVIEW', 'NEEDS_REVIEW'))
    
    report['roles_approved'] = approved
    report['roles_excluded'] = excluded
    report['roles_pending'] = pending

    with open(candidates_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(candidates)
        
    with open(approved_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(approved_records)

    return candidates
