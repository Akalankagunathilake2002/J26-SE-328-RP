# Skillaro C03 Readiness Engine — API Reference

## 1. Overview

The **Skill Gap Analysis and Career Readiness Engine (C03)** assesses student skill profiles against industry role requirements, calculates career readiness scores, prioritizes learning gaps, and generates deterministic explanations for downstream consumption (including C04 — Learning Skill Tree).

### Base URLs & Route Aliases
All routes are available both under the root path and under the `/readiness` prefix alias:
- Root routes: `http://localhost:8010/`
- Prefixed routes: `http://localhost:8010/readiness/`
- Interactive OpenAPI Docs: `http://localhost:8010/readiness/docs`
- OpenAPI JSON Schema: `http://localhost:8010/readiness/openapi.json`

---

## 2. API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health`, `/readiness/health` | Service health status |
| `POST` | `/analyses`, `/readiness/analyses` | Initiate career readiness analysis and return C04 contract |
| `GET` | `/analyses`, `/readiness/analyses` | List historical analyses with filtering and pagination |
| `GET` | `/analyses/{analysis_id}`, `/readiness/analyses/{analysis_id}` | Get full analysis execution details and per-skill results |
| `GET` | `/analyses/{analysis_id}/c04`, `/readiness/analyses/{analysis_id}/c04` | Retrieve persisted external C04 payload |
| `GET` | `/analyses/{analysis_id}/report`, `/readiness/analyses/{analysis_id}/report` | Retrieve deterministic explanation and report |

---

## 3. Detailed Endpoint Reference

### 3.1 Health Check
- **Path:** `GET /health` and `GET /readiness/health`
- **Description:** Verifies service availability.
- **Responses:**
  - `200 OK`: `{"status": "ok", "service": "readiness-engine"}`

---

### 3.2 Initiate Career Readiness Analysis
- **Path:** `POST /analyses` and `POST /readiness/analyses`
- **Description:** Coordinates Algorithms 1, 2, 3A, and 3B on database-persisted profiles. Evaluates skill matching, computes readiness score, ranks learning priorities, and persists results.
- **Request Body:** `AnalysisCreateRequest`
  ```json
  {
    "user_skill_profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "industry_profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "snapshot_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "matching_method": "EXACT",
    "scoring_config_version": "1.0"
  }
  ```
- **Responses:**
  - `201 Created`: Returns standard `C04AnalysisResponse`.
  - `400 Bad Request`: Validation failure or missing database records.
  - `500 Internal Server Error`: Pipeline execution failure.

---

### 3.3 List Analysis History
- **Path:** `GET /analyses` and `GET /readiness/analyses`
- **Description:** Lists previous analyses with deterministic descending sort (`started_at DESC, analysis_id DESC`).
- **Query / Header Parameters:**
  - `user_id` (query UUID, optional): Filter by student user UUID.
  - `X-User-Id` (header UUID, optional): Header alternative for user UUID.
  - `status` (query string, optional): `PENDING`, `RUNNING`, `COMPLETED`, or `FAILED`.
  - `role_id` (query string, optional): Filter by canonical or candidate role identifier.
  - `limit` (query int, default 20, 1-100): Pagination page size.
  - `offset` (query int, default 0, >= 0): Records to skip.
- **Responses:**
  - `200 OK`: `AnalysisHistoryResponse` containing items and total count.

---

### 3.4 Get Analysis Details
- **Path:** `GET /analyses/{analysis_id}` and `GET /readiness/analyses/{analysis_id}`
- **Description:** Retrieves the header record, all per-skill results, ordered priority skills, and the C04 payload.
- **Path Parameters:**
  - `analysis_id` (UUID): ID of the analysis.
- **Responses:**
  - `200 OK`: `AnalysisDetailResponse`.
  - `404 Not Found`: Analysis ID does not exist.

---

### 3.5 Get Downstream C04 Payload
- **Path:** `GET /analyses/{analysis_id}/c04` and `GET /readiness/analyses/{analysis_id}/c04`
- **Description:** Retrieves the persisted `to-C04.json` compliant payload for downstream learning tree generation.
- **Path Parameters:**
  - `analysis_id` (UUID): ID of the completed analysis.
- **Responses:**
  - `200 OK`: `C04AnalysisResponse`.
  - `400 Bad Request`: Analysis is not in `COMPLETED` status.
  - `404 Not Found`: Analysis or C04 payload not found.

---

