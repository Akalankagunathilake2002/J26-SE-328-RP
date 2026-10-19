"""Load the collected job ads into PostgreSQL (job_market_db).

    python -m app.database.loader        # needs SKILLBRIDGE_DATABASE_URL

SKILLBRIDGE_DATABASE_URL, e.g. for the Docker database:
    postgresql+psycopg://skillbridge:<POSTGRES_PASSWORD>@localhost:15432/job_market_db
(needs ``pip install -e ".[db]"``).

Reads the processed files (the cleaned ads, ad_analysis.jsonl, ad_skills.jsonl, sync_log.csv) and
the status history kept in raw/, and writes them to the tables in app/database/schema.py. Safe to
repeat: ads are updated in place, an ad's sectors and skill mentions are replaced by the latest
ones, history and sync rows are added once. Nothing is deleted.

``run`` calls this after every run when SKILLBRIDGE_DATABASE_URL is set. If the database can't be
reached, the run still finishes and the next run loads everything.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import create_engine, delete
from sqlalchemy.engine import Connection, Engine

from app.collectors.base import utc_now
from app.collectors.config import load_settings, load_sites
from app.collectors.models import ACTIVE, JobAd
from app.collectors.storage import Storage
from app.database.schema import create_schema, job_ad_sectors, job_ad_skills, job_ad_status_history, job_ads, sync_runs

BATCH = 200  # rows per INSERT statement


@dataclass
class LoadResult:
    ads: int = 0
    sector_rows: int = 0
    skill_mentions: int = 0
    status_changes: int = 0
    sync_runs: int = 0


def connect(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def load(engine: Engine, storage: Storage, sites: Sequence[str], now: str | None = None) -> LoadResult:
    create_schema(engine)
    loaded_at = _datetime(now or utc_now())
    ads = [ad for site in sites for ad in storage.read_jsonl(site)]
    keys = {(ad.site, ad.job_id) for ad in ads}
    analysis = {(r["site"], r["job_id"]): r for r in _jsonl(storage.processed_dir / "ad_analysis.jsonl")}
    skills = [r for r in _jsonl(storage.processed_dir / "ad_skills.jsonl") if (r["site"], r["job_id"]) in keys]
    history = [row for site in sites for row in _status_history(storage, site) if (row["site"], row["job_id"]) in keys]
    syncs = [_sync_row(r) for r in storage.read_sync_log() if r["site"] in sites]

    with engine.begin() as conn:
        _upsert(conn, job_ads, [_ad_row(ad, analysis.get((ad.site, ad.job_id)), loaded_at) for ad in ads],
                ["site", "job_id"])
        for site in sites:
            job_ids = sorted(ad.job_id for ad in ads if ad.site == site)
            for table in (job_ad_sectors, job_ad_skills):
                for chunk in _batches(job_ids):
                    conn.execute(delete(table).where(table.c.site == site, table.c.job_id.in_(chunk)))
        sector_rows = [{"site": ad.site, "job_id": ad.job_id, "sector": s} for ad in ads for s in dict.fromkeys(ad.sectors)]
        _insert(conn, job_ad_sectors, sector_rows)
        _insert(conn, job_ad_skills, [_skill_row(r) for r in skills])
        _upsert(conn, job_ad_status_history, history, ["site", "job_id", "changed_at", "status"], update=False)
        _upsert(conn, sync_runs, syncs, ["site", "synced_at"], update=False)
    return LoadResult(len(ads), len(sector_rows), len(skills), len(history), len(syncs))


# --- rows ---------------------------------------------------------------------------------------


def _ad_row(ad: JobAd, analysis: dict | None, loaded_at: datetime) -> dict:
    analysis = analysis or {}
    return {
        "site": ad.site,
        "job_id": ad.job_id,
        "url": ad.url,
        "job_title": ad.job_title,
        "company": ad.company,
        "location": ad.location,
        "posted_date": _date(ad.posted_date),
        "closing_date": _date(ad.closing_date),
        "employment_type": ad.employment_type,
        "experience_level": ad.experience_level,
        "salary_text": ad.salary_text,
        "description_text": ad.description_text,
        "requirements_text": ad.requirements_text,
        "is_image_ad": ad.is_image_ad,
        "status": ad.status,
        "collected_at": _datetime(ad.collected_at),
        "last_seen_at": _datetime(ad.last_seen_at),
        "status_changed_at": _datetime(ad.status_changed_at),
        "role": analysis.get("role"),
        "role_mapped": analysis.get("role_mapped"),
        "seniority": analysis.get("seniority"),
        "has_text": analysis.get("has_text"),
        "flags": ",".join(analysis.get("flags", [])) or None,
        "loaded_at": loaded_at,
    }


def _skill_row(r: dict) -> dict:
    return {
        "site": r["site"],
        "job_id": r["job_id"],
        "extractor": r["extractor"],
        "raw_text": r["text"],
        "start_char": r["start"],
        "end_char": r["end"],
        "label": r.get("label"),
        "lexicon_skill": r.get("lexicon_skill"),
        "counted_as": r.get("counted_as"),
        "ssk_id": r.get("ssk_id"),
        "ssks_name": r.get("preferred_name"),
        "match_type": r.get("match_type") or "pending",
    }


def _status_history(storage: Storage, site: str) -> Iterator[dict]:
    """Status changes recorded by the syncs. Ads stored before statuses were tracked have none:
    they get one "active" row at the time they were collected."""
    for raw in storage.iter_raw(site):
        entries = raw.meta.get("status_history") or [{"status": ACTIVE, "at": raw.meta["collected_at"]}]
        for entry in entries:
            yield {"site": site, "job_id": raw.job_id, "changed_at": _datetime(entry["at"]), "status": entry["status"]}


def _sync_row(r: dict) -> dict:
    number = lambda key: int(r[key]) if r.get(key) not in (None, "") else None  # noqa: E731
    return {
        "site": r["site"],
        "synced_at": _datetime(r["synced_at"]),
        **{k: number(k) for k in ("live_on_homepage", "listed", "new_ads", "active", "expired", "removed",
                                  "reactivated", "unconfirmed")},
    }


# --- writing --------------------------------------------------------------------------------------


def _insert(conn: Connection, table, rows: list[dict]) -> None:
    for chunk in _batches(rows):
        conn.execute(table.insert(), chunk)


def _upsert(conn: Connection, table, rows: list[dict], keys: list[str], update: bool = True) -> None:
    """Insert rows; on a key conflict update them (or, with update=False, keep the existing row)."""
    if conn.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif conn.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise NotImplementedError(f"upserts are written for PostgreSQL and SQLite, not {conn.dialect.name}")
    for chunk in _batches(rows):
        statement = insert(table).values(chunk)
        if update:
            statement = statement.on_conflict_do_update(
                index_elements=keys,
                set_={c.name: statement.excluded[c.name] for c in table.columns if c.name not in keys},
            )
        else:
            statement = statement.on_conflict_do_nothing(index_elements=keys)
        conn.execute(statement)


def _batches(items: list, size: int = BATCH) -> Iterator[list]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _jsonl(path) -> Iterable[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def main(argv: Sequence[str] | None = None) -> int:
    settings = load_settings()
    if not settings.database_url:
        print("error: set SKILLBRIDGE_DATABASE_URL (see app/database/loader.py)", file=sys.stderr)
        return 2
    sites = [name for name, site in load_sites().items() if site.enabled]
    result = load(connect(settings.database_url), Storage(settings.data_dir), sites)
    print(f"loaded {result.ads} ads, {result.skill_mentions} skill mentions, {result.status_changes} status "
          f"changes, {result.sync_runs} syncs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
