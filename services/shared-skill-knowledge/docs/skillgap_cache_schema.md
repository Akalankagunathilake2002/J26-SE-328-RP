# Skill Gap Analysis and Career Readiness Engine (`SkillGap`) Cache Schema Specification

## 1. Overview

The **Skill Gap Analysis and Career Readiness Engine (`SkillGap`)** consumes canonical skill entities, verified aliases, and verified directional relationships from the **Shared Skill Knowledge Service (SSKS)**.

To evaluate career readiness, identify skill gaps, and traverse skill hierarchies efficiently without repeated remote round-trips over the entire knowledge graph, SkillGap will maintain a local, read-only cache of SSKS data.

> **Note on Implementation Scope**:
> Neither the SkillGap service nor its database has been provisioned yet. The schema defined in this document is a **design specification only**. No database migrations or cache tables are created within SSKS.

---

## 2. SSKS Snapshot Export Endpoints

SSKS provides dedicated read-only endpoints under `/ssks/snapshots` for cache hydration and version validation:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/ssks/snapshots/export?consumer=SkillGap` | Exports complete, transaction-consistent knowledge snapshot payload |
| `POST` | `/ssks/snapshots/export?consumer=SkillGap` | Idempotent snapshot export endpoint for environments preferring POST |
| `GET` | `/ssks/snapshots/metadata?consumer=SkillGap` | Returns current snapshot ID, version hash, timestamp, and entity counts |
| `GET` | `/ssks/snapshots/validate?version={version}&consumer=SkillGap` | Checks whether a local cache version matches SSKS authoritative state |

### Consumer Identifier Convention
- **Default Consumer**: `SkillGap`
- **Formal Name**: Skill Gap Analysis and Career Readiness Engine
- **Snapshot ID Format**: `SNAP-SkillGap-v{YYYYMMDD}-{sha256_hash[:12]}` (e.g. `SNAP-SkillGap-v20261016-a1b2c3d4e5f6`)
- **Backward Compatibility**: Custom and legacy identifiers (such as `consumer=C03`) are accepted and generate corresponding snapshot IDs (`SNAP-C03-v...`).

---

## 3. Postman / cURL Examples

### 3.1 Check Cache Freshness (Metadata)
```http
GET /ssks/snapshots/metadata?consumer=SkillGap HTTP/1.1
Host: localhost:8005
Accept: application/json
```
```bash
curl -X GET "http://localhost:8005/ssks/snapshots/metadata?consumer=SkillGap" \
  -H "Accept: application/json"
```

**Response (`200 OK`)**:
```json
{
  "snapshot_id": "SNAP-SkillGap-v20261016-f3b18c0e2a91",
  "consumer": "SkillGap",
  "version": "v20261016-f3b18c0e2a91",
  "generated_at": "2026-10-16T18:00:00Z",
  "status": "ACTIVE",
  "counts": {
    "skills": 1688,
    "aliases": 2916,
    "relationships": 842,
    "domains": 1,
    "external_ids": 1723,
    "sources": 2
  },
  "source_metadata": [
    {
      "source_id": "SRC-ESCO",
      "source_code": "ESCO",
      "source_name": "European Skills, Competences, Qualifications and Occupations",
      "source_version": "1.2.1",
      "last_synced_at": null
    }
  ]
}
```

### 3.2 Validate Existing Local Cache Version
```http
GET /ssks/snapshots/validate?version=v20261016-f3b18c0e2a91&consumer=SkillGap HTTP/1.1
Host: localhost:8005
Accept: application/json
```
```bash
curl -X GET "http://localhost:8005/ssks/snapshots/validate?version=v20261016-f3b18c0e2a91&consumer=SkillGap" \
  -H "Accept: application/json"
```

**Response (`200 OK`)**:
```json
{
  "consumer": "SkillGap",
  "requested_version": "v20261016-f3b18c0e2a91",
  "current_version": "v20261016-f3b18c0e2a91",
  "is_current": true,
  "generated_at": "2026-10-16T18:00:00Z",
  "counts": {
    "skills": 1688,
    "aliases": 2916,
    "relationships": 842,
    "domains": 1,
    "external_ids": 1723,
    "sources": 2
  },
  "message": "Snapshot version is up to date with authoritative SSKS knowledge graph"
}
```

### 3.3 Download Full Snapshot Payload
```http
GET /ssks/snapshots/export?consumer=SkillGap HTTP/1.1
Host: localhost:8005
Accept: application/json
```
```bash
curl -X GET "http://localhost:8005/ssks/snapshots/export?consumer=SkillGap" \
  -H "Accept: application/json"
