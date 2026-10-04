# Academic-to-Industry Skill Bridge

The Academic-to-Industry Skill Bridge compares the skills that industry roles require with the
skills a student can show evidence for. It identifies the student's skill gaps, measures how
ready they are for a role, and recommends what to learn next.

## How it works

```text
  C01 Industry Skill Extraction             C02 Student Skill Profile
  ─────────────────────────────             ─────────────────────────
  Industry skill profile for a role         Evidence-based student skill profile
  (required skills, importance,             (skills, proficiency, evidence
   required proficiency)                     confidence, evidence sources)
                 │                                        │
                 └───────────────────┬────────────────────┘
                                     ▼
                 C03 Skill Gap Analysis and Career Readiness
                 ───────────────────────────────────────────
                 Compares the two profiles and produces
                 skill gaps, a readiness score and learning priorities
                                     │
                                     ▼
                 C04 Learning Skill Tree
                 ───────────────────────
                 Turns learning priorities into a learning path


  Shared Skill Knowledge: canonical skills, aliases, roles and verified
  skill relationships, used by C01, C02, C03 and C04
```

## Components

Only the Auth Service, the frontend and the API gateway exist so far. The Shared Skill Knowledge
service has a folder with its plan (README only); C01–C04 get their folders under `services/`
when development starts.

| Component | Folder | What it does |
|---|---|---|
| C01 Industry Skill Extraction | planned: `services/c01-industry-skill-extraction/` | Extracts the skills industry roles require and produces an industry skill profile for each role, with each skill's importance and required proficiency. |
| C02 Student Skill Profile | planned: `services/c02-student-skill-profile/` | Builds an evidence-based profile of a student's skills: their proficiency, how confident the evidence is, and where the evidence came from. |
| C03 Skill Gap Analysis and Career Readiness | planned: `services/c03-skill-gap-readiness/` | Compares an industry skill profile with a student skill profile, identifies skill gaps, measures career readiness and decides learning priorities. |
| C04 Learning Skill Tree | planned: `services/c04-learning-skill-tree/` | Turns the learning priorities from C03 into a learning path for the student. |
| Shared Skill Knowledge | `services/shared-skill-knowledge/` (plan only) | The single source of canonical skills, roles, aliases and verified skill relationships for all components. |
| Auth Service | `services/auth-service/` | User accounts: registration, login and the current user. Issues signed access tokens. |
| Frontend | `frontend/` | The web application for the system. |
| API Gateway | `infrastructure/gateway/` | The single entry point to the backend services. Routes `/auth/…` to the Auth Service; each new service gets a route here. |

## Shared skill knowledge

All components refer to skills by canonical ID, so different names for the same skill are
treated as one skill. The Shared Skill Knowledge service owns:

- **Canonical skill and role IDs**, such as `SK_001` for JavaScript
- **Aliases** that lead to a canonical skill: `"JS"` → JavaScript → `SK_001`
- **Skill categories** (domains)
- **Verified skill relationships**, each with a type, a direction and a verification status:
  Amazon Web Services (`SK_205`) → Cloud Computing (`SK_100`)

No other component keeps its own copy of this knowledge.

## Research focus: two ways to measure readiness

C03 measures career readiness with two methods, using the same C01 and C02 input for both, so
that their results can be compared experimentally.

| Method | What it uses |
|---|---|
| Baseline | Canonical exact matching + industry importance + student proficiency + evidence confidence |
| Proposed | Everything in the baseline + coverage through validated skill relationships |

For example, a role requires Cloud Computing and the student has evidence of Amazon Web
Services. The baseline sees no exact match, so Cloud Computing counts as missing. The proposed
method finds the verified relationship between the two skills, so the student's AWS skill can
count towards Cloud Computing.

Only relationships verified in the Shared Skill Knowledge service can earn readiness credit.
Similarity between skill embeddings alone never does.

## Technology

- **Backend services:** Python, FastAPI, Pydantic
- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Database:** PostgreSQL, one database per service
- **Architecture:** microservices behind an Nginx API gateway, one folder per service in a single repository, run with Docker Compose
- **Planned:** RabbitMQ for messaging between services

## Repository structure

```text
├── frontend/                            Next.js + TypeScript web application
├── services/                            One folder per backend microservice
│   ├── auth-service/                    Working
│   └── shared-skill-knowledge/          Plan only (README); C01–C04 are added here when built
├── shared/                              Contracts shared between services (schemas, message formats)
├── infrastructure/                      Docker Compose, API gateway (gateway/nginx.conf), database setup
├── docs/                                Architecture and research documentation
└── scripts/                             Development and setup scripts
```

## Running locally

Start PostgreSQL, the backend services and the API gateway with Docker:

```bash
docker compose -f infrastructure/docker-compose.yml up --build
```

Then start the frontend:

```bash
cd frontend
npm install
npm run dev
```

| What | Where |
|---|---|
| Web app | http://localhost:3000 |
| API gateway (single entry point to all services) | http://localhost:8080 |
| Auth Service, through the gateway | http://localhost:8080/auth/… (API docs at `/auth/docs`) |
| PostgreSQL | `localhost:5433`, user `skillbridge`, password `skillbridge` (local development only) |

## Status

The project is at an early stage. The home page, login and registration work end to end with the
Auth Service. C01–C04 and the Shared Skill Knowledge service are not implemented yet.
