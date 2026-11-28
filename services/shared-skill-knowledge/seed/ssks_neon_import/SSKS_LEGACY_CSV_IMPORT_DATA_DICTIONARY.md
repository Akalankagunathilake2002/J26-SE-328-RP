# SSKS Legacy Database Structure & CSV Import Reference

**Purpose:** Explain the legacy SSKS (`ssks_db`) table structures so an implementation agent can inspect and import the existing CSV seed data safely.

**Source of the legacy schema:** *Skillaro-Database-Tables-by-Schema.pdf*, pages 2–3. The PDF identifies the existing SSKS structure as 13 tables and describes the schema as read from the model code on `main` at commit `b4215a5` (22 Nov 2026).

**Important scope note:** This document describes the **old SSKS table structure**. It is not the new Neon contract. In this legacy structure, the IDs shown below are `varchar(50)` unless otherwise stated. The new Neon setup may change some internal IDs to UUIDs. Do not assume the old CSV values can be inserted unchanged into the new schema.

---

## 1. Import safety rules — read before doing anything

1. Treat `seed/import_ready/` as the **source-data directory**. Its existing CSV files must be preserved.
2. Do not delete, rename, move, overwrite, reformat, or edit the original CSV files.
3. Do not generate replacement CSVs inside `seed/import_ready/`.
4. First inspect and report:
   - every CSV filename;
   - its exact header row;
   - row count;
   - delimiter and text encoding;
   - empty/null values;
   - duplicate primary keys;
   - duplicate natural keys;
   - references to IDs that do not exist in the parent CSV/table.
5. Do not guess a CSV-to-table mapping from filenames alone. Confirm it from the actual headers and sample rows.
6. Do not run an import, migration, `TRUNCATE`, `DELETE`, `DROP`, or schema-changing SQL until the mapping and target database have been explicitly confirmed.
7. Keep the original legacy ID in the import mapping/audit output whenever an ID is converted to a UUID. This is needed to trace a new ID back to its original CSV value.
8. Make the importer repeatable (idempotent): running it again must not create duplicate records or generate different UUIDs for the same legacy record.
9. Validate parent records before importing child records. Do not silently discard rows with missing references.
10. Never assume the legacy schema below is identical to the current Neon `setup.sql`. Compare the actual target schema before writing data.

---

## 2. Legacy SSKS table inventory

The legacy SSKS database contains these 13 tables:

| # | Table | Purpose | Primary key |
|---:|---|---|---|
| 1 | `domains` | Skill/role knowledge domains such as IT, HR and Business | `domain_id` |
| 2 | `knowledge_sources` | External or internal sources such as ESCO, O*NET or custom sources | `source_id` |
| 3 | `skills` | Canonical skills; IDs use the `SK-...` format | `skill_id` |
| 4 | `roles` | Canonical job roles; IDs use the `RL-...` format | `role_id` |
| 5 | `skill_aliases` | Alternative names for canonical skills | `alias_id` |
| 6 | `role_aliases` | Alternative names for canonical roles | `alias_id` |
| 7 | `skill_domains` | Many-to-many mapping between skills and domains | (`skill_id`, `domain_id`) |
| 8 | `role_domains` | Many-to-many mapping between roles and domains | (`role_id`, `domain_id`) |
| 9 | `skill_relationships` | Typed, directional links between canonical skills | `relationship_id` |
| 10 | `candidate_entities` | Proposed new skills or roles awaiting review | `candidate_entity_id` |
| 11 | `candidate_skill_relationships` | Proposed skill-to-skill relationships awaiting review | `candidate_relationship_id` |
| 12 | `skill_external_ids` | External taxonomy identifiers for skills | `external_id_id` |
| 13 | `role_external_ids` | External taxonomy identifiers for roles | `external_id_id` |

The field definitions below reproduce the legacy table structure shown in the PDF. `NOT NULL` is shown only where the PDF marks a column as required. A blank/unspecified nullable field should not be treated as required without checking the actual legacy model or database.

---

## 3. Legacy table definitions

### 3.1 `domains`

**Purpose:** Areas such as IT, HR and Business.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `domain_id` | `varchar(50)` | PK, required | Stable domain identifier, e.g. `DOM-IT` |
| `name` | `varchar(255)` | — | Display name |
| `code` | `varchar(50)` | Required | Short domain code |
| `description` | `text` | — | Domain description |
| `status` | `varchar(50)` | Required | Domain status |

### 3.2 `knowledge_sources`

