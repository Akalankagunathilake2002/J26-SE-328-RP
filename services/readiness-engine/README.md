# Readiness Engine (C03)

**Project:** Skillaro Career Readiness Platform  
**Service:** `readiness-engine`  
**Purpose:** Compare a student's skill profile with an industry role profile, calculate career readiness, identify capability gaps, rank improvement priorities, and provide explainable results.

## Architecture

C03 consumes data from:

- **C01 — Job Market Intelligence:** industry role profiles, required skills, proficiency targets, and demand weights.
- **C02 — Student Skill Profile:** canonical student skills, proficiency, evidence confidence, and supporting evidence.
- **SSKS — Shared Skill Knowledge Service:** canonical skills, aliases, verified typed relationships, and knowledge snapshots.

C03 stores local, versioned copies of the inputs it needs, runs deterministic analysis, and returns results and a C04-compatible learning-priority payload. It may submit potential skill relationships to SSKS for review; unverified candidates never affect readiness scores.

```text
C01 role profile ─────┐
C02 student profile ──┼─> C03 Readiness Engine ──> Results / report / C04 payload
SSKS knowledge ───────┘             │
                                    └─> relationship candidates for SSKS review
```

## Analysis pipeline

1. Resolve the student profile, industry role profile, and knowledge snapshot.
2. Run exact canonical/alias matching as a baseline and relationship-aware matching using verified, directionally valid SSKS relationships.
3. Calculate readiness using requirement demand weights, match coverage, proficiency alignment, and student evidence confidence.
4. Classify capability gaps and rank actionable learning priorities.
5. Persist the analysis, per-requirement results, priorities, and deterministic explanation/report data.
6. Run semantic candidate discovery separately in a background task. Discovery does not change the completed analysis score.

### Scoring concepts

For each assessable requirement, satisfaction combines coverage credit, proficiency alignment, and evidence confidence. The overall score is the demand-weighted satisfaction across assessable requirements, expressed as a percentage. Unassessed requirements are excluded from the score. Exact matching and relationship-aware matching are both retained to support comparison.

Capability gaps are based on capability coverage; evidence confidence affects readiness satisfaction but is not itself treated as a student skill deficiency. Learning priority is based on industry demand weight multiplied by capability gap. Only verified relationships can influence matching; `RELATED_TO` and `PREREQUISITE_OF` do not provide coverage credit.

## API endpoints

Through the API gateway, use the `/readiness` prefix. Interactive API documentation is available at `/readiness/docs` when served by the service/gateway configuration.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/readiness/health` | Health check |
| `POST` | `/readiness/analyses` | Run an analysis |
| `GET` | `/readiness/analyses` | List/paginate analysis history; supports available filters such as `user_id`, `role_id`, and `status` |
| `GET` | `/readiness/analyses/{analysis_id}` | Detailed analysis and skill results |
| `GET` | `/readiness/analyses/{analysis_id}/c04` | Retrieve the C04 payload |
| `GET` | `/readiness/analyses/{analysis_id}/report` | Retrieve the deterministic explanation report |
| `GET` | `/readiness/analyses/{analysis_id}/candidate-discovery` | Retrieve candidate-discovery run details |
| `GET` | `/readiness/industry-profiles` | List available role profiles |
| `GET` | `/readiness/industry-profiles/{profile_id}` | Get one industry profile |

`POST /readiness/analyses` accepts a student `user_id` or `user_skill_profile_id` and a target `role_id` or `industry_profile_id`, plus optional matching/scoring configuration and snapshot selection. Check the service's OpenAPI schema for the current request and response fields.

## Data storage

C03 uses PostgreSQL with SQLAlchemy's async support and `asyncpg`. Its tables store:

- versioned SSKS knowledge snapshots and cached skills, aliases, relationships, and embeddings;
- imported student profiles, skills, and evidence from C02;
- imported industry role profiles and requirements from C01;
- analysis records, per-requirement results, ranked priorities, report payloads, and candidate-discovery run logs.

The local profile/knowledge copies allow an analysis to refer to a known input version. Keep source IDs and version information consistent when synchronizing updated data.

## Semantic candidate discovery

After an analysis, C03 can compare cached skill embeddings to find potentially useful but unverified skill pairs. It excludes identical skills and pairs already connected by verified relationships, applies a similarity threshold, and submits candidate `RELATED_TO` relationships to SSKS. Candidate discovery is for knowledge maintenance only: similarity is not proof of equivalence and does not directly contribute readiness credit. SSKS remains responsible for reviewing and verifying candidates.

## Configuration

Settings are loaded through Pydantic Settings. Common variables include:

| Variable | Purpose |
|---|---|
| `SERVICE_NAME` | Service identifier |
| `VERSION` | API version |
| `DATABASE_URL` | Async PostgreSQL connection string |
| `SSKS_BASE_URL` | SSKS service base URL |
| `CANDIDATE_SIMILARITY_THRESHOLD` | Minimum similarity for candidate proposals |
| `CANDIDATE_MAX_SUBMISSIONS_PER_RUN` | Candidate submission cap per discovery run |
| `CANDIDATE_DISCOVERY_EMBEDDING_MODEL` | Embedding model identifier |
| `CANDIDATE_DISCOVERY_TIMEOUT_SECONDS` | SSKS request timeout |
| `CANDIDATE_DISCOVERY_MAX_RETRIES` | Retry limit for transient submission failures |

Check `app/config/settings.py` and the infrastructure environment file for the current defaults. Do not commit secrets or local `.env` files.

## Run locally

From `services/readiness-engine`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

API docs: `http://localhost:8010/readiness/docs`

