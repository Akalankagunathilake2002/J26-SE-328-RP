"""HTTP API for the Market Pulse page, reached through the API gateway under /jobs/.

    uvicorn app.main:app --port 8003      # API docs at http://localhost:8003/jobs/docs

GET /jobs/health        service status
GET /jobs/market-pulse  the skill profile (data/processed/skill_profile.json) and every job site,
                        including the ones that are not collected and why

The API only reads the processed files; collection runs separately (python -m app.collectors.run).
Nothing from raw/ is served.
"""

from __future__ import annotations

import json
from urllib.parse import urlsplit

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from app.collectors.config import load_settings, load_sites

SERVICE = "job-market-intelligence-engine"
NO_PROFILE = (
    "No market data yet. Collect ads and build the skill profile first: "
    "python -m app.collectors.run --site topjobs --sector all"
)


class SkillDemand(BaseModel):
    skill: str
    category: str
    ssk_id: str | None
    ads: int  # ads asking for the skill
    share: float  # of the ads with readable text, 0–1


class SectorProfile(BaseModel):
    sector: str
    ads: int
    ads_with_text: int
    skills: list[SkillDemand]


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
    generated_at: str
    ad_statuses: list[str]
    sources: list[Source]
    totals: Totals
    sectors: list[SectorProfile]
    skills: list[SkillDemand]
    roles: list[RoleProfile]


router = APIRouter(prefix="/jobs")


@router.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "healthy", "service": SERVICE}


@router.get("/market-pulse", response_model=MarketPulse, tags=["market pulse"])
def market_pulse() -> dict:
    """Skill demand per job role and sector, from the latest skill profile."""
    path = load_settings().data_dir / "processed" / "skill_profile.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=NO_PROFILE)
    profile = json.loads(path.read_text(encoding="utf-8"))
    profile["sources"] = all_sources(profile["sources"])
    return profile


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


app = FastAPI(
    title="Job Market Intelligence Engine",
    version="0.1.0",
    docs_url="/jobs/docs",
    redoc_url=None,
    openapi_url="/jobs/openapi.json",
)
app.include_router(router)