**Purpose:** Records where imported or verified knowledge came from (for example ESCO, O*NET or custom sources).

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `source_id` | `varchar(50)` | PK, required | Legacy source ID, e.g. `SRC-ESCO` |
| `source_code` | `varchar(100)` | Required | Source code |
| `source_name` | `varchar(255)` | Required | Human-readable source name |
| `source_version` | `varchar(100)` | — | Version of the source dataset |
| `last_synced_at` | `timestamptz` | — | Last synchronization time |

### 3.3 `skills`

**Purpose:** Canonical skill records. Skill IDs use the `SK-xxxxxx` format and should be preserved when migrating existing skills.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `skill_id` | `varchar(50)` | PK, required | Canonical skill ID, e.g. `SK-000001` |
| `preferred_name` | `varchar(255)` | Required | Canonical/display name |
| `description` | `text` | — | Skill description |
| `skill_type` | `varchar(100)` | Required | Skill classification |
| `skill_nature` | `varchar(50)` | — | Nature/category of the skill |
| `status` | `varchar(50)` | Required | Current skill status |
| `created_at` | `timestamptz` | Required | Creation timestamp |
| `updated_at` | `timestamptz` | Required | Last update timestamp |

### 3.4 `roles`

**Purpose:** Canonical job roles. Role IDs use the `RL-xxxxxx` format and should be preserved when migrating existing roles.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `role_id` | `varchar(50)` | PK, required | Canonical role ID, e.g. `RL-000001` |
| `preferred_name` | `varchar(255)` | Required | Canonical/display role name |
| `description` | `text` | — | Role description |
| `status` | `varchar(50)` | Required | Current role status |
| `created_at` | `timestamptz` | Required | Creation timestamp |
| `updated_at` | `timestamptz` | — | Last update timestamp |

### 3.5 `skill_aliases`

**Purpose:** Alternative names or terms for canonical skills.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `alias_id` | `varchar(50)` | PK, required | Legacy alias ID |
| `skill_id` | `varchar(50)` | FK, required | References `skills.skill_id` |
| `alias_text` | `varchar(255)` | Required | Original alias text |
| `normalized_alias` | `varchar(255)` | Required | Normalized alias used for matching |
| `source_id` | `varchar(50)` | FK | References `knowledge_sources.source_id` |
| `verification_status` | `varchar(50)` | Required | Alias verification state |

### 3.6 `role_aliases`

**Purpose:** Alternative names or terms for canonical roles.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `alias_id` | `varchar(50)` | PK, required | Legacy role-alias ID |
| `role_id` | `varchar(50)` | FK, required | References `roles.role_id` |
| `alias_text` | `varchar(255)` | Required | Original alias text |
| `normalized_alias` | `varchar(255)` | Required | Normalized alias used for matching |
| `source_id` | `varchar(50)` | FK | References `knowledge_sources.source_id` |
| `verification_status` | `varchar(50)` | Required | Alias verification state |

### 3.7 `skill_domains`

**Purpose:** Many-to-many mapping of skills to domains.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `skill_id` | `varchar(50)` | Composite PK, FK, required | References `skills.skill_id` |
| `domain_id` | `varchar(50)` | Composite PK, FK, required | References `domains.domain_id` |

### 3.8 `role_domains`

**Purpose:** Many-to-many mapping of roles to domains.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `role_id` | `varchar(50)` | Composite PK, FK, required | References `roles.role_id` |
| `domain_id` | `varchar(50)` | Composite PK, FK, required | References `domains.domain_id` |

### 3.9 `skill_relationships`

**Purpose:** Typed, directional links between canonical skills. Example relationship type shown in the PDF: `PART_OF`.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `relationship_id` | `varchar(50)` | PK, required | Legacy relationship ID |
| `source_skill_id` | `varchar(50)` | FK, required | Source skill; references `skills.skill_id` |
| `target_skill_id` | `varchar(50)` | FK, required | Target skill; references `skills.skill_id` |
| `relationship_type` | `varchar(50)` | Required | Type of directional relationship |
| `verification_status` | `varchar(50)` | Required | Verification state |
| `source_id` | `varchar(50)` | FK | References `knowledge_sources.source_id` |
| `evidence_note` | `text` | — | Evidence note |
| `evidence_description` | `text` | — | Detailed evidence description |
| `evidence_url` | `varchar(500)` | — | Evidence URL |
| `reviewed_by` | `varchar(100)` | — | Reviewer identifier in the legacy structure |
| `created_at` | `timestamptz` | Required | Creation timestamp |
| `updated_at` | `timestamptz` | Required | Last update timestamp |

**Important:** Relationships are directional. Do not reverse `source_skill_id` and `target_skill_id` during import.

### 3.10 `candidate_entities`

**Purpose:** Proposed new skills or roles waiting for review.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `candidate_entity_id` | `varchar(50)` | PK, required | Legacy candidate entity ID |
| `entity_type` | `varchar(20)` | Required | Entity kind (skill or role) |
| `submitted_name` | `varchar(255)` | Required | Submitted name |
| `normalized_name` | `varchar(255)` | Required | Normalized submitted name |
| `description` | `text` | — | Candidate description |
| `proposed_skill_type` | `varchar(100)` | — | Proposed skill type, when applicable |
| `proposed_skill_nature` | `varchar(50)` | — | Proposed skill nature, when applicable |
| `source_component` | `varchar(50)` | — | Component that submitted the candidate |
| `source_reference` | `varchar(255)` | — | Reference in the submitting component |
| `review_status` | `varchar(50)` | Required | Review state |
| `review_note` | `text` | — | Reviewer note |
| `matched_entity_id` | `varchar(50)` | — | Existing canonical entity matched to this candidate, if any |
| `created_at` | `timestamptz` | Required | Creation timestamp |
| `reviewed_at` | `timestamptz` | — | Review timestamp |

### 3.11 `candidate_skill_relationships`

**Purpose:** Proposed skill relationships waiting for review.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `candidate_relationship_id` | `varchar(50)` | PK, required | Legacy candidate relationship ID |
| `source_skill_id` | `varchar(50)` | FK, required | Source skill; references `skills.skill_id` |
| `target_skill_id` | `varchar(50)` | FK, required | Target skill; references `skills.skill_id` |
| `proposed_relationship_type` | `varchar(50)` | Required | Proposed relationship type |
| `confidence_score` | `float` | — | Confidence score |
| `review_status` | `varchar(50)` | Required | Review state |
| `source_id` | `varchar(50)` | FK | References `knowledge_sources.source_id` |
| `review_note` | `text` | — | Reviewer note |
| `evidence_description` | `text` | — | Evidence description |
| `evidence_url` | `varchar(500)` | — | Evidence URL |
| `reviewed_by` | `varchar(100)` | — | Reviewer identifier in the legacy structure |
| `canonical_relationship_id` | `varchar(50)` | FK | References `skill_relationships.relationship_id`, when linked |
| `created_at` | `timestamptz` | Required | Creation timestamp |
| `reviewed_at` | `timestamptz` | — | Review timestamp |

### 3.12 `skill_external_ids`

**Purpose:** External taxonomy identifiers associated with canonical skills.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `external_id_id` | `varchar(50)` | PK, required | Legacy external-ID record ID |
| `skill_id` | `varchar(50)` | FK, required | References `skills.skill_id` |
| `source_id` | `varchar(50)` | FK, required | References `knowledge_sources.source_id` |
| `external_identifier` | `varchar(255)` | Required | Identifier used by the external source |

### 3.13 `role_external_ids`

**Purpose:** External taxonomy identifiers associated with canonical roles.

| Column | Legacy type | Key / requirement | Meaning |
|---|---|---|---|
| `external_id_id` | `varchar(50)` | PK, required | Legacy external-ID record ID |
| `role_id` | `varchar(50)` | FK, required | References `roles.role_id` |
| `source_id` | `varchar(50)` | FK, required | References `knowledge_sources.source_id` |
| `external_identifier` | `varchar(255)` | Required | Identifier used by the external source |

---

## 4. Legacy foreign-key relationships

Use these relationships to validate references and determine import order.

| Child table.column | Parent table.column |
|---|---|
| `skill_aliases.skill_id` | `skills.skill_id` |
| `skill_aliases.source_id` | `knowledge_sources.source_id` |
| `role_aliases.role_id` | `roles.role_id` |
| `role_aliases.source_id` | `knowledge_sources.source_id` |
| `skill_domains.skill_id` | `skills.skill_id` |
| `skill_domains.domain_id` | `domains.domain_id` |
| `role_domains.role_id` | `roles.role_id` |
| `role_domains.domain_id` | `domains.domain_id` |
| `skill_relationships.source_skill_id` | `skills.skill_id` |
| `skill_relationships.target_skill_id` | `skills.skill_id` |
| `skill_relationships.source_id` | `knowledge_sources.source_id` |
| `candidate_entities.matched_entity_id` | Potential canonical entity reference; verify actual model/constraint before treating it as an FK |
| `candidate_skill_relationships.source_skill_id` | `skills.skill_id` |
| `candidate_skill_relationships.target_skill_id` | `skills.skill_id` |
| `candidate_skill_relationships.source_id` | `knowledge_sources.source_id` |
| `candidate_skill_relationships.canonical_relationship_id` | `skill_relationships.relationship_id` |
| `skill_external_ids.skill_id` | `skills.skill_id` |
| `skill_external_ids.source_id` | `knowledge_sources.source_id` |
| `role_external_ids.role_id` | `roles.role_id` |
| `role_external_ids.source_id` | `knowledge_sources.source_id` |

