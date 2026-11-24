# Shared database on Neon

One PostgreSQL database, `skillaro`, with one schema per component, as agreed in
`Skillaro_DB_Contract_v2` (24 Nov 2026):

| Schema | Component | Login |
|---|---|---|
| `auth` | Auth Service | `auth_svc` |
| `ssks` | Shared Skill Knowledge Service | `ssks_svc` |
| `job_market` | C01 Job Market Intelligence | `job_market_svc` |
| `skill_profile` | C02 Student Skill Profile | `skill_profile_svc` |
| `readiness` | C03 Readiness Engine | `readiness_svc` |
| `learning` | C04 learning service | `learning_svc` |
| `interview` | C04 interview service | `interview_svc` |

- Each login owns its schema, and its default `search_path` is that schema. A service can keep using plain
  table names: they land in its own schema.
- Other logins can only read the agreed contract tables (for example, `readiness_svc` reads the
  `job_market.role_profile*` tables). There are no foreign keys across schemas: ids travel as values.
- `vector` and `uuid-ossp` are installed once, in `public`.

## Set it up

1. In the Neon console, create a project and a database named `skillaro` (Databases → New database, owner
   `neondb_owner`). Or, from the default `neondb`: `CREATE DATABASE skillaro OWNER neondb_owner;`.
   The team's project is "Skillaro project" in AWS US East 2 (Ohio), PostgreSQL 18.
2. Copy the owner's **direct** connection string for `skillaro` (Connect → turn off connection pooling) into
   `infrastructure/.env`:

   ```
   NEON_OWNER_URL=postgresql://<owner>:<password>@<endpoint>.<region>.aws.neon.tech/skillaro?sslmode=require
   ```

3. Run:

   ```bash
   infrastructure/neon/setup.sh
   ```

   It adds a random password for each login to `infrastructure/.env` (`NEON_AUTH_PASSWORD`,
   `NEON_SSKS_PASSWORD`, …) plus `NEON_HOST`, then creates the schemas, logins and tables. It is safe to run
   again; existing tables are left as they are.

`infrastructure/.env` is ignored by git. Never commit it or paste its values anywhere.

## Run Auth, C01 and C02 on Neon

These three already match the v2 tables. `docker-compose.neon.yml` points them at Neon; every other
service stays on the local postgres container:

```bash
cd infrastructure
docker compose -f docker-compose.yml -f docker-compose.neon.yml up --build
# C01's daily sync too:
docker compose -f docker-compose.yml -f docker-compose.neon.yml --profile job-market-sync up -d --build job-market-sync
```

Accounts and C02 profiles in the local database are not copied to Neon; register again (or copy the rows).

## Connecting a service

Use the direct host and the service's own login:

```
# services using asyncpg
postgresql+asyncpg://<schema>_svc:<NEON_<SCHEMA>_PASSWORD>@<NEON_HOST>/skillaro?ssl=require
# C01 loader (psycopg)
postgresql+psycopg://job_market_svc:<NEON_JOB_MARKET_PASSWORD>@<NEON_HOST>/skillaro?sslmode=require
```

The learning and interview services take `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB=skillaro` and `POSTGRES_SSL=require`.

## Before a service switches to Neon

`setup.sql` creates the **v2** tables. Some differ from what the service code creates today, so each owner
updates their models first:

- **SSKS:** internal ids (`alias_id`, `relationship_id`, `candidate_*_id`, `source_id`) are `uuid`; new
  `skill_embeddings`.
- **C01:** new `companies`, `company_*` and `role_profile*` tables. The five existing ad tables are unchanged.
- **C02:** versioned `student_profiles`, `profile_skills`, `profile_evidence`, `education_records`,
  `experience_records`. `user_profiles` stays for now.
- **C03:** the snapshot and cache tables are gone; read `ssks` directly. `analyses.snapshot_id` has no foreign
  key until the knowledge-version question is settled.
- **C04:** `student_id` is `uuid`; `analysis_id`, `analysis_context` and `skill_id` added.

`setup.sql` is generated from the same data as the database design PDF (`Skillaro-Database-Design-v2.pdf`),
so the two match.
