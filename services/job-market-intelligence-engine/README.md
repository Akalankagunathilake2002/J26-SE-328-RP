# Job Market Intelligence Engine (C01)

Collects job advertisements from Sri Lankan job sites, responsibly, and works out which skills
each job role demands in four sectors: **IT / Software, HR, Management and Agriculture**.

**Status:** project setup. The scraper, OCR and skill profile are added in the next steps.

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
- an identifying User-Agent with a contact address (`SKILLBRIDGE_CONTACT`)
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
│   └── sector_mapping.yaml  site categories → the four sectors
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

## Development plan

One branch per step, merged into `main` before the next one starts
(`Akalanka-Job-market-intelligence-engine/<step>`):

1. `project-setup` — folders, `pyproject.toml`, `.gitignore`, sector mapping *(this step)*
2. `web-scrapping` — polite HTTP client, robots.txt, topjobs scraper, storage, deduplication, CLI
3. `data-quality-report` — data quality report
4. `ocr` — text from image flyers (Tesseract)
5. `skill-profile` — skills per job role
6. `scraper-sync` — active / expired / removed status and new-ad collection
7. `postgres-loader` — load ads and skills into PostgreSQL
8. `scheduled-sync` — daily sync on a schedule