```

---

## 4. Proposed SkillGap Local Cache Schema (Design Specification)

When the SkillGap service is implemented, it will run on its own database. The proposed PostgreSQL schema below models the local cache tables needed to store the snapshot data for high-speed readiness calculations.

```sql
-- Design Specification Only: Future SkillGap Local Knowledge Cache
-- Target Database: skillgap_db (planned)

-- 1. Snapshot metadata ledger
CREATE TABLE IF NOT EXISTS skillgap_knowledge_snapshots (
    snapshot_id VARCHAR(100) PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    consumer VARCHAR(50) NOT NULL DEFAULT 'SkillGap',
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    imported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    skill_count INTEGER NOT NULL DEFAULT 0,
    alias_count INTEGER NOT NULL DEFAULT 0,
    relationship_count INTEGER NOT NULL DEFAULT 0,
    domain_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Cached canonical skills
CREATE TABLE IF NOT EXISTS skillgap_cached_skills (
    snapshot_version VARCHAR(50) NOT NULL,
    skill_id VARCHAR(50) NOT NULL,
    preferred_name VARCHAR(255) NOT NULL,
    skill_type VARCHAR(100) NOT NULL,
    skill_nature VARCHAR(50),
    domain_codes TEXT[] NOT NULL DEFAULT '{}',
    domain_ids TEXT[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (snapshot_version, skill_id),
    CONSTRAINT fk_cached_skills_snapshot
        FOREIGN KEY (snapshot_version)
        REFERENCES skillgap_knowledge_snapshots(version)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_skillgap_cached_skills_name
    ON skillgap_cached_skills (preferred_name);

-- 3. Cached verified aliases (for local fast normalization)
CREATE TABLE IF NOT EXISTS skillgap_cached_aliases (
    snapshot_version VARCHAR(50) NOT NULL,
    alias_id VARCHAR(50) NOT NULL,
    skill_id VARCHAR(50) NOT NULL,
    alias_text VARCHAR(255) NOT NULL,
    normalized_alias VARCHAR(255) NOT NULL,
    PRIMARY KEY (snapshot_version, alias_id),
    CONSTRAINT fk_cached_aliases_snapshot
        FOREIGN KEY (snapshot_version)
        REFERENCES skillgap_knowledge_snapshots(version)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_skillgap_cached_aliases_normalized
    ON skillgap_cached_aliases (normalized_alias);

-- 4. Cached verified directional skill relationships
CREATE TABLE IF NOT EXISTS skillgap_cached_relationships (
    snapshot_version VARCHAR(50) NOT NULL,
    relationship_id VARCHAR(50) NOT NULL,
    source_skill_id VARCHAR(50) NOT NULL,
    target_skill_id VARCHAR(50) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'VERIFIED',
    evidence_note TEXT,
    source_id VARCHAR(50),
    PRIMARY KEY (snapshot_version, relationship_id),
    CONSTRAINT fk_cached_relationships_snapshot
        FOREIGN KEY (snapshot_version)
        REFERENCES skillgap_knowledge_snapshots(version)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_skillgap_cached_rel_source
    ON skillgap_cached_relationships (snapshot_version, source_skill_id);

CREATE INDEX IF NOT EXISTS ix_skillgap_cached_rel_target
    ON skillgap_cached_relationships (snapshot_version, target_skill_id);

CREATE INDEX IF NOT EXISTS ix_skillgap_cached_rel_type
    ON skillgap_cached_relationships (snapshot_version, relationship_type);
```

---

## 5. Architectural Guarantees & Semantics

1. **Strictly Verified Data**: SSKS snapshot export includes only records with `verification_status = 'VERIFIED'` and `status = 'ACTIVE'`. Pending candidate entities and candidate relationships are excluded.
2. **Directionality Preservation**: Skill relationships maintain strict directional semantics:
   - `PREREQUISITE_OF`: `source_skill_id` is a prerequisite for `target_skill_id`.
   - `BROADER_THAN` / `NARROWER_THAN`: Strict hierarchical direction.
   - `RELATED_TO`: Conceptual association only.
   - Reverse records are not automatically synthesized by SSKS.
3. **Deterministic Versioning**: The version string `v{YYYYMMDD}-{hash[:12]}` is derived by computing a SHA-256 digest over the sorted canonical IDs, ensuring that identical SSKS state generates identical version strings.
4. **Zero-Downtime Cache Rotation**: SkillGap can ingest new snapshots into an inactive version partition, verify record integrity, and atomically swap `is_active = TRUE` to the new version.
