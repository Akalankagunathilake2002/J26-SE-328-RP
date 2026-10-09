import os
from .utils import load_csv, safe_write_csv, get_match_level

def compare_skills(esco_skills, onet_skills, existing_reviews=None):
    if existing_reviews is None:
        existing_reviews = {}
        
    matches = []
    matched_esco = set()
    matched_onet = set()
    
    report = {
        'exact_matches': 0,
        'alternative_matches': 0,
        'fuzzy_matches': 0,
        'unmatched_esco': 0,
        'unmatched_onet': 0,
        'missing_esco_types': 0,
        'conflicting_domains': 0
    }
    
    from .utils import normalize_text
    
    for os_rec in onet_skills:
        os_rec['_names'] = [normalize_text(os_rec.get('preferred_name', ''))]
        os_rec['_domains'] = set(d.strip() for d in os_rec.get('suggested_domain_code', '').split(',') if d.strip())

    for es in esco_skills:
        if not es.get('skill_type'):
            report['missing_esco_types'] += 1
            
        e_names = [normalize_text(es.get('preferred_name', ''))] + [normalize_text(n) for n in es.get('alternative_labels', '').split('|') if n]
        e_domains = set(d.strip() for d in es.get('suggested_domain_code', '').split(',') if d.strip())
        
        for os_rec in onet_skills:
            match_type, score = get_match_level(e_names, os_rec['_names'])
            if match_type:
                matched_esco.add(es['esco_uri'])
                matched_onet.add(os_rec['source_id'])
                
                # Check for conflicting domains if both have domains
                conflict = False
                if e_domains and os_rec['_domains'] and not (e_domains & os_rec['_domains']):
                    conflict = True
                    report['conflicting_domains'] += 1
                
                match_id = f"{es['esco_uri']}::{os_rec['source_id']}"
                existing = existing_reviews.get(match_id, {})
                
                matches.append({
                    'match_id': match_id,
                    'esco_uri': es['esco_uri'],
                    'esco_name': es.get('preferred_name', ''),
                    'esco_skill_type': es.get('skill_type', ''),
                    'esco_domain': es.get('suggested_domain_code', ''),
                    'onet_source_id': os_rec['source_id'],
                    'onet_name': os_rec.get('preferred_name', ''),
                    'onet_skill_type': os_rec.get('skill_type', ''),
                    'onet_domain': os_rec.get('suggested_domain_code', ''),
                    'match_method': match_type,
                    'match_score': round(score, 4),
                    'domain_conflict': 'YES' if conflict else 'NO',
                    'review_status': existing.get('review_status', 'PENDING_REVIEW'),
                    'review_notes': existing.get('review_notes', '')
                })
                
                if match_type == 'EXACT':
                    report['exact_matches'] += 1
                elif match_type == 'ALTERNATIVE':
                    report['alternative_matches'] += 1
                elif match_type == 'FUZZY':
                    report['fuzzy_matches'] += 1
                    
    unmatched_esco = [r for r in esco_skills if r['esco_uri'] not in matched_esco]
    unmatched_onet = [r for r in onet_skills if r['source_id'] not in matched_onet]
    
    report['unmatched_esco'] = len(unmatched_esco)
    report['unmatched_onet'] = len(unmatched_onet)
    
    return matches, unmatched_esco, unmatched_onet, report
