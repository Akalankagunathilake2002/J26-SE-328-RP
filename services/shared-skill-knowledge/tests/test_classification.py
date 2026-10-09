import os
import csv
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IMPORT_READY_DIR = os.path.join(BASE_DIR, 'seed', 'import_ready')

def load_csv(filename):
    path = os.path.join(IMPORT_READY_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

@pytest.fixture(scope="module")
def entities():
    return load_csv('canonical_entities.csv')

@pytest.fixture(scope="module")
def aliases():
    return [a for a in load_csv('aliases_and_domains.csv') if a['record_type'] == 'ALIAS']

def test_programming_languages_distinct_from_general(entities, aliases):
    # Find computer programming entity
    cp = next((e for e in entities if e['name'].lower() == 'computer programming'), None)
    assert cp is not None, "Computer programming concept must exist"
    
    # Get its aliases
    cp_aliases = [a['value'].lower() for a in aliases if a['canonical_entity_id'] == cp['id']]
    
    # Ensure known PLs are not in its aliases
    pls = ['java', 'python', 'c', 'c++', 'c#', 'javascript', 'ruby']
    for pl in pls:
        assert pl not in cp_aliases, f"{pl} should not be an alias of computer programming"

def test_c_cpp_csharp_distinct(entities, aliases):
    # Find C, C++, C#
    c_entities = [e for e in entities if e['name'].lower() == 'c']
    cpp_entities = [e for e in entities if e['name'].lower() == 'c++']
    csharp_entities = [e for e in entities if e['name'].lower() == 'c#']
    
    assert len(c_entities) > 0, "C concept must exist"
    assert len(cpp_entities) > 0, "C++ concept must exist"
    assert len(csharp_entities) > 0, "C# concept must exist"
    
    # Ensure they don't share IDs
    c_ids = set(e['id'] for e in c_entities)
    cpp_ids = set(e['id'] for e in cpp_entities)
    csharp_ids = set(e['id'] for e in csharp_entities)
    
    assert c_ids.isdisjoint(cpp_ids), "C and C++ must have distinct IDs"
    assert c_ids.isdisjoint(csharp_ids), "C and C# must have distinct IDs"
    assert cpp_ids.isdisjoint(csharp_ids), "C++ and C# must have distinct IDs"

def test_original_classifications_preserved(entities):
    # Check that skill_type is preserved (not overwritten by concept_kind)
    for e in entities:
        if e['entity_type'] == 'SKILL':
            # It should have skill_type and concept_kind separated
            assert 'skill_type' in e
            assert 'concept_kind' in e
            assert e['concept_kind'] in ['PROGRAMMING_LANGUAGE', 'PROGRAMMING_SKILL', 'PROGRAMMING_PARADIGM', 'SOFTWARE_OR_TOOL', 'KNOWLEDGE', 'OTHER_SKILL', 'ROLE']

def test_no_dangling_references(entities, aliases):
    entity_ids = set(e['id'] for e in entities)
    for a in aliases:
        assert a['canonical_entity_id'] in entity_ids, f"Dangling reference: {a['canonical_entity_id']}"
