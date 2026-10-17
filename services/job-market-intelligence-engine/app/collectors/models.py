"""Records shared by every collector."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields

# Status of a stored ad. Ads are never deleted, so their history stays available for trend analysis.
ACTIVE = "active"  # still live on the site
EXPIRED = "expired"  # closing date has passed
REMOVED = "removed"  # taken down before its closing date
STATUSES = (ACTIVE, EXPIRED, REMOVED)


@dataclass(frozen=True)
class Category:
    """A job site's own category, e.g. topjobs' "SDQ" or xpress.jobs' 30."""

    name: str
    code: str | None = None
    id: int | None = None

    @property
    def key(self) -> str:
        return self.code or (str(self.id) if self.id is not None else self.name)


@dataclass(frozen=True)
class SiteConfig:
    name: str
    enabled: bool
    base_url: str
    categories: dict[str, tuple[Category, ...]]  # sector → that site's categories for it
    disabled_reason: str | None = None


@dataclass
class ListingEntry:
    """An ad as shown on a category listing page, before its own page is downloaded."""

    site: str
    job_id: str
    url: str
    sector: str
    category: str
    job_title: str | None = None
    company: str | None = None
    posted_date: str | None = None  # ISO date (yyyy-mm-dd)
    closing_date: str | None = None  # ISO date (yyyy-mm-dd)
    location: str | None = None


@dataclass
class JobAd:
    site: str
    job_id: str
    url: str
    sectors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    job_title: str | None = None
    company: str | None = None  # None when the ad says "Company Name Withheld"
    location: str | None = None
    posted_date: str | None = None
    closing_date: str | None = None
    employment_type: str | None = None
    description_text: str | None = None
    requirements_text: str | None = None
    experience_level: str | None = None
    salary_text: str | None = None
    is_image_ad: bool = False
    image_url: str | None = None
    image_path: str | None = None
    status: str = ACTIVE
    collected_at: str | None = None  # when the ad page was downloaded (UTC, ISO 8601)

    @property
    def key(self) -> str:
        return f"{self.site}:{self.job_id}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> JobAd:
        return cls(**{name: data[name] for name in FIELDS if name in data})


FIELDS = [f.name for f in fields(JobAd)]
