# Job Market Intelligence Engine (C01)

Collects job advertisements from Sri Lankan job sites, responsibly, and works out which skills
each job role demands in four sectors: **IT / Software, HR, Management and Agriculture**.

**Status:** steps 1–5 built: collection from topjobs.lk, data quality report, OCR of flyer ads and
the skill profile per job role. Sync, the PostgreSQL loader and scheduling come next.

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
│   ├── collectors/          collecting ads (scraper, storage, deduplication)
│   └── processing/          analysis (OCR, job roles, skill demand)
├── config/
│   ├── sector_mapping.yaml  site categories → the four sectors
│   ├── role_taxonomy.yaml   job titles → roles and seniority (editable)
│   └── skills_lexicon.yaml  skills with their aliases (editable)
├── scripts/                 scheduled refresh scripts
├── tests/
└── pyproject.toml
```

## Setup

Requires Python 3.11+.

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
python -m app.collectors.run --site topjobs --reparse                # offline: rebuild from data/raw/
python -m app.processing.skills                                      # skill profile only
```

Outputs in `data/processed/`: the cleaned ads (`topjobs.jsonl`, `combined.csv`),
`quality_report.md`, and the skill demand per job role (`skill_profile.md`, and
`skill_profile.json` for the Market Pulse page).

## Development plan

One branch per step, merged into `main` before the next one starts
(`Akalanka-Job-market-intelligence-engine/<step>`):

1. `project-setup` — folders, `pyproject.toml`, `.gitignore`, sector mapping
2. `web-scrapping` — polite HTTP client, robots.txt, topjobs scraper, storage, deduplication, CLI
3. `data-quality-report` — data quality report
4. `ocr` — text from image flyers (Tesseract)
5. `skill-profile` — job roles and the skills each role's ads ask for
6. `scraper-sync` — active / expired / removed status and new-ad collection
7. `postgres-loader` — load ads and skills into PostgreSQL
8. `scheduled-sync` — daily sync on a schedule
