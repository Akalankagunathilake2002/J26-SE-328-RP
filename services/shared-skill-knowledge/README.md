# Shared Skill Knowledge Service (SSKS)

## 1. Overview

The Shared Skill Knowledge Service (SSKS) is the central knowledge service of Skillaro. It maintains canonical skills, job roles, domains, aliases, external taxonomy identifiers, and directional relationships between skills.

SSKS provides a common source of skill knowledge so that each component does not need to maintain its own independent skill definitions.

### How it supports Skillaro

| Component | How it uses SSKS |
|---|---|
| C01 – Job Market Intelligence Engine | Normalizes skills extracted from job postings to canonical skill IDs. |
| C02 – Student Skill Profile Builder | Normalizes skills submitted by students. |
| C03 – Readiness Engine | Uses verified skill knowledge through a local cache for matching, skill-gap analysis, and readiness assessment. |
| C04 – Personalized Learning | Can use skill relationships, especially prerequisites, to support learning paths. |

**Boundary:** SSKS manages shared skill knowledge and its review workflows. It does not calculate student-job matching scores or career readiness scores.

## 2. Project Structure

The service is implemented using FastAPI, SQLAlchemy, and Pydantic.

```text
services/shared-skill-knowledge/
├── app/
│   ├── main.py
│   ├── config/
│   │   └── settings.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── core.py
│   │   ├── aliases.py
│   │   ├── relationships.py
│   │   ├── sources.py
│   │   └── candidates.py
│   ├── schemas/
│   │   ├── core.py
│   │   ├── normalization.py
│   │   ├── relationships.py
│   │   ├── candidates.py
│   │   └── snapshots.py
│   ├── repositories/
│   │   ├── core.py
│   │   ├── candidates.py
│   │   ├── relationships.py
│   │   └── snapshots.py
│   ├── services/
│   │   ├── core.py
│   │   ├── normalization.py
│   │   ├── candidates.py
│   │   ├── relationships.py
│   │   └── snapshots.py
│   └── api/
│       ├── dependencies.py
│       └── routers/
│           ├── domains.py
│           ├── skills.py
│           ├── roles.py
│           ├── skill_domains.py
│           ├── role_domains.py
│           ├── normalization.py
│           ├── candidates.py
│           ├── relationships.py
│           ├── candidate_relationships.py
│           └── snapshots.py
├── migrations/
├── scripts/
│   ├── db_import/
│   └── import_prep/
├── seed/
│   └── import_ready/
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

The structure follows a layered design:

- **Routers:** Define HTTP endpoints and handle requests and responses.
- **Schemas:** Validate incoming requests and shape API responses.
- **Services:** Implement business rules, normalization, validation, and review workflows.
- **Repositories:** Handle database queries and persistence.
- **Models:** Define the database entities and relationships.
- **Scripts and seed files:** Support offline data preparation and import.
- **Tests:** Check the API, business rules, review workflows, and snapshot behavior.

## 3. Main Data Concepts

| Concept | Purpose |
|---|---|
| Canonical skills | Authoritative skill records with stable `SK-xxxxxx` IDs. |
| Canonical roles | Authoritative job-role records with stable `RL-xxxxxx` IDs. |
| Domains | Group skills and roles into areas such as IT, HR, and Business. |
| Aliases | Store alternative names for canonical skills or roles. Only verified aliases are used for normalization. |
| External IDs | Connect canonical entities to identifiers from external taxonomies. |
| Knowledge sources | Record source systems such as ESCO, O*NET, and custom sources. |
| Skill relationships | Store typed, directional links between canonical skills. |
| Candidate entities | Hold proposed skills or roles awaiting review. |
| Candidate relationships | Hold proposed relationships awaiting review. |

A candidate is separate from a canonical entity until it is approved. In the current entity workflow, approval creates a canonical skill or role; approval as an alias is a possible future enhancement.

## 4. API Endpoints

All endpoints use the `/ssks` prefix. The following are the current documented endpoints; interactive documentation is available at `/ssks/docs`.

### 4.1 Health, skills, roles, and domains

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/ssks/health` | Check service health. |
| GET | `/ssks/domains/` | List domains. |
| POST | `/ssks/domains/` | Create a domain. |
| GET | `/ssks/skills/` | List skills, with pagination and filters. |
| GET | `/ssks/skills/{skill_id}` | Retrieve a skill by ID. |
| POST | `/ssks/skills/` | Create a canonical skill. |
| GET | `/ssks/roles/` | List roles, with pagination and filters. |
| GET | `/ssks/roles/{role_id}` | Retrieve a role by ID. |
| POST | `/ssks/roles/` | Create a canonical role. |

