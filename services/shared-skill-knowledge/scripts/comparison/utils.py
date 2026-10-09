import os
import re
import csv
import tempfile
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    """Normalize text for matching by lowercasing, stripping whitespace, and removing punctuation."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())

def is_fuzzy_match(text1: str, text2: str, threshold: float = 0.85) -> bool:
    """Check if two strings are a fuzzy match based on SequenceMatcher ratio."""
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

def safe_write_csv(records, filepath, fieldnames):
    """Safely write records to a CSV file using a temporary file to avoid partial writes or locking errors."""
    if not records:
        return
        
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.csv')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        os.replace(temp_path, filepath)
    except PermissionError:
        os.remove(temp_path)
        raise PermissionError(f"Permission denied writing to {filepath}. Is the file open in another program like Excel?")
    except Exception as e:
        os.remove(temp_path)
        raise e

def load_csv(filepath):
    """Load a CSV file into a list of dictionaries."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def load_existing_reviews(filepath, id_field='match_id'):
    """Load existing reviews by their identifier."""
    records = load_csv(filepath)
    return {r[id_field]: r for r in records if r.get(id_field)}

def get_match_level(esco_norm, onet_norm):
    """
    Compare lists of pre-normalized names and return (match_type, score)
    match_type: EXACT, ALTERNATIVE, FUZZY, None
    """
    if not esco_norm or not onet_norm:
        return None, 0.0

    # Exact Match
    if esco_norm[0] == onet_norm[0]:
        return "EXACT", 1.0
        
    # Alternative Match (either primary matches any alternative, or any alternative matches primary)
    for e in esco_norm:
        for o in onet_norm:
            if e == o:
                return "ALTERNATIVE", 1.0
                
    # Fuzzy Match
    best_score = 0.0
    for e in esco_norm:
        le = len(e)
        for o in onet_norm:
            lo = len(o)
            # Max possible ratio
            max_ratio = 2.0 * min(le, lo) / (le + lo) if (le + lo) > 0 else 0
            if max_ratio < 0.85:
                continue
                
            score = SequenceMatcher(None, e, o).ratio()
            if score > best_score:
                best_score = score
                
    if best_score >= 0.85:
        return "FUZZY", best_score
        
    return None, 0.0
