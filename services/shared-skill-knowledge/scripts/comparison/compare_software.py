import os
from .utils import get_match_level

def compare_software(esco_skills, onet_software, existing_reviews=None):
    if existing_reviews is None:
        existing_reviews = {}
        
    matches = []
    matched_esco = set()
    matched_onet = set()
    
    report = {
        'exact_matches': 0,
        'alternative_matches': 0,
        'fuzzy_matches': 0,
        'unmatched_software': 0
    }
    
    from .utils import normalize_text

    for es in esco_skills:
        es['_names'] = [normalize_text(es.get('preferred_name', ''))] + [normalize_text(n) for n in es.get('alternative_labels', '').split('|') if n]

    for os_rec in onet_software:
        o_names = [os_rec.get('technology_example', ''), os_rec.get('preferred_name', '')]
        os_rec['_names'] = [normalize_text(n) for n in o_names if n]
        
        found_match = False
        for es in esco_skills:
            match_type, score = get_match_level(es['_names'], os_rec['_names'])
            if match_type:
                found_match = True
                matched_esco.add(es['esco_uri'])
                matched_onet.add(os_rec['onet_element_id'] + "::" + os_rec['technology_example'])
                
                # In software, the source_id might be empty, so we combine element_id and technology
                match_id = f"{es['esco_uri']}::{os_rec['onet_element_id']}::{os_rec['technology_example']}"
                existing = existing_reviews.get(match_id, {})
                
                matches.append({
                    'match_id': match_id,
                    'esco_uri': es['esco_uri'],
                    'esco_name': es.get('preferred_name', ''),
                    'esco_skill_type': es.get('skill_type', ''),
                    'onet_element_id': os_rec['onet_element_id'],
                    'onet_software_category': os_rec.get('preferred_name', ''),
                    'onet_technology_example': os_rec.get('technology_example', ''),
                    'match_method': match_type,
                    'match_score': round(score, 4),
                    'review_status': existing.get('review_status', 'PENDING_REVIEW'),
                    'review_notes': existing.get('review_notes', '')
                })
                
                if match_type == 'EXACT':
                    report['exact_matches'] += 1
                elif match_type == 'ALTERNATIVE':
                    report['alternative_matches'] += 1
                elif match_type == 'FUZZY':
                    report['fuzzy_matches'] += 1
                    
        if not found_match:
            report['unmatched_software'] += 1
            
    return matches, report
