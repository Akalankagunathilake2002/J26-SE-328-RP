import os
from .utils import load_csv, safe_write_csv, get_match_level

def compare_roles(esco_roles, onet_roles, existing_reviews=None):
    """
    Compare ESCO roles and O*NET roles.
    Returns: matches, unmatched_esco, unmatched_onet, report
    """
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
        'unmatched_onet': 0
    }
    
    from .utils import normalize_text
    
    # Pre-normalize O*NET roles
    for orole in onet_roles:
        orole['_names'] = [normalize_text(orole.get('preferred_name', ''))] + [normalize_text(n) for n in orole.get('alternative_labels', '').split('|') if n]

    # Iterate over ESCO roles
    for er in esco_roles:
        e_names = [normalize_text(er.get('preferred_name', ''))] + [normalize_text(n) for n in er.get('alternative_labels', '').split('|') if n]
        
        found_match = False
        for orole in onet_roles:
            match_type, score = get_match_level(e_names, orole['_names'])
            if match_type:
                found_match = True
                matched_esco.add(er['esco_uri'])
                matched_onet.add(orole['source_id'])
                
                match_id = f"{er['esco_uri']}::{orole['source_id']}"
                existing = existing_reviews.get(match_id, {})
                
                matches.append({
                    'match_id': match_id,
                    'esco_uri': er['esco_uri'],
                    'esco_name': er.get('preferred_name', ''),
                    'onet_source_id': orole['source_id'],
                    'onet_name': orole.get('preferred_name', ''),
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
                    
    unmatched_esco = [r for r in esco_roles if r['esco_uri'] not in matched_esco]
    unmatched_onet = [r for r in onet_roles if r['source_id'] not in matched_onet]
    
    report['unmatched_esco'] = len(unmatched_esco)
    report['unmatched_onet'] = len(unmatched_onet)
    
    return matches, unmatched_esco, unmatched_onet, report
