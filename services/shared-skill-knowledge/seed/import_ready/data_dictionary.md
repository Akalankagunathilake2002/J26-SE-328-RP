# Proposed SSKS Data Dictionary (Simplified)

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
| review_category | String | Broad classification of review item |
| entity_type | String | Entity type associated with the issue |
| entity_id | String | Identifier associated with the issue |
| issue | Text | Description of the unresolved decision or conflict |
| source | String | Source triggering the flag (ESCO, ONET, COMPARISON) |
