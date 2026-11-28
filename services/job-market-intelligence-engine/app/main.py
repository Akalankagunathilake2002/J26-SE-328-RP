"""HTTP API for the Market Pulse page, reached through the API gateway under /jobs/.

    uvicorn app.main:app --port 8003      # API docs at http://localhost:8003/jobs/docs

GET /jobs/health        service status
GET /jobs/market-pulse  the skill profile and every job site, including the ones that are not
                        collected and why

With SKILLBRIDGE_DATABASE_URL set, the profile is built from the database (the job_market tables the
loader fills; see app/database/market_pulse.py) and kept for MARKET_PULSE_CACHE_SECONDS. Without it,
or if the database can't be reached, it is read from data/processed/skill_profile.json.
Collection runs separately (python -m app.collectors.run). Nothing from raw/ is served.

Company job posts (companies post jobs, admins verify companies, students apply) are in app/companies/api.py.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from app.collectors.config import load_settings, load_sites
from app.companies.api import router as company_router

log = logging.getLogger(__name__)

SERVICE = "job-market-intelligence-engine"
CACHE_SECONDS = float(os.environ.get("MARKET_PULSE_CACHE_SECONDS", "600"))  # the data changes once a day
NO_PROFILE = (
    "No market data yet. Collect ads and build the skill profile first: "
    "python -m app.collectors.run --site topjobs --sector all"
)


class SkillDemand(BaseModel):
    skill: str
    category: str
    ssk_id: str | None  # set when the skill has exactly one SSKS ID
    ssk_ids: list[str] = []  # every SSKS ID of the skill
    source: str = "lexicon"  # lexicon, or ner (verified in SSKS)
    ads: int  # ads asking for the skill
    share: float  # of the ads with readable text, 0–1


class UnverifiedSkill(BaseModel):
    """Found by NER but not verified in SSKS: shown, never counted in demand."""

    text: str
    ads: int
    match_type: str  # fuzzy, unmatched or pending
    suggestion: str | None = None


class SectorProfile(BaseModel):
    sector: str
    ads: int
    ads_with_text: int
    skills: list[SkillDemand]
    unverified: list[UnverifiedSkill] = []


class RoleProfile(BaseModel):
    role: str
    mapped: bool  # False: a job title not in config/role_taxonomy.yaml yet
    sectors: list[str]
    ads: int
    ads_with_text: int
    titles: list[str]
    seniority: dict[str, int]
    experience: dict[str, int]
    skills: list[SkillDemand]
    unverified: list[UnverifiedSkill] = []
    flags: dict[str, int]


class Totals(BaseModel):
    ads: int
    ads_with_text: int
    roles: int
    unmapped_roles: int
    unique_skills: int


class Source(BaseModel):
    site: str
    name: str  # e.g. "topjobs.lk"
    url: str
    collected: bool
    reason: str | None  # why a site is not collected
    ads: int
    last_collected: str | None  # newest ad downloaded (UTC, ISO 8601)
    last_checked: str | None  # listing pages last read


class MarketPulse(BaseModel):
    data_source: str = "file"  # database, or file (data/processed/skill_profile.json)
    generated_at: str
    ad_statuses: list[str]
    extraction: dict | None = None  # extractor used and SSKS match rates (see app/processing/skills.py)
    sources: list[Source]
    totals: Totals
    sectors: list[SectorProfile]
    skills: list[SkillDemand]
    unverified: list[UnverifiedSkill] = []
    roles: list[RoleProfile]


router = APIRouter(prefix="/jobs")


@router.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy", "service": SERVICE}


@router.get("/market-pulse", response_model=MarketPulse, tags=["market pulse"])
def market_pulse() -> dict:
    """Skill demand per job role and sector: from the database when configured, otherwise from the file."""
    settings = load_settings()
    profile = database_profile(settings.database_url) if settings.database_url else None
    if profile is None:
        path = settings.data_dir / "processed" / "skill_profile.json"
        if not path.is_file():
            raise HTTPException(status_code=404, detail=NO_PROFILE)
        profile = {**json.loads(path.read_text(encoding="utf-8")), "data_source": "file"}
    profile["sources"] = all_sources(profile["sources"])
    return profile


_cache: dict = {"url": None, "at": 0.0, "profile": None, "engine": None, "refreshing": False}
_cache_lock = threading.Lock()


def database_profile(url: str) -> dict | None:
    """The profile from the database. None if there are no ads or the database can't be reached.

    Kept for CACHE_SECONDS. After that the cached profile is still served while a background thread
    rebuilds it, so only the very first request (or a cold start before warm-up) waits for the database."""
    with _cache_lock:
        cached, age = _cache["profile"], time.monotonic() - _cache["at"]
        if _cache["url"] == url and cached is not None:
            if age >= CACHE_SECONDS and not _cache["refreshing"]:
                _cache["refreshing"] = True
                threading.Thread(target=_refresh, args=(url,), daemon=True).start()
            return dict(cached)
    return _refresh(url)


def _refresh(url: str) -> dict | None:
    from sqlalchemy import create_engine

    from app.database.market_pulse import profile_from_database

    try:
        with _cache_lock:
            if _cache["url"] != url or _cache["engine"] is None:
                _cache.update(url=url, engine=create_engine(url, pool_pre_ping=True), profile=None, at=0.0)
            engine = _cache["engine"]
        enabled = [name for name, site in load_sites().items() if site.enabled]
        profile = profile_from_database(engine, enabled)
    except Exception:  # the page still works from the file
        log.exception("Market Pulse: database not available, using the file")
        profile = None
    with _cache_lock:
        _cache["refreshing"] = False
        if profile is None:
            return None
        profile["data_source"] = "database"
        _cache.update(at=time.monotonic(), profile=profile)
        return dict(profile)


def all_sources(collected: list[dict]) -> list[dict]:
    """Every configured site, with the profile's numbers for the collected ones."""
    by_site = {source["site"]: source for source in collected}
    return [
        {
            "site": name,
            "name": (urlsplit(site.base_url).hostname or name).removeprefix("www."),
            "url": site.base_url,
            "collected": site.enabled,
            "reason": site.disabled_reason,
            "ads": by_site.get(name, {}).get("ads", 0),
            "last_collected": by_site.get(name, {}).get("last_collected"),
            "last_checked": by_site.get(name, {}).get("last_checked"),
        }
        for name, site in load_sites().items()
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Warm the Market Pulse cache in the background, so the first visitor doesn't wait for the database."""
    url = load_settings().database_url
    if url:
        threading.Thread(target=_refresh, args=(url,), daemon=True).start()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Job Market Intelligence Engine",
    version="0.1.0",
    docs_url="/jobs/docs",
    redoc_url=None,
    openapi_url="/jobs/openapi.json",
)
app.include_router(router)
app.include_router(company_router)