The service can also be run through the project's Docker Compose setup. Check the repository's current Compose file and environment configuration for service names and exposed ports.

### Tests

Run unit tests for the pure algorithm modules:

```bash
pytest tests/test_matching.py tests/test_readiness.py tests/test_skill_gaps.py tests/test_priorities.py -v
```

Run the complete service test suite with a dedicated test database configured in `DATABASE_URL`:

```bash
pytest tests/ -v
```

**Important:** do not point database-backed tests at the development database. The service includes a safety guard for the development database name; use an isolated test database.

## Current limitations

- Matching currently uses direct, single-hop verified relationships; multi-hop graph reasoning is not implemented.
- Partial relationship credits use fixed configured values rather than learned/domain-specific calibration.
- Explanations are deterministic templates; an LLM/RAG explanation layer is not yet implemented.
- Candidate discovery proposes relationships but does not itself verify them.
- C03 currently depends on locally stored input profiles; automated event-driven synchronization with C01 and C02 is planned.
- The current API does not provide every desired administrative update/delete operation; endpoint coverage needs to be reviewed and extended where safe.

## Future improvements

- **RAG-based report explanations:** Generate richer student-friendly explanations from saved C03 results and grounded C01/C02 evidence. The LLM should explain the deterministic result, not calculate or change the score.
- **C01/C02 event synchronization with RabbitMQ:** Subscribe to role-profile and student-profile create/update events, consume versioned payloads, and upsert them into C03's local database. Handle duplicate/out-of-order events, retries, and failed messages so updated role requirements and student profiles are reflected reliably.
- **Enhanced relationship candidate discovery and review:** Go beyond approve/reject by showing canonical names, evidence, provenance, and relationship rationale; support candidate validation, duplicate detection, prioritization, and review/audit history. Verified relationships remain under SSKS authority.
- **API completeness:** Review and add missing update/delete endpoints where appropriate, with validation, referential-integrity safeguards, and explicit authorization. Do not allow unsafe deletion of records referenced by completed analyses.
- **Versioning and reproducibility:** Track the exact C01 profile version, C02 student profile version, and SSKS snapshot used by each analysis so historical results remain explainable after upstream updates.
- **Evaluation and observability:** Add integration tests for event synchronization, retry/idempotency tests, structured logs/metrics, and comparative evaluation of exact versus relationship-aware matching.
- **Advanced matching research:** Evaluate multi-hop relationship reasoning and calibrated relationship credits experimentally before allowing them to affect readiness scores.
