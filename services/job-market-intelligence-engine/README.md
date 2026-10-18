# Job Market Intelligence Engine (C01)

Collects job advertisements from Sri Lankan job sites, responsibly, and works out which skills
each job role demands in four sectors: **IT / Software, HR, Management and Agriculture**.

**Status:** steps 1–6 of 8 done. Ads are collected from topjobs.lk, read with OCR, kept up to date
by a sync, and turned into a skill demand profile per job role that the Market Pulse page shows.
Next: the PostgreSQL loader and the scheduled daily sync. See [Progress](#progress).

## Sources

| Site | Collected? | Why |
|---|---|---|
| topjobs.lk | Yes | No robots.txt restrictions and no scraping clause in its terms |
| xpress.jobs | No | Its terms prohibit scraping |
| ikman.lk | No | Its terms forbid storing content without written permission |

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
│   ├── processing/          analysis (OCR, job roles, skill demand)
│   └── main.py              the Market Pulse API
├── config/
│   ├── sector_mapping.yaml  site categories → the four sectors
│   ├── role_taxonomy.yaml   job titles → roles and seniority (editable)
│   └── skills_lexicon.yaml  skills with their aliases (editable)
├── scripts/sync.sh          sync with a log file
├── tests/                   134 tests on saved pages; no live requests
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
python -m app.collectors.run --site topjobs --sector HR --limit 25   # collect new ads
scripts/sync.sh                                                      # sync: statuses + new ads, logged
python -m app.collectors.run --site topjobs --reparse                # offline: rebuild from data/raw/
python -m app.processing.skills                                      # skill profile only
```

A sync (`scripts/sync.sh`, or `run --sync`) marks every stored ad **active**, **expired**
(closing date passed) or **removed** (taken down early), and downloads new ads only. An ad counts
as removed only if it is missing from both its category page and the topjobs homepage, which lists
every live ad posted directly by an employer. Ads posted through recruitment agencies are not on
the homepage, so they are never marked removed; they expire at their closing date. Ads are never
deleted, so their history stays available.

Outputs in `data/processed/`: the cleaned ads (`topjobs.jsonl`, `combined.csv`),
`quality_report.md`, `sync_log.csv` (one row per sync), and the skill demand per job role
(`skill_profile.md`, and `skill_profile.json` for the Market Pulse page). Sync logs are in
`data/logs/`.

## Market Pulse API

The Market Pulse page gets its data from this service, through the API gateway:

| Endpoint | Returns |
|---|---|
| `GET /jobs/health` | service status |
| `GET /jobs/market-pulse` | skill demand per job role and sector, totals, and the job sites with their status |

In Docker the service runs on port 8003 (`JOB_MARKET_INTELLIGENCE_PORT`) and is reached at
http://localhost:8080/jobs/ (API docs at `/jobs/docs`). Docker Compose mounts only
`data/processed/`, read-only: ads are collected on the host with the commands above, and a
refresh of the page shows the new data.

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
| 7 | `postgres-loader` | Load ads, statuses and skills into PostgreSQL; link each skill to the Shared Skill Knowledge service (`ssk_id`) | ⏳ Next |
| 8 | `scheduled-sync` | Run the sync automatically every day | ⏳ To do |

### Still to do

- **First full sync:** `scripts/sync.sh` collects about 100 ads across the four sectors
  (~15 minutes). Only 5 HR ads have been collected so far, so the Market Pulse percentages are
  only indicative.
- **Steps 7 and 8** in the table above.
- **Dead skills on Market Pulse:** skills that ads ask for less and less. Needs a few weeks of
  daily syncs first.
- **Data improvements:** collect roles with no ads yet (e.g. Software Engineer), filter the
  non-agriculture ads out of topjobs' Agriculture category (already flagged), and tune the skill
  list on the larger sample.
- **Evaluation:** compare the extracted skills with about 30 ads checked by hand, to measure
  accuracy.

### Known limitations

- Only topjobs.lk is collected (see [Sources](#sources)).
- Almost every topjobs ad is a flyer image, so skills depend on OCR. Badly designed or garbled
  flyers give fewer or wrong skills, and only English text is read.
- Skills are found by matching the skill list, so a skill missing from
  `config/skills_lexicon.yaml` is not counted.
- Agency ads can't be confirmed as removed, so they stay active until their closing date.
