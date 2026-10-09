import os
import csv
import json
import re
from datetime import datetime

REGISTRY_FILE = os.path.join(os.getcwd(), 'scripts', 'import_prep', 'id_registry.json')
ID_REGISTRY = {}
if os.path.exists(REGISTRY_FILE):
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        ID_REGISTRY = json.load(f)

ID_COUNTERS = {
    'SK': 0,
    'RL': 0,
    'EXT': 0,
    'AL': 0,
    'DOM': 0
}

def generate_id(prefix, unique_key):
    if prefix not in ID_REGISTRY:
        ID_REGISTRY[prefix] = {}
    
    if unique_key in ID_REGISTRY[prefix]:
        return ID_REGISTRY[prefix][unique_key]
        
    if ID_COUNTERS[prefix] == 0 and ID_REGISTRY[prefix]:
        max_id = max(int(val.split('-')[1]) for val in ID_REGISTRY[prefix].values())
        ID_COUNTERS[prefix] = max_id
        
    ID_COUNTERS[prefix] += 1
    new_id = f"{prefix}-{ID_COUNTERS[prefix]:06d}"
    ID_REGISTRY[prefix][unique_key] = new_id
    return new_id

def save_registry():
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(ID_REGISTRY, f, indent=2)

def load_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_csv(records, filepath, fieldnames):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def normalize_alias(alias):
    return " ".join(alias.strip().split())