The list endpoints support pagination and applicable filters, including status and domain. The skills endpoint also supports skill type and skill nature filters.

**Note:** Update and delete operations for canonical skills and roles are planned enhancements, not part of the currently documented endpoint set.

### 4.2 Normalization

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ssks/normalize/skills` | Normalize a list of skill names. |
| POST | `/ssks/normalize/roles` | Normalize a list of role names. |

Normalization follows this order:

1. Standardize the input text.
2. Check for a canonical name match.
3. Check for a verified alias.
4. Return fuzzy similarity suggestions if no exact match is found.
5. Return `UNMATCHED` when no suitable match is found.

Fuzzy suggestions do not automatically create entities or confirm a match.

### 4.3 Candidate entity workflow

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ssks/candidates/entities` | Submit a candidate skill or role. |
| GET | `/ssks/candidates/entities` | List candidates with applicable filters. |
| GET | `/ssks/candidates/entities/{id}` | Retrieve a candidate. |
| PATCH | `/ssks/candidates/entities/{id}/review` | Approve or reject a candidate. |

The current workflow checks for duplicate canonical names, verified aliases, and pending candidates before accepting a submission.

When approved, a candidate becomes a canonical skill or role. When rejected, it remains a rejected candidate and does not become a canonical entity.

Review endpoints currently require a non-empty `X-Reviewer-Id` header. This is a placeholder check, not full authentication or role-based authorization.

### 4.4 Canonical skill relationships

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ssks/relationships` | Create a canonical skill relationship. |
| GET | `/ssks/relationships` | List relationships with filters. |
| GET | `/ssks/relationships/{id}` | Retrieve a relationship. |
| PATCH | `/ssks/relationships/{id}` | Update permitted relationship fields. |
| DELETE | `/ssks/relationships/{id}` | Delete a relationship. |

Supported types are `EQUIVALENT_TO`, `BROADER_THAN`, `NARROWER_THAN`, `PART_OF`, `PREREQUISITE_OF`, and `RELATED_TO`.

Relationships are directional. SSKS does not automatically create a reverse relationship. Self-referencing relationships and duplicate relationships of the same type are rejected.

### 4.5 Candidate relationship workflow

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ssks/candidates/relationships` | Submit a proposed relationship between existing skills. |
| GET | `/ssks/candidates/relationships` | List relationship candidates. |
| GET | `/ssks/candidates/relationships/{id}` | Retrieve a relationship candidate. |
| PATCH | `/ssks/candidates/relationships/{id}/review` | Approve or reject a proposed relationship. |

Approval creates a canonical verified relationship and marks the candidate as approved. Rejection does not create a canonical relationship.

Candidate relationship submissions can include a confidence score, source ID, and review note. These fields do not mean that an LLM-based relationship suggestion system is currently implemented.

### 4.6 Domain associations

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/ssks/skills/{skill_id}/domains` | List domains associated with a skill. |
| PUT | `/ssks/skills/{skill_id}/domains/{domain_id}` | Associate a skill with a domain. |
| DELETE | `/ssks/skills/{skill_id}/domains/{domain_id}` | Remove a skill-domain association. |
| GET | `/ssks/roles/{role_id}/domains` | List domains associated with a role. |
| PUT | `/ssks/roles/{role_id}/domains/{domain_id}` | Associate a role with a domain. |
| DELETE | `/ssks/roles/{role_id}/domains/{domain_id}` | Remove a role-domain association. |

These endpoints manage many-to-many domain associations separately from creating canonical skills or roles.

### 4.7 Knowledge snapshots

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/ssks/snapshots/export` | Export a knowledge snapshot. |
| POST | `/ssks/snapshots/export` | Alternative snapshot export endpoint. |
| GET | `/ssks/snapshots/metadata` | Retrieve snapshot version and entity counts. |
| GET | `/ssks/snapshots/validate` | Check whether a cached version is current. |

