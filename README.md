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

| Component | Folder | What it does |
|---|---|---|
| C01 Industry Skill Extraction | `services/c01-industry-skill-extraction/` | Extracts the skills industry roles require and produces an industry skill profile for each role, with each skill's importance and required proficiency. |
| C02 Student Skill Profile | `services/c02-student-skill-profile/` | Builds an evidence-based profile of a student's skills: their proficiency, how confident the evidence is, and where the evidence came from. |
| C03 Skill Gap Analysis and Career Readiness | `services/c03-skill-gap-readiness/` | Compares an industry skill profile with a student skill profile, identifies skill gaps, measures career readiness and decides learning priorities. |
| C04 Learning Skill Tree | `services/c04-learning-skill-tree/` | Turns the learning priorities from C03 into a learning path for the student. |
| Shared Skill Knowledge | `services/shared-skill-knowledge/` | The single source of canonical skills, roles, aliases and verified skill relationships for all components. |
| Frontend | `frontend/` | The web application for the system. |

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
- **Frontend:** Next.js, TypeScript
- **Architecture:** microservices, one folder per service in a single repository
- **Planned:** PostgreSQL for storage, RabbitMQ for messaging between services, Docker

## Repository structure

```text
├── frontend/                            Next.js + TypeScript web application
├── services/
│   ├── c01-industry-skill-extraction/
│   ├── c02-student-skill-profile/
│   ├── c03-skill-gap-readiness/
│   ├── c04-learning-skill-tree/
│   └── shared-skill-knowledge/
├── shared/                              Contracts shared between services (schemas, message formats)
├── infrastructure/                      Docker, database and messaging setup
├── docs/                                Architecture and research documentation
└── scripts/                             Development and setup scripts
```

## Status

The project is at an early stage. The repository structure is in place, but no service has
been implemented yet.