**Note:** `matched_entity_id` is shown as a column in the PDF, but the PDF does not mark it as an FK. Verify the actual legacy SQLAlchemy model/database constraint before enforcing it as one.

---

## 5. Suggested parent-first import sequence

This is a dependency-based order, not a claim about the current CSV filenames. Confirm which CSV files actually exist before mapping.

1. `domains`
2. `knowledge_sources`
3. `skills`
4. `roles`
5. `skill_domains`
6. `role_domains`
7. `skill_aliases`
8. `role_aliases`
9. `skill_relationships`
10. `candidate_entities`
11. `candidate_skill_relationships`
12. `skill_external_ids`
13. `role_external_ids`

The order of independent child tables can be adjusted. Parent records must exist before dependent rows are inserted.

---

## 6. Legacy IDs versus the new Neon contract

The legacy schema in this reference uses string IDs for all SSKS identifiers, including:

- canonical skills: `SK-...`
- canonical roles: `RL-...`
- domains: `DOM-...`
- sources: `SRC-...`
- aliases: legacy alias IDs such as `AL-...`
- relationships: legacy relationship IDs such as `REL-...`
- candidate entities: legacy candidate IDs such as `CE-...`
- candidate relationships: legacy candidate relationship IDs such as `CR-...`

The newer Neon `setup.sql` inspected separately proposes UUID columns for some internal identifiers, including `source_id`, `alias_id`, `relationship_id`, `candidate_entity_id`, and `candidate_relationship_id`.

Therefore:

- Preserve canonical `SK-...` and `RL-...` IDs if that is the agreed contract.
- Do not insert legacy `SRC-...`, `AL-...`, `REL-...`, `CE-...`, or `CR-...` strings into UUID columns.
- If the team approves UUID conversion, define one deterministic mapping function and use it consistently for primary keys and every corresponding foreign key.
- Keep a mapping/audit file or table with at least `entity_type`, `legacy_id`, and `new_uuid`.
- Do not generate random replacement UUIDs independently in different CSV import steps.
- Confirm the `reviewed_by` type and value format with the team before importing reviewer values.

---

## 7. CSV inspection and validation checklist for the import agent

Before writing an importer, produce a mapping report with one section per CSV:

| Check | Required result |
|---|---|
| CSV filename | Exact filename under `seed/import_ready/` |
| Target table | One of the 13 legacy SSKS tables, or explicitly flagged as unmapped |
| Header | Exact header names and order |
| Row count | Count of data rows, excluding header |
| Encoding/delimiter | Detected and reported |
| Primary key | Present, non-empty and unique |
| Required fields | No unexpected blanks |
| Foreign keys | Every non-null reference resolves to a parent record |
| IDs | Legacy format validated; conversion mapping documented if needed |
| Duplicates | Duplicate rows and duplicate natural keys reported |
| Unknown columns | Reported; never silently dropped |
| Missing columns | Reported; never silently invented |
| Target compatibility | Every mapped field checked against the actual Neon table type and nullability |

### Expected validation examples

- Every `skill_aliases.skill_id` must resolve to an imported `skills.skill_id`.
- Every `role_aliases.role_id` must resolve to an imported `roles.role_id`.
- Every relationship endpoint must resolve to an imported skill.
- Every non-null source reference must resolve to an imported knowledge source.
- Every external-ID row must resolve to its canonical skill/role and source.
- Every converted legacy UUID must map to exactly one stable UUID.
- Re-running the import must leave record counts and identifiers unchanged.

---

## 8. Instructions to the implementation agent

Use this file as the **legacy schema/data dictionary**, not as permission to modify or import data.

The agent should:

1. Inspect the SSKS service code and actual files in `seed/import_ready/`.
2. Inspect the current Neon `setup.sql` and compare its SSKS tables/columns/types against this legacy reference.
3. Produce a CSV inventory and exact CSV-to-table/column mapping.
4. Identify every schema mismatch, missing field, extra field, ID conversion and FK dependency.
5. Propose a safe, repeatable importer and a validation/dry-run mode.
6. Preserve the original CSV files in `seed/import_ready/`.
7. Make no changes to source CSVs and execute no import until explicitly authorized.

**Do not assume the CSV files contain exactly one file per table.** Some tables may be combined, split across files, generated by scripts, or absent. Determine this from the actual directory contents and CSV headers.

**Do not infer missing data or silently discard unmapped columns/rows.** Report ambiguities and ask for a decision.