The `consumer` query parameter defaults to `SkillGap` in the current implementation. The consuming component is referred to here as the Readiness Engine (C03).

The current snapshot includes active skills and domains, verified aliases, verified relationships between active skills, skill-domain information, skill external identifiers, and registered knowledge sources. Skill descriptions are included in the export.

The version fingerprint helps detect changes in exported knowledge. The Readiness Engine is responsible for its own cache storage and synchronization schedule. Role snapshots are not currently included in the export schema.

## 5. Knowledge Flow

The intended flow between components is:

1. C01 and C02 submit skill or role names for normalization.
2. SSKS returns canonical matches, verified-alias matches, fuzzy suggestions, or unmatched results.
3. Unknown entities can be submitted for review instead of being added automatically.
4. Authorized review processes can promote approved candidates into canonical knowledge.
5. C03 retrieves a knowledge snapshot and maintains its own local cache.
6. C03 applies its matching and readiness rules using the relevant cached knowledge.

SSKS remains the authoritative source. A local cache in C03 is a copy used for performance, not a replacement for SSKS ownership.

## 6. Current Implementation and Limitations

The current implementation includes core entity endpoints, normalization, candidate workflows, relationship management, domain associations, and snapshot export and validation.

Important boundaries:

- Reviewer identity is checked through a header; full authentication and RBAC are not yet integrated.
- The documented test suite primarily uses SQLite. Live PostgreSQL behavior must be verified separately.
- The snapshot schema currently exports skill knowledge, not role snapshots.
- Snapshot export is on demand. Scheduled cache synchronization is the responsibility of the consuming component.
- Alias-specific candidate approval and comprehensive provenance management are not yet implemented.
- LLM-assisted relationship suggestions are a possible future enhancement, not a current SSKS capability.

## 7. Planned Improvements

### Authentication and permissions

Integrate the shared authentication service and enforce role-based permissions. For example, administrators could manage canonical knowledge, while designated reviewers could review candidate entities and relationships.

### Canonical entity lifecycle management

Add controlled update and delete operations for skills and roles, including safeguards for records referenced by aliases, relationships, external IDs, and consuming components.

### Alias review and provenance

Extend candidate review so an administrator can decide whether a submission should become a new canonical entity or an alias of an existing entity. Track the source, verification status, and review decision for each alias.

### Stronger relationship review

Allow reviewers to edit proposed relationship details, manage supporting evidence and sources, and efficiently submit or review multiple relationship proposals. Preserve the distinction between proposed and verified relationships.

### Improved source management

Support traceable provenance using taxonomy identifiers, source URLs, documents, or other evidence. Where appropriate, allow multiple relationships to be submitted with their respective sources.

### Optional LLM assistance

Investigate LLM-assisted relationship suggestions. Suggestions should be reviewed by an authorized person before becoming verified knowledge.

### Readiness Engine cache synchronization

Implement and test a daily or weekly cache refresh schedule in C03, using snapshot version validation to detect when its cached knowledge is outdated.

## 8. Setup and Testing

The service can be run locally using the Python dependencies in `requirements.txt` and Uvicorn:

```bash
cd services/shared-skill-knowledge
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

Open `http://localhost:8005/ssks/docs` to explore the API interactively.

Run the automated tests from the service directory:

```bash
pytest
```

The tests cover core APIs, normalization, candidate review, relationships, domain associations, snapshots, and seed/import validation. Passing SQLite-based tests does not by itself prove that the service has been integrated successfully with a live PostgreSQL instance.

## 9. Key Takeaway

**SSKS is the authoritative knowledge layer of Skillaro.** It centralizes canonical skills and roles, normalization, directional relationships, candidate review, and knowledge snapshot exports. The other components use this shared knowledge to perform their own tasks, while future authentication, provenance, alias-review, and synchronization improvements will strengthen the service's governance and integration.