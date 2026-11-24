# Job Market Intelligence Engine (C01)

Collects job advertisements from Sri Lankan job sites, responsibly, and works out which skills
each job role demands in four sectors: **IT / Software, HR, Management and Agriculture**.

**Status:** all 8 steps done. Ads are collected from two sites, topjobs.lk (flyer images, read
with OCR) and itpro.lk (full-text RSS feeds), synced once a day, loaded into PostgreSQL and turned
into a skill demand profile per job role that the Market Pulse page shows. Also built: NER skill
extraction (spaCy and JobBERT, trained on SkillSpan) and linking of skills to the Shared Skill
Knowledge Service; both are off by default. Next: the topjobs test set for the NER comparison and
more job roles in the role taxonomy. See [Progress](#progress).

## Sources

| Site | Collected? | Why |
|---|---|---|
| topjobs.lk | Yes | No robots.txt restrictions and no scraping clause in its terms. Ads are mostly flyer images (OCR). |
| itpro.lk | Yes | IT job board. Read through the RSS feeds it publishes; robots.txt allows them (10 s between requests) and its terms have no clause against it. Full-text ads, no OCR. No HR or Agriculture categories. |
| xpress.jobs | No | Its terms prohibit scraping |
| ikman.lk | No | Its terms forbid storing content without written permission |
| jobeka.lk | No | Its terms allow only "personal, non-commercial transitory viewing" and forbid copying |
| rooster.jobs | No | Its terms forbid scraping without written authorisation |
| SmartRecruiters (company career pages) | No | Its API's robots.txt allows only LinkedIn's bot |
| lankacareer.lk, jobs.paths.lk | No | robots.txt blocks AI crawlers / the job data API |
| Government Gazette | Not now | The vacancies section is published only in Sinhala |

Checked in October 2026.

The site categories for each sector are in [`config/sector_mapping.yaml`](config/sector_mapping.yaml).

## Responsible collection

- robots.txt is checked before every request
- a random 3–5 second wait between requests; stop on HTTP 403 or 429
- an identifying User-Agent naming the project (`SkillBridge-Research-Bot`); a contact address
  can be added with `SKILLBRIDGE_CONTACT`
- no logins, CAPTCHAs or rate limits are bypassed
- personal data (e-mails, phone numbers, contact names) is removed from processed data;
  collected data (`data/`) is never committed

## Structure

```text
job-market-intelligence-engine/
├── app/
│   ├── collectors/          collecting ads (scraper, sync, storage, deduplication, quality report)
│   ├── processing/          analysis (OCR, job roles, skill demand, NER extractor, SSKS candidates)
│   ├── integrations/        client for the Shared Skill Knowledge Service (SSKS)
│   ├── database/            PostgreSQL tables and the loader
│   └── main.py              the Market Pulse API
├── config/
│   ├── sector_mapping.yaml  site categories → the four sectors
│   ├── role_taxonomy.yaml   job titles → roles and seniority (editable)
│   └── skills_lexicon.yaml  skills with their aliases (editable)
├── scripts/sync.sh          sync with a log file
├── tests/                   176 tests on saved pages and feeds, a fake SSKS and SQLite; no live requests
├── Dockerfile
└── pyproject.toml
```

## Setup

Requires Python 3.11+, and Tesseract for reading flyer images (`brew install tesseract`).

```bash
cd services/job-market-intelligence-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Usage

```bash
python -m app.collectors.run --site topjobs --sector HR --limit 25   # collect new ads from one site
scripts/sync.sh                                                      # sync all sites: statuses + new ads, logged
python -m app.collectors.run --reparse                               # offline: rebuild from data/raw/
python -m app.processing.skills                                      # skill profile only
python -m app.collectors.schedule --status                           # the last and the next daily sync
```

`--site` is `all` (the default) or one site; a run for one site still rebuilds the processed data
from every site's stored ads.

A sync (`scripts/sync.sh`, or `run --sync`) marks every stored ad **active**, **expired**
(closing date passed) or **removed** (taken down early), and downloads new ads only. An ad counts
as removed only if it is missing from both its listing and the site's own list of live ads:
- **topjobs.lk:** the homepage, which lists every live ad posted directly by an employer. Ads posted
  through recruitment agencies are not on it, so they are never marked removed; they expire at
  their closing date.
- **itpro.lk:** its sitemap (`/sitemap.xml`), which lists every live job. Its ads have no closing date.

Ads are never deleted, so their history stays available. A flyer that is missing or isn't an image
(e.g. the site's maintenance page) is downloaded again on the next sync.

Outputs in `data/processed/`: the cleaned ads per site (`topjobs.jsonl`, `itpro.jsonl`) and all
together (`combined.csv`),
`quality_report.md`, `sync_log.csv` (one row per sync), and the skill demand per job role
(`skill_profile.md`, and `skill_profile.json` for the Market Pulse page). Sync logs are in
`data/logs/`.

## Daily sync (step 8)

The `job-market-sync` Docker container syncs both sites once a day, at 06:00 Sri Lanka time, and
loads the result into `job_market_db`. It is opt-in, so only the C01 owner's computer collects
ads, and the data stays in this folder's `data/` on that computer.

```bash
cd infrastructure
docker compose --profile job-market-sync up -d --build job-market-sync   # switch on
docker compose --profile job-market-sync logs job-market-sync           # when syncs ran
docker compose --profile job-market-sync stop job-market-sync           # switch off
```

- It checks every hour. A sync missed while the computer or Docker was off runs as soon as they
  are back, so switching it on after a break syncs straight away. A failed sync (e.g. no
  internet) is tried again an hour later, at most 3 times a day.
- It stays on after restarts until it is switched off, but only runs while Docker Desktop does:
  turn on "Start Docker Desktop when you sign in" in Docker Desktop's settings.
- Each sync's output goes to `data/logs/sync-<date>.log`, as with `scripts/sync.sh`. Only one run
  at a time can use `data/`: a run started while another is going stops with "another run is
  using …".
- Another time: `JOB_MARKET_SYNC_TIME=HH:MM` in `infrastructure/.env`. After code changes, run the
  `up` command again (`--build` rebuilds the image).
- Why Docker and not a macOS launchd job: macOS doesn't let background jobs read `~/Documents`,
  where the project is (tested: "Operation not permitted"), and giving bash or Python Full Disk
  Access would weaken the Mac's security. Docker Desktop already has access to the project folder.

## Skill extraction and SSKS

| Setting | Values |
|---|---|
| `SKILLBRIDGE_SKILL_EXTRACTOR` | `lexicon` (default): the skill list in `config/skills_lexicon.yaml`. `ner`: a trained NER model (`ml/c01-skill-ner/`). `both`: the two combined. |
| `SKILLBRIDGE_NER_MODEL` | the model folder, for `ner` and `both` (needs `pip install -e ".[ner]"` and Python 3.12) |
| `SKILLBRIDGE_SSKS_URL` | the Shared Skill Knowledge Service, e.g. `http://localhost:8080/ssks`. Not set: no SSKS IDs. |

- With SSKS, every skill mention is normalized (`POST /ssks/normalize/skills`, cached in
  `processed/ssks_cache.json`) and stored with its raw text, SSKS ID and match type (exact, alias,
  fuzzy, unmatched, pending) in `processed/ad_skills.jsonl`.
- `lexicon` counts skills as before and adds their SSKS IDs. `ner` counts only skills SSKS matches
  exactly or through a verified alias; the rest are listed as **unverified** (visible, not counted).
- If SSKS is down, mentions stay "pending" and collection continues; they are looked up on the next run.
- `python -m app.processing.ssks_candidates` lists skills SSKS doesn't know (unmatched, seen in 2+
  ads) in `processed/ssks_candidates.csv`. Nothing is sent without `--submit`.

The NER models, their training and the evaluation are in [`ml/c01-skill-ner/`](../../ml/c01-skill-ner/README.md).
Measured so far ([evaluation report](../../ml/c01-skill-ner/reports/evaluation.md)):

| On the SkillSpan test split (3,569 sentences) | Exact-span F1 | Partial-overlap F1 |
|---|--:|--:|
| Lexicon | 0.240 | 0.421 |
| spaCy NER | 0.475 | 0.731 |
| JobBERT NER | 0.573 | 0.871 |

- SSKS (its seed: 1,842 skills) gives an ID to 66 of the 145 lexicon skills (46%), but matches
  only 10–12% of the NER mentions exactly or by alias: NER often returns phrases ("communication
  and teamwork skills") where SSKS has short names. That is why `lexicon` stays the default.
- The comparison that matters, on hand-labelled topjobs ads, is still to be done (see below).

## Role profiles for C03 (the Readiness Engine)

After every load, the sync publishes what each job role needs, per career level, into the contract
tables C03 reads (`Skillaro_DB_Contract_v2`): `role_profiles`, `role_profile_requirements`,
`role_profile_education`, `role_profile_experience`, `role_profile_certifications` and
`requirement_evidence`. By hand: `python -m app.database.role_profiles`. The rules are at the top of
`app/database/role_profiles.py`; in short:

- Only roles with an `ssks_role_id` in `config/role_taxonomy.yaml` are published (the contract needs
  a role id). Career level comes from the title's seniority.
- `demand_weight` = ads asking for the skill ÷ ads with readable text for that role and level.
  Skills get an SSKS id from the lexicon or an exact/alias SSKS match (`SKILLBRIDGE_SSKS_URL`);
  otherwise they are UNMAPPED. Proficiency is never invented.
- Degrees go to education (`SLQF_1`…`SLQF_12`), professional qualifications and licences to
  certifications, "2–3 years" to experience (median of the minimums).
- Fewer than 3 readable ads: DRAFT. Versions are immutable; a new one is written only when the
  content changes, and the previous published one becomes ARCHIVED.

First run on Neon (24 Nov 2026): 11 published and 16 draft profiles for 10 roles, 581 requirements
(229 with an SSKS skill id).

## Database (PostgreSQL)

With `SKILLBRIDGE_DATABASE_URL` set, every run ends by loading the data into the database
`job_market_db` (needs `pip install -e ".[db]"`):

```bash
export SKILLBRIDGE_DATABASE_URL="postgresql+psycopg://skillbridge:<POSTGRES_PASSWORD>@localhost:15432/job_market_db"
python -m app.database.loader        # or just run a sync: it loads at the end
```

| Table | One row per |
|---|---|
| `job_ads` | ad: listing details, cleaned text (no personal data), status, role, seniority, flags |
| `job_ad_sectors` | ad and sector |
| `job_ad_skills` | skill mention: raw text, position, extractor, lexicon skill, SSKS ID, match type, what it counts as |
| `job_ad_status_history` | status change (active, expired, removed) |
| `sync_runs` | sync |
| `role_skill_demand` (view) | role, sector and skill: active ads asking for it, and the share |

Loading is safe to repeat and never deletes anything (expired and removed ads keep their history).
If the database is down, the run still finishes and the next run loads everything. The database
is created by `infrastructure/postgres/init-dbs.sh`, and the daily sync loads it after every sync.

Checked on the Docker PostgreSQL 16 on 19 November 2026: 229 ads, 4,017 skill mentions, 237 status
changes and 3 syncs loaded, and loading again changed nothing. The PostgreSQL test runs with
`SKILLBRIDGE_TEST_DATABASE_URL` set to an empty database.

## Market Pulse API

The Market Pulse page gets its data from this service, through the API gateway:

| Endpoint | Returns |
|---|---|
| `GET /jobs/health` | service status |
| `GET /jobs/market-pulse` | skill demand per job role and sector, totals, and the job sites with their status |

With `SKILLBRIDGE_DATABASE_URL` set, `/jobs/market-pulse` is built from the database tables (`app/database/market_pulse.py`, the same `build_profile` as the file, so the numbers match) and says `"data_source": "database"`. It is cached for `MARKET_PULSE_CACHE_SECONDS` (600), warmed at start-up and refreshed in the background. Without the variable, or if the database can't be reached, it reads `data/processed/skill_profile.json` (`"data_source": "file"`).

In Docker the service runs on port 8003 (`JOB_MARKET_INTELLIGENCE_PORT`) and is reached at
http://localhost:8080/jobs/ (API docs at `/jobs/docs`). The API container mounts only
`data/processed/`, read-only. Ads are collected by the daily sync or with the commands above, and
a refresh of the page shows the new data.

## Progress

One branch per step (`Akalanka-Job-market-intelligence-engine/<step>`), merged into `main`
before the next one starts.

| # | Step | What it adds | Status |
|--:|---|---|---|
| 1 | `project-setup` | Folders, `pyproject.toml`, `.gitignore`, sector mapping | ✅ Done |
| 2 | `web-scrapping` | Polite HTTP client, robots.txt, topjobs scraper, storage, deduplication, CLI | ✅ Done |
| 3 | `data-quality-report` | Data quality report per sector | ✅ Done |
| 4 | `ocr` | Text from flyer images (Tesseract), with personal data removed | ✅ Done |
| 5 | `skill-profile` | Job roles, skills per role, the Market Pulse API and page | ✅ Done |
| 6 | `scraper-sync` | Active / expired / removed ads, new ads only, sync log | ✅ Done |
| – | `skill-ner` | NER skill extraction (spaCy, JobBERT) compared with the lexicon; SSKS IDs for skills; candidate proposals | 🔄 In progress: test set labelling |
| 7 | `database-loader` | Load ads, statuses, skill mentions and SSKS IDs into PostgreSQL (`job_market_db`) | ✅ Done |
| – | `itpro-collector` | itpro.lk as a second source (RSS feeds, removals via its sitemap); one quality report for all sites | ✅ Done |
| 8 | `scheduled-sync` | The sync runs every day by itself (Docker), catches up missed days and loads `job_market_db` | ✅ Done |

The Market Pulse page was also redesigned in the style of the Skill Analysis page
(`Akalanka-Frontend/market-pulse-redesign`).

**Data so far** (sync of 22 October 2026): 221 active ads, 171 from topjobs.lk and 50 from itpro.lk.
By sector: IT 73, HR 50, Management 69, Agriculture 35 (an ad can be in more than one). They have
92 job roles, 66 of them not yet in `config/role_taxonomy.yaml`, and 137 different skills.

### Still to do

- **NER evaluation on topjobs:** draw 100 test ads (`ml/c01-skill-ner/src/export_label_studio.py`;
  165 topjobs ads qualify), label them by hand (`LABELLING.md`) and run the evaluation: lexicon vs
  spaCy vs JobBERT on Sri Lankan ads. Then decide the extractor.
- **Role taxonomy:** add the 66 job roles that are not mapped yet, so their ads are grouped
  correctly on Market Pulse.
- **Dead skills on Market Pulse:** skills that ads ask for less and less. Needs a few weeks of
  daily syncs first.
- **Data improvements:** filter the non-agriculture ads out of topjobs' Agriculture category
  (already flagged) and tune the skill list on the larger sample.
- **SSKS:** the SSKS seed has to be loaded in Docker before skills can be linked there, and new
  skills are proposed as candidates only after the SSKS owner agrees.
- **Flyer storage:** flyers take about 1.2 MB each (224 MB for the first 184), and the daily sync
  keeps adding them. Decide whether to keep the flyers of expired ads.

### Known limitations

- Only two sites can be collected (see [Sources](#sources)), and itpro.lk has IT and Management
  ads only, so HR and Agriculture come from topjobs.lk alone.
- Almost every topjobs ad is a flyer image, so skills depend on OCR. Badly designed or garbled
  flyers give fewer or wrong skills, and only English text is read.
- Skills are found by matching the skill list, so a skill missing from
  `config/skills_lexicon.yaml` is not counted (unless the NER extractor is switched on).
- Agency ads can't be confirmed as removed, so they stay active until their closing date.
- The daily sync runs only while the computer and Docker Desktop are on; a missed day is synced
  when they are back, but ads that opened and closed in between are not collected.
- Fewer than half of the lexicon skills, and few NER phrases, have an SSKS ID with the current
  SSKS seed (no agriculture skills, few soft skills).
