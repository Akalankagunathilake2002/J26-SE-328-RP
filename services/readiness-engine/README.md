# Skill Gap Analysis and Career Readiness Engine (`readiness-engine`)

**Component:** C03 — Skill Gap Analysis and Career Readiness Engine

The Readiness Engine evaluates career readiness, identifies skill gaps, and prioritizes learning needs. It compares standardized industry skill profiles from C01 with user skill profiles from C02, referencing canonical skill and role identifiers from the Shared Skill Knowledge Service (SSKS).

## Responsibilities

- Receive and validate industry skill profile targets from C01.
- Ingest and evaluate user skill evidence and proficiency profiles from C02.
- Perform skill gap analysis and compute readiness scores.
- Determine high-priority learning recommendations for downstream consumption by C04 (Learning Skill Tree).

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Root health check |
| `/readiness/health` | `GET` | Service health status under service prefix |
| `/analyses` | `POST` | Execute analysis pipeline and return C04 contract |
| `/analyses` | `GET` | List analysis history with pagination |
| `/analyses/{analysis_id}` | `GET` | Retrieve detailed analysis record and per-skill results |
| `/analyses/{analysis_id}/c04` | `GET` | Retrieve downstream C04 payload |
| `/analyses/{analysis_id}/report` | `GET` | Retrieve deterministic explanation and report |
| `/readiness/docs` | `GET` | Interactive OpenAPI documentation |

All routes are also accessible under the `/readiness` prefix alias (e.g. `/readiness/analyses/{analysis_id}/report`).
For complete endpoint specifications and payload schemas, see [API Reference](docs/api-reference.md).

## Configuration

Settings are managed via environment variables or a local `.env` file:

| Variable | Default | Description |
|---|---|---|
| `SERVICE_NAME` | `readiness-engine` | Service identifier |
| `DATABASE_URL` | `postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/readiness_engine_db` | PostgreSQL connection URL |

## Database Setup and Schema Management

The database layer is aligned with the `shared-skill-knowledge` service pattern:

- **Automatic Initialization:** All 16 application tables are automatically created on service startup via SQLAlchemy `Base.metadata.create_all()` within the FastAPI application `lifespan` handler.
- **PostgreSQL Extensions:** When connected to PostgreSQL, `create_tables()` automatically ensures the required `vector` (`pgvector`) and `uuid-ossp` extensions are installed (`CREATE EXTENSION IF NOT EXISTS`).
- **No Migration Tool Overhead:** Following the SSKS architecture, the service does not require Alembic or external migration tooling; the schema is managed directly via SQLAlchemy declarative models.
- **Idempotency:** Startup schema creation is safe and idempotent across container restarts and test environments.

### Managed Tables (16 Application Entities)

1. `knowledge_snapshots`
2. `cached_skills`
3. `cached_aliases`
4. `cached_relationships`
5. `cached_skill_embeddings` (includes pgvector `Vector(1536)` column)
6. `user_skill_profiles`
7. `user_skill_profile_skills`
8. `skill_evidence`
9. `industry_profiles`
10. `industry_profile_requirements`
11. `industry_skill_evidence`
12. `analyses`
13. `analysis_skill_results`
14. `analysis_priority_skills`
15. `analysis_reports`
16. `candidate_discovery_runs`

## Local Development

### 1. Set Up Environment

```bash
cd services/readiness-engine
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

On startup, all database tables and required extensions will be initialized automatically. Interactive documentation is available at `http://localhost:8010/readiness/docs`.

### 3. Run Tests

```bash
pytest tests/ -v
```