def main():
    base_dir = os.getcwd()
    esco_dir = os.path.join(base_dir, "seed/curated/esco")
    onet_dir = os.path.join(base_dir, "seed/curated/onet")
    comp_dir = os.path.join(base_dir, "seed/curated/comparison")
    out_dir = os.path.join(base_dir, "seed/import_ready")

    print("Loading data...")
    esco_roles = load_csv(os.path.join(esco_dir, "esco_roles_candidates.csv"))
    esco_skills = load_csv(os.path.join(esco_dir, "esco_skills_candidates.csv"))
    onet_roles = load_csv(os.path.join(onet_dir, "onet_roles_candidates.csv"))
    onet_skills = load_csv(os.path.join(onet_dir, "onet_skills_candidates.csv"))
    onet_software = load_csv(os.path.join(onet_dir, "onet_software_candidates.csv"))

    role_matches = load_csv(os.path.join(comp_dir, "role_matches.csv"))
    skill_matches = load_csv(os.path.join(comp_dir, "skill_matches.csv"))
    tech_matches = load_csv(os.path.join(comp_dir, "technology_matches.csv"))

    canonical_entities = []
    external_ids = []
    aliases_and_domains = []
    review_required = []
    
    # Process ESCO Roles
    for r in esco_roles:
        r_id = generate_id("RL", f"ESCO_ROLE_{r['esco_uri']}")
        review_status = 'PENDING_REVIEW' if r.get('review_status') != 'APPROVED' else 'APPROVED'
        
        canonical_entities.append({
            'id': r_id,
            'entity_type': 'ROLE',
            'name': r['preferred_name'],
            'description': r.get('description', ''),
            'skill_type': '',
            'concept_kind': 'ROLE',
            'review_status': review_status
        })
        
        external_ids.append({
            'id': generate_id("EXT", f"EXT_ROLE_{r['esco_uri']}"),
            'canonical_entity_id': r_id,
            'source_system': 'ESCO',
            'external_id': r['esco_uri'],
            'source_version': r.get('source_version', '')
        })
        
        seen_aliases = set()
        for raw_alias in re.split(r'[\n|;]+', r.get('alternative_labels', '')):
            alias = normalize_alias(raw_alias)
            if alias and alias.lower() not in seen_aliases:
                seen_aliases.add(alias.lower())
                aliases_and_domains.append({
                    'id': generate_id("AL", f"ALIAS_{r_id}_{alias}"),
                    'canonical_entity_id': r_id,
                    'record_type': 'ALIAS',
                    'value': alias,
                    'is_verified': 'false' if review_status == 'PENDING_REVIEW' else 'true'
                })
                
        for d in r.get('suggested_domain_code', '').split(','):
            d = d.strip()
            if d in ['IT', 'HR', 'BUSINESS']:
                aliases_and_domains.append({
                    'id': generate_id("DOM", f"DOMAIN_{r_id}_{d}"),
                    'canonical_entity_id': r_id,
                    'record_type': 'DOMAIN',
                    'value': d,
                    'is_verified': '1.0'
                })
            elif d:
                review_required.append({
                    'review_category': 'DOMAIN_UNKNOWN',
                    'entity_type': 'ROLE',
                    'entity_id': r_id,
                    'issue': f"Unknown domain '{d}'",
                    'source': 'ESCO'
                })

    # Process O*NET Roles
    for r in onet_roles:
        r_id = generate_id("RL", f"ONET_ROLE_{r['source_id']}")
        review_status = 'PENDING_REVIEW' if r.get('review_status') != 'APPROVED' else 'APPROVED'
        
        canonical_entities.append({
            'id': r_id,
            'entity_type': 'ROLE',
            'name': r['preferred_name'],
            'description': r.get('description', ''),
            'skill_type': '',
            'concept_kind': 'ROLE',
            'review_status': review_status
        })
        
        external_ids.append({
            'id': generate_id("EXT", f"EXT_ROLE_{r['source_id']}"),
            'canonical_entity_id': r_id,
            'source_system': 'ONET',
            'external_id': r['source_id'],
            'source_version': r.get('source_version', '')
        })
        
        seen_aliases = set()
        for raw_alias in re.split(r'[\n|;]+', r.get('alternative_labels', '')):
            alias = normalize_alias(raw_alias)
            if alias and alias.lower() not in seen_aliases:
                seen_aliases.add(alias.lower())
                aliases_and_domains.append({
                    'id': generate_id("AL", f"ALIAS_{r_id}_{alias}"),
                    'canonical_entity_id': r_id,
                    'record_type': 'ALIAS',
                    'value': alias,
                    'is_verified': 'false' if review_status == 'PENDING_REVIEW' else 'true'
                })
                
        for d in r.get('suggested_domain_code', '').split(','):
            d = d.strip()
            if d in ['IT', 'HR', 'BUSINESS']:
                aliases_and_domains.append({
                    'id': generate_id("DOM", f"DOMAIN_{r_id}_{d}"),
                    'canonical_entity_id': r_id,
                    'record_type': 'DOMAIN',
                    'value': d,
                    'is_verified': '1.0'
                })
            elif d:
                review_required.append({
                    'review_category': 'DOMAIN_UNKNOWN',
                    'entity_type': 'ROLE',
                    'entity_id': r_id,
                    'issue': f"Unknown domain '{d}'",
                    'source': 'ONET'
                })
                
    # Process ESCO Skills
    for s in esco_skills:
        s_id = generate_id("SK", f"ESCO_SKILL_{s['esco_uri']}")
        review_status = 'PENDING_REVIEW' if s.get('review_status') != 'APPROVED' else 'APPROVED'
        
        if not s.get('skill_type'):
            review_required.append({
                'review_category': 'MISSING_TYPE',
                'entity_type': 'SKILL',
                'entity_id': s_id,
                'issue': 'Missing skill_type',
                'source': 'ESCO'
            })

        concept_kind = 'OTHER_SKILL'
        name_lower = s['preferred_name'].lower()
        desc_lower = s.get('description', '').lower()
        skill_type = s.get('skill_type', '')

        if 'programming paradigms in' in desc_lower or '(computer programming)' in name_lower:
            concept_kind = 'PROGRAMMING_LANGUAGE'
        elif name_lower in ['c', 'c++', 'c#', 'java', 'javascript', 'python', 'ruby', 'go', 'rust', 'typescript', 'php', 'swift', 'kotlin']:
            concept_kind = 'PROGRAMMING_LANGUAGE'
        elif 'programming paradigm' in desc_lower or any(x in name_lower for x in ['object-oriented programming', 'logic programming', 'concurrent programming', 'scripting programming', 'automatic programming']):
            concept_kind = 'PROGRAMMING_PARADIGM'
        elif name_lower == 'computer programming' or 'web programming' in name_lower or ('programming' in name_lower and 'use ' in name_lower):
            concept_kind = 'PROGRAMMING_SKILL'
        elif 'framework' in name_lower or 'library' in name_lower or skill_type == 'Software':
            concept_kind = 'SOFTWARE_OR_TOOL'
        elif skill_type == 'knowledge':
            concept_kind = 'KNOWLEDGE'
            
        canonical_entities.append({
            'id': s_id,
            'entity_type': 'SKILL',
            'name': s['preferred_name'],
            'description': s.get('description', ''),
            'skill_type': skill_type,
            'concept_kind': concept_kind,
            'review_status': review_status
        })
        
        external_ids.append({
            'id': generate_id("EXT", f"EXT_SKILL_{s['esco_uri']}"),
            'canonical_entity_id': s_id,
            'source_system': 'ESCO',
            'external_id': s['esco_uri'],
            'source_version': s.get('source_version', '')
        })
        
        seen_aliases = set()
        for raw_alias in re.split(r'[\n|;]+', s.get('alternative_labels', '')):
            alias = normalize_alias(raw_alias)
            if alias and alias.lower() not in seen_aliases:
                seen_aliases.add(alias.lower())
                aliases_and_domains.append({
                    'id': generate_id("AL", f"ALIAS_{s_id}_{alias}"),
                    'canonical_entity_id': s_id,
                    'record_type': 'ALIAS',
                    'value': alias,
                    'is_verified': 'false' if review_status == 'PENDING_REVIEW' else 'true'
                })
                
        for d in s.get('suggested_domain_code', '').split(','):
            d = d.strip()
            if d in ['IT', 'HR', 'BUSINESS']:
                aliases_and_domains.append({
                    'id': generate_id("DOM", f"DOMAIN_{s_id}_{d}"),
                    'canonical_entity_id': s_id,
                    'record_type': 'DOMAIN',
                    'value': d,
                    'is_verified': '1.0'
                })
            elif d:
                review_required.append({
                    'review_category': 'DOMAIN_UNKNOWN',
                    'entity_type': 'SKILL',
                    'entity_id': s_id,
                    'issue': f"Unknown domain '{d}'",
                    'source': 'ESCO'
                })

    # Process ONET Skills
    for s in onet_skills:
        s_id = generate_id("SK", f"ONET_SKILL_{s['source_id']}")
        review_status = 'PENDING_REVIEW' if s.get('review_status') != 'APPROVED' else 'APPROVED'
        
        concept_kind = 'OTHER_SKILL'
        name_lower = s['preferred_name'].lower()
        skill_type = s.get('skill_type', '')
        
        if name_lower == 'computer programming':
            concept_kind = 'PROGRAMMING_SKILL'
        elif 'programming' in name_lower:
            concept_kind = 'PROGRAMMING_SKILL'
        elif skill_type == 'knowledge':
            concept_kind = 'KNOWLEDGE'
            
        canonical_entities.append({
            'id': s_id,
            'entity_type': 'SKILL',
            'name': s['preferred_name'],
            'description': s.get('description', ''),
            'skill_type': skill_type,
            'concept_kind': concept_kind,
            'review_status': review_status
        })
        
        external_ids.append({
            'id': generate_id("EXT", f"EXT_SKILL_{s['source_id']}"),
            'canonical_entity_id': s_id,
            'source_system': 'ONET',
            'external_id': s['source_id'],
            'source_version': s.get('source_version', '')
        })
        
        for d in s.get('suggested_domain_code', '').split(','):
            d = d.strip()
            if d in ['IT', 'HR', 'BUSINESS']:
                aliases_and_domains.append({
                    'id': generate_id("DOM", f"DOMAIN_{s_id}_{d}"),
                    'canonical_entity_id': s_id,
                    'record_type': 'DOMAIN',
                    'value': d,
                    'is_verified': '1.0'
                })
            elif d:
                review_required.append({
                    'review_category': 'DOMAIN_UNKNOWN',
                    'entity_type': 'SKILL',
                    'entity_id': s_id,
                    'issue': f"Unknown domain '{d}'",
                    'source': 'ONET'
                })

    # Process ONET Software
    for s in onet_software:
        unique_key = f"{s['onet_element_id']}::{s['technology_example']}"
        s_id = generate_id("SK", f"ONET_SOFTWARE_{unique_key}")
        review_status = 'PENDING_REVIEW' if s.get('review_status') != 'APPROVED' else 'APPROVED'
        
        canonical_entities.append({
            'id': s_id,
            'entity_type': 'SKILL',
            'name': s['technology_example'],
            'description': f"Software product/technology in category: {s['preferred_name']}",
            'skill_type': 'Software',
            'concept_kind': 'SOFTWARE_OR_TOOL',
            'review_status': review_status
        })
        
        external_ids.append({
            'id': generate_id("EXT", f"EXT_SKILL_{unique_key}"),
            'canonical_entity_id': s_id,
            'source_system': 'ONET_SOFTWARE',
            'external_id': unique_key,
            'source_version': s.get('source_version', '')
        })

    # Process Matches into review_required (as uncertain equivalence)
    for rm in role_matches:
        if rm.get('review_status', 'PENDING_REVIEW') != 'APPROVED':
            review_required.append({
                'review_category': 'ROLE_MATCH',
                'entity_type': 'ROLE',
                'entity_id': rm['match_id'],
                'issue': f"Unresolved {rm['match_method']} match between ESCO '{rm['esco_name']}' and ONET '{rm['onet_name']}'",
                'source': 'COMPARISON'
            })
            
    for sm in skill_matches:
        if sm.get('review_status', 'PENDING_REVIEW') != 'APPROVED':
            review_required.append({
                'review_category': 'SKILL_MATCH',
                'entity_type': 'SKILL',
                'entity_id': sm['match_id'],
                'issue': f"Unresolved {sm['match_method']} match between ESCO '{sm['esco_name']}' and ONET '{sm['onet_name']}'",
                'source': 'COMPARISON'
            })
            
    for tm in tech_matches:
        if tm.get('review_status', 'PENDING_REVIEW') != 'APPROVED':
            review_required.append({
                'review_category': 'TECHNOLOGY_MATCH',
                'entity_type': 'SKILL',
                'entity_id': tm['match_id'],
                'issue': f"Unresolved {tm['match_method']} match between ESCO '{tm['esco_name']}' and ONET '{tm['onet_technology_example']}'",
                'source': 'COMPARISON'
            })

    


    # Scrub bad aliases
    pl_names = set(re.sub(r'\(computer programming\)', '', ce['name'].lower()).strip() for ce in canonical_entities if ce.get('concept_kind') == 'PROGRAMMING_LANGUAGE')
    pl_names.update(['c', 'c++', 'c#', 'java', 'python', 'javascript', 'ruby', 'go', 'rust', 'typescript', 'php', 'swift', 'kotlin'])
    
    clean_ad = []
    for ad in aliases_and_domains:
        if ad['record_type'] == 'ALIAS':
            ce = next((c for c in canonical_entities if c['id'] == ad['canonical_entity_id']), None)
            if ce:
                ce_name_clean = re.sub(r'\(computer programming\)', '', ce['name'].lower()).strip()
                alias_clean = ad['value'].lower().strip()
                
                # Rule 1: computer programming shouldn't have PLs as aliases
                if ce_name_clean == 'computer programming':
                    if alias_clean in pl_names or (len(alias_clean) < 20 and 'programming' not in alias_clean and 'code' not in alias_clean and 'comput' not in alias_clean):
                        continue
                        
                # Rule 2: C, C++, C# cross-mapping prevention
                if ce_name_clean in ['c', 'c++', 'c#'] and alias_clean in ['c', 'c++', 'c#']:
                    if ce_name_clean != alias_clean:
                        continue
        clean_ad.append(ad)
    aliases_and_domains = clean_ad

    # Conflict Detection
    name_map = {}
    alias_map = {}
    
    for ce in canonical_entities:
        name = ce['name'].lower()
        if name not in name_map:
            name_map[name] = []
        name_map[name].append(ce['id'])
        
    for ad in aliases_and_domains:
        if ad['record_type'] == 'ALIAS':
            alias = ad['value'].lower()
            if alias not in alias_map:
                alias_map[alias] = []
            alias_map[alias].append(ad['canonical_entity_id'])
            
    for alias, ids in alias_map.items():
        unique_ids = list(set(ids))
        if len(unique_ids) > 1:
            for u_id in unique_ids:
                review_required.append({
                    'review_category': 'ALIAS_CONFLICT',
                    'entity_type': 'ALIAS',
                    'entity_id': u_id,
                    'issue': f"Alias '{alias}' is shared across multiple entities: {', '.join(unique_ids)}",
                    'source': 'VALIDATION'
                })
        
        if alias in name_map:
            for name_id in name_map[alias]:
                if name_id not in unique_ids:
                    for u_id in unique_ids:
                        review_required.append({
                            'review_category': 'ALIAS_CONFLICT',
                            'entity_type': 'ALIAS',
                            'entity_id': u_id,
                            'issue': f"Alias '{alias}' conflicts with preferred name of entity '{name_id}'",
                            'source': 'VALIDATION'
                        })

    print("Saving CSVs...")
    save_csv(canonical_entities, os.path.join(out_dir, "canonical_entities.csv"), ['id', 'entity_type', 'name', 'description', 'skill_type', 'concept_kind', 'review_status'])
    save_csv(external_ids, os.path.join(out_dir, "external_ids.csv"), ['id', 'canonical_entity_id', 'source_system', 'external_id', 'source_version'])
    save_csv(aliases_and_domains, os.path.join(out_dir, "aliases_and_domains.csv"), ['id', 'canonical_entity_id', 'record_type', 'value', 'is_verified'])
    save_csv(review_required, os.path.join(out_dir, "review_required.csv"), ['review_category', 'entity_type', 'entity_id', 'issue', 'source'])

    # Validation
    val_report = ["Import Data Validation Report", "=============================", ""]
    
    # 1. Check duplicate IDs
    all_entity_ids = [r['id'] for r in canonical_entities]
    if len(all_entity_ids) != len(set(all_entity_ids)):
        val_report.append("[ERROR] Duplicate Entity IDs found.")
    else:
        val_report.append("[PASS] Entity IDs are unique.")
        
    all_ext_ids = [e['id'] for e in external_ids]
    if len(all_ext_ids) != len(set(all_ext_ids)):
        val_report.append("[ERROR] Duplicate External IDs found.")
    else:
        val_report.append("[PASS] External IDs are unique.")

    # 2. Check FK consistency
    entity_id_set = set(all_entity_ids)
    
    fk_errors = 0
    for e in external_ids:
        if e['canonical_entity_id'] not in entity_id_set:
            val_report.append(f"[ERROR] Invalid canonical_entity_id in external_ids: {e['canonical_entity_id']}")
            fk_errors += 1
            
    for ad in aliases_and_domains:
        if ad['canonical_entity_id'] not in entity_id_set:
            val_report.append(f"[ERROR] Invalid canonical_entity_id in aliases_and_domains: {ad['canonical_entity_id']}")
            fk_errors += 1

    if fk_errors == 0:
        val_report.append("[PASS] All foreign keys are consistent.")

    with open(os.path.join(out_dir, "import_validation_report.txt"), "w") as f:
        f.write("\n".join(val_report))

    # Manifest
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "counts": {
            "canonical_entities": len(canonical_entities),
            "external_ids": len(external_ids),
            "aliases_and_domains": len(aliases_and_domains),
            "review_required": len(review_required)
        },
        "review_status": {
            "pending_entities": sum(1 for e in canonical_entities if e['review_status'] != 'APPROVED'),
            "review_required_items": len(review_required)
        }
    }
    
    with open(os.path.join(out_dir, "import_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Data Dictionary
    with open(os.path.join(out_dir, "data_dictionary.md"), "w") as f:
        f.write("""# Proposed SSKS Data Dictionary (Simplified)

## canonical_entities
| Column | Type | Description |
|---|---|---|
| id | String | Unique internal identifier (SK-###### or RL-######) |
| entity_type | String | 'ROLE' or 'SKILL' |
| name | String | Preferred name |
| description | Text | Description |
| skill_type | String | Category of concept (knowledge, skill/competence, Software) or empty |
| concept_kind | String | Differentiates PROGRAMMING_LANGUAGE, SOFTWARE_OR_TOOL, etc. |
| review_status | String | Current review status (PENDING_REVIEW, APPROVED) |

## external_ids
| Column | Type | Description |
|---|---|---|
| id | String | Unique internal identifier (EXT-######) |
| canonical_entity_id | String | FK to canonical_entities.id |
| source_system | String | Origin of data (ESCO, ONET, ONET_SOFTWARE) |
| external_id | String | Exact source URI, SOC code, or Element ID |
| source_version | String | Version of the source system data |

## aliases_and_domains
| Column | Type | Description |
|---|---|---|
| id | String | Unique internal identifier (AL-###### or DOM-######) |
| canonical_entity_id | String | FK to canonical_entities.id |
| record_type | String | 'ALIAS' or 'DOMAIN' |
| value | String | The alternative name or domain code (IT, HR, BUSINESS) |
| is_verified | String | 'true', 'false', or a confidence score like '1.0' |

## review_required
| Column | Type | Description |
|---|---|---|
| review_category | String | Broad classification of review item |\n| entity_type | String | Entity type associated with the issue |
| entity_id | String | Identifier associated with the issue |
| issue | Text | Description of the unresolved decision or conflict |
| source | String | Source triggering the flag (ESCO, ONET, COMPARISON) |
""")

    save_registry()
    print("Import preparation complete.")

if __name__ == "__main__":
    main()
