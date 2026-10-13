# Shared Skill Knowledge Service

**Status:** not implemented yet. This README describes the plan; the code is added when
development starts.

## Purpose

The single, authoritative source of the skill and role knowledge that C01, C02, C03 and C04 all
use. No other service keeps its own copy of this knowledge.

It will own:

- **Canonical skill IDs** — e.g. `SK_001` for JavaScript
- **Canonical role IDs**
- **Skill aliases** — e.g. `"JS"` → JavaScript → `SK_001`
- **Skill categories** (domains)
- **Verified skill relationships** — each with a type, a direction and a verification status,
  e.g. Amazon Web Services (`SK_205`) → Cloud Computing (`SK_100`)

## Rules

- Relationships start as **pending** and are only shared with other services once **verified**.
- C03 uses verified relationships for its proposed readiness method. This service never
  calculates matching, skill gaps or readiness itself.
- There is one skill graph, here; no service builds its own.

## Works with

| Service | How |
|---|---|
| C01 Industry Skill Extraction | Looks up canonical skill and role IDs |
| C02 Student Skill Profile | Maps skill names and aliases to canonical skill IDs |
| C03 Skill Gap Analysis and Career Readiness | Reads verified skill relationships |
| C04 Learning Skill Tree | Reads relationships such as prerequisites to order learning paths |

## Plan

- Python, FastAPI, PostgreSQL (its own database), port **8005**
- Planned endpoints: `GET /skills/{skill_id}`, `GET /skills/search`,
  `GET /skills/{skill_id}/relationships`, `GET /roles/{role_id}`, `GET /roles/{role_id}/skills`
- Reached through the API gateway: add a route in `infrastructure/gateway/nginx.conf` (there is a
  commented example for this service) and the service in `infrastructure/docker-compose.yml`

## Database Migrations & Setup

- **Fresh Setup**: When running the FastAPI application against a clean database, `Base.metadata.create_all` automatically generates all tables with current columns and constraints (including `skill_nature` and `check_valid_skill_nature`).
- **Existing Database Upgrade**: To upgrade an existing database instance that lacks the `skill_nature` column, apply the idempotent SQL migration:
  ```bash
  psql -d <database_name> -f migrations/001_add_skill_nature_to_skills.sql
  ```
  The script safely adds `skill_nature VARCHAR(50)` and constraint `check_valid_skill_nature` only if not already present. It is safe to re-run multiple times.