### 3.6 Get Analysis Explanation Report
- **Path:** `GET /analyses/{analysis_id}/report` and `GET /readiness/analyses/{analysis_id}/report`
- **Description:** Generates and returns a comprehensive, deterministic explanation report derived from already-persisted analysis results.
- **Path Parameters:**
  - `analysis_id` (UUID): ID of the completed analysis.

#### Status Behavior and Error Handling
- **Non-existent ID:** Returns `404 Not Found`.
  ```json
  {
    "detail": "Analysis with ID '3fa85f64-5717-4562-b3fc-2c963f66afa6' not found"
  }
  ```
- **Incomplete Status (`PENDING`, `RUNNING`, `FAILED`):** Returns `400 Bad Request` without returning a misleading partial report.
  ```json
  {
    "detail": "Analysis has not completed successfully (current status: RUNNING)"
  }
  ```
  If the analysis failed, the failure reason is appended:
  ```json
  {
    "detail": "Analysis has not completed successfully (current status: FAILED). Error: Industry profile has no requirements"
  }
  ```

#### Response Schema (`AnalysisReportResponse`)

| Field | Type | Description |
|---|---|---|
| `analysisId` | `string` | Unique UUID of the analysis. |
| `userId` | `string` | UUID of the evaluated student. |
| `roleId` | `string` | Target industry role identifier. |
| `roleName` | `string \| null` | Human-readable role title. |
| `readinessScore` | `float` | Overall readiness percentage (0.00 – 100.00). |
| `generatedAt` | `datetime` | ISO-8601 timestamp of report generation. |
| `summary` | `ReadinessSummaryOut` | Overall readiness score interpretation and breakdown. |
| `skillExplanations` | `list[SkillExplanationOut]` | Per-requirement match, gap, and readiness contribution details. |
| `priorityExplanations` | `list[PriorityExplanationOut]` | Ranked learning priority recommendations with demand rationale. |
| `relationshipExplanations` | `list[RelationshipExplanationOut]` | Verified semantic relationships leveraged during matching. |

##### Summary Schema (`ReadinessSummaryOut`)
- `readinessScore`: Persisted readiness score.
- `interpretationTier`: Categorized readiness band (`High`, `Moderate`, `Developing`, `Low`).
- `headline`: Clear one-line qualitative summary.
- `narrative`: Paragraph explaining overall readiness and requirements distribution.
- `totalRequirements`: Total industry requirements evaluated.
- `assessableRequirements`: Count of evaluated requirements excluding unassessed skills.
- `satisfiedCount`: Fully satisfied requirements (`gap == 0`).
- `partialCount`: Partially met requirements (`0 < gap < 1.0`).
- `deficientCount`: High-gap requirements (`gap >= 1.0`).
- `missingCount`: Requirements with no demonstrated skill found.
- `unassessedCount`: Skills unassessed or unmapped.

##### Skill Explanation Schema (`SkillExplanationOut`)
- `skillId`: Canonical or requirement skill ID.
- `skillName`: Required skill name.
- `matchType`: Match technique (`EXACT`, `ALIAS`, `RELATIONSHIP`, `SBERT`, `NONE`).
- `resultStatus`: Evaluation status (`COVERED`, `PARTIALLY_COVERED`, `MISSING`, `UNASSESSED`).
- `requiredProficiency`: Target proficiency (1.0 – 5.0) or `null`.
- `demonstratedProficiency`: Student proficiency (0.0 – 5.0) or `null`.
- `gap`: Skill gap score or `null`.
- `industryWeight`: Demand weight of requirement (0.0 – 1.0) or `null`.
- `satisfaction`: Satisfaction ratio (0.0 – 1.0) or `null`.
- `readinessContributionPoints`: Exact points added to overall readiness or `null`.
- `maxPossiblePoints`: Maximum potential points for this requirement or `null`.
- `isUnassessed`: Boolean flag indicating if excluded from readiness.
- `explanation`: Deterministic text explanation.

