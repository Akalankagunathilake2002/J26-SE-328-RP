# Skill Gap Analysis and Career Readiness Engine (`readiness-engine`)

**Component:** C03 — Skill Gap Analysis and Career Readiness Engine

The Readiness Engine evaluates career readiness, identifies skill gaps, and prioritizes learning needs. It compares standardized industry skill profiles from C01 with student skill profiles from C02, referencing canonical skill and role identifiers from the Shared Skill Knowledge Service (SSKS).

## Responsibilities

- Receive and validate industry skill profile targets from C01.
- Ingest and evaluate student skill evidence and proficiency profiles from C02.
- Perform skill gap analysis and compute readiness scores.
- Determine high-priority learning recommendations for downstream consumption by C04 (Learning Skill Tree).

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Root health check |
| `/readiness/health` | `GET` | Service health status under service prefix |
| `/readiness/docs` | `GET` | Interactive OpenAPI documentation |

## Configuration

Settings are managed via environment variables or a local `.env` file:

| Variable | Default | Description |
|---|---|---|
| `SERVICE_NAME` | `readiness-engine` | Service identifier |
| `DATABASE_URL` | `postgresql+asyncpg://skillbridge:skillbridge@localhost:5432/readiness_engine_db` | PostgreSQL connection URL |

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

Interactive documentation is available at `http://localhost:8010/readiness/docs`.

### 3. Run Tests

```bash
pytest tests/ -v
```