##### Priority Explanation Schema (`PriorityExplanationOut`)
- `skillId`: Skill ID.
- `skillName`: Skill name.
- `priorityRank`: Sequential ranking (#1, #2, ...).
- `learningPriorityScore`: Computed priority score.
- `gap`: Persisted skill gap.
- `demandWeight`: Industry demand weight.
- `recommendationReason`: Brief classification string.
- `explanation`: Detailed deterministic learning recommendation rationale.

##### Relationship Explanation Schema (`RelationshipExplanationOut`)
- `requiredSkillName`: Target industry skill.
- `matchedSkillName`: Student's demonstrated skill.
- `relationshipType`: Verified relationship type (e.g. `SPECIALIZES_IN`, `SUBSUMES`).
- `coverageCredit`: Credit multiplier applied (e.g. 0.85).
- `explanation`: Traceable explanation of relationship match.

---

## 4. Example Successful Response

`GET /analyses/6b4e758a-f8fa-4a6c-9457-4148bfa17cb1/report`

```json
{
  "analysisId": "6b4e758a-f8fa-4a6c-9457-4148bfa17cb1",
  "userId": "6a96e676-e17f-4f81-9cb0-13f63c32608c",
  "roleId": "ROLE_BACKEND_ENG",
  "roleName": "Backend Software Engineer",
  "readinessScore": 81.25,
  "generatedAt": "2026-10-19T02:00:00Z",
  "summary": {
    "readinessScore": 81.25,
    "interpretationTier": "High",
    "headline": "High Readiness (81.25/100) for Backend Software Engineer",
    "narrative": "The candidate demonstrates strong alignment with the role requirements, satisfying 2 of 3 assessable requirements. Closing 1 identified skill gap(s) will further elevate career readiness.",
    "totalRequirements": 3,
    "assessableRequirements": 3,
    "satisfiedCount": 2,
    "partialCount": 0,
    "deficientCount": 1,
    "missingCount": 1,
    "unassessedCount": 0
  },
  "skillExplanations": [
    {
      "skillId": "SKILL_PYTHON",
      "skillName": "Python",
      "matchType": "EXACT",
      "resultStatus": "COVERED",
      "requiredProficiency": 4.0,
      "demonstratedProficiency": 4.5,
      "gap": 0.0,
      "industryWeight": 0.9,
      "satisfaction": 1.0,
      "readinessContributionPoints": 42.86,
      "maxPossiblePoints": 42.86,
      "isUnassessed": false,
      "explanation": "Direct exact match found. The candidate demonstrated proficiency of 4.50 against the required 4.00, fully satisfying the requirement with no skill gap (gap: 0.00). This contributed 42.86 points out of a maximum 42.86 points (100.0% satisfaction) to the overall readiness score."
    },
    {
      "skillId": "SKILL_FASTAPI",
      "skillName": "FastAPI",
      "matchType": "RELATIONSHIP",
      "resultStatus": "COVERED",
      "requiredProficiency": 3.0,
      "demonstratedProficiency": 4.0,
      "gap": 0.0,
      "industryWeight": 0.4,
      "satisfaction": 1.0,
      "readinessContributionPoints": 19.05,
      "maxPossiblePoints": 19.05,
      "isUnassessed": false,
      "explanation": "Verified relationship match 'SPECIALIZES_IN' to candidate skill 'Python' with 85.0% coverage credit. The candidate demonstrated proficiency of 4.00 against the required 3.00, fully satisfying the requirement with no skill gap (gap: 0.00). This contributed 19.05 points out of a maximum 19.05 points (100.0% satisfaction) to the overall readiness score."
    },
    {
      "skillId": "SKILL_DOCKER",
      "skillName": "Docker",
      "matchType": "NONE",
      "resultStatus": "MISSING",
      "requiredProficiency": 3.0,
      "demonstratedProficiency": 0.0,
      "gap": 3.0,
      "industryWeight": 0.8,
      "satisfaction": 0.0,
      "readinessContributionPoints": 0.0,
      "maxPossiblePoints": 38.1,
      "isUnassessed": false,
      "explanation": "No demonstrated skill found to meet requirement. Required proficiency is 3.00, resulting in a skill gap of 3.00 (demonstrated: 0.00). Contributed 0.00 points out of a potential 38.10 points to readiness score due to missing requirement."
    }
  ],
  "priorityExplanations": [
    {
      "skillId": "SKILL_DOCKER",
      "skillName": "Docker",
      "priorityRank": 1,
      "learningPriorityScore": 2.4,
      "gap": 3.0,
      "demandWeight": 0.8,
      "recommendationReason": "High Priority Gap (Large gap with high industry demand)",
      "explanation": "Ranked #1 learning priority (score: 2.40). Recommended due to a skill gap of 3.00 combined with a high industry demand weight of 0.80. Addressing this gap will provide significant career readiness gains."
    }
  ],
  "relationshipExplanations": [
    {
      "requiredSkillName": "FastAPI",
      "matchedSkillName": "Python",
      "relationshipType": "SPECIALIZES_IN",
      "coverageCredit": 0.85,
      "explanation": "Requirement 'FastAPI' was satisfied via verified relationship 'SPECIALIZES_IN' using demonstrated skill 'Python' (85.0% coverage credit)."
    }
  ]
}
```

---

## 5. Deterministic Generation & Persistence Strategy

### 5.1 Source of Truth
Explanations are strictly derived from already-persisted records in PostgreSQL:
- `analyses`: overall readiness score, configuration, timestamps, user ID, and profile IDs.
- `analysis_skill_results`: matched skill, match type, relationship ID, coverage credit, proficiencies, weights, satisfaction, gap, and status.
- `analysis_priority_skills`: ranked priority skills, learning priority score, and gap.
- `industry_profiles` & `industry_profile_requirements`: demand weights, role titles, and canonical identifiers.

### 5.2 Zero Hallucination & Neutral Fallbacks
- No data is fabricated or inferred beyond persisted outputs.
- If a proficiency or demand weight is absent, the template outputs an explicit unavailable reason (e.g. `"Required proficiency: 3.00 (demonstrated proficiency not recorded)"`).
- Unassessed or unmapped skills (`UNASSESSED`) receive an explicit unassessed explanation, generate 0.0 readiness contribution points, and are excluded from learning priorities.

### 5.3 Idempotent Persistence
- The report payload is stored in the existing `analysis_reports` table with `report_version="explanation_v1.0"`.
- On first retrieval via `GET /analyses/{id}/report`, the report is deterministically generated and persisted in a clean database transaction.
- On subsequent requests, the persisted report is retrieved directly. Repeated requests never create duplicate database rows.
- Existing C04 payloads (`report_version="1.0"`) remain completely isolated and unaffected.

---

## 6. Scope Boundaries (No RAG / LLM)

- **Strictly Deterministic:** This implementation uses deterministic Python string templates and mathematical models.
- **No External LLM Calls:** No AI models, OpenAI APIs, Ollama, LangChain, or external network requests are executed.
- **No Vector Embeddings Query:** No RAG or vector database queries are used for explanation generation.
- **Future AI Extensibility:** The architecture encapsulates explanation generation in `app/services/explanation_service.py`, permitting future AI providers to ground summaries on persisted results without altering the scoring engine.

---

## 7. Semantic Candidate Discovery & SSKS Integration API

The Readiness Engine includes a lightweight semantic discovery feature designed to detect potential skill relationships between unmatched industry requirements and unmatched student skills, submitting them as candidate relationship proposals to the Shared Skill Knowledge Service (SSKS).

### 7.1 Architecture & Boundaries
- **Asynchronous Execution:** Runs in the background via FastAPI `BackgroundTasks` after the analysis response is dispatched.
- **Scoring Isolation:** Candidate discovery never modifies readiness scores, matching outputs, gap calculations, learning priorities, or reports.
- **SSKS Ownership:** SSKS is the authoritative owner of skill taxonomy relationships. Candidate submissions are proposals with review status `PENDING` awaiting human editorial approval.
- **Cached Embedding Reuse:** SBERT vectors are loaded from `cached_skill_embeddings` for the active snapshot; no external embedding models are invoked during analysis.

### 7.2 Retrieval Endpoint: `GET /analyses/{id}/candidate-discovery`

Retrieve candidate discovery execution runs for an analysis:

- **Method:** `GET`
- **Path:** `/analyses/{analysis_id}/candidate-discovery` (or `/readiness/analyses/{analysis_id}/candidate-discovery`)
- **Status:** `200 OK`

#### Response JSON Schema (`list[CandidateDiscoveryRunOut]`):
```json
[
  {
    "id": "76df529b-986c-48ae-8b3d-18751fa0ef2b",
    "analysis_id": "a90dfeb6-0428-444a-9ef8-e8cb9b6ea17c",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "similarity_threshold": 0.75,
    "status": "COMPLETED",
    "candidates_submitted_count": 2,
    "started_at": "2026-10-19T14:30:00Z",
    "completed_at": "2026-10-19T14:30:01Z"
  }
]
```

### 7.3 SSKS Upstream Submission Contract

Eligible candidates meeting or exceeding the configurable threshold (default `0.75`) are submitted to SSKS:

- **Endpoint:** `POST {SSKS_BASE_URL}/ssks/candidates/relationships`
- **Payload Schema:**
```json
{
  "source_skill_id": "SK-001606",
  "target_skill_id": "SK-001881",
  "proposed_relationship_type": "RELATED_TO",
  "confidence_score": 0.8123,
  "source_id": null,
  "review_note": "Discovered by C03 Readiness Engine (Analysis: a90dfeb6-0428-444a-9ef8-e8cb9b6ea17c) with cosine similarity 0.8123"
}
```

- **Candidate Persistence Constraint:** C03 persists only run-level records in `candidate_discovery_runs`. Individual candidate relationships are never persisted in C03 database tables.
