"""Data quality report: how much usable data each sector has, and whether it is worth scaling up.

    python -m app.collectors.report        # writes data/processed/quality_report.md

Works offline from data/: the stored pages (raw/), the processed ads, the dedup log and the
listing sizes recorded by the last collection run. ``run`` also refreshes it after every run.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.collectors.config import load_sectors, load_settings, load_sites
from app.collectors.models import ACTIVE, STATUSES, JobAd
from app.collectors.storage import Storage

# Without OCR, a sector is worth scaling up only if at least this share of its ads is text.
TEXT_SHARE_TO_SCALE = 0.5

MISSING_FIELDS: dict[str, Callable[[JobAd], object]] = {
    "location": lambda ad: ad.location,
    "company": lambda ad: ad.company,
    "experience_level": lambda ad: ad.experience_level,
    "salary_text": lambda ad: ad.salary_text,
    "description / requirements": lambda ad: ad.description_text or ad.requirements_text,
    "posted_date": lambda ad: ad.posted_date,
    "closing_date": lambda ad: ad.closing_date,
}


@dataclass
class SectorQuality:
    sector: str
    live_on_site: int | None  # ads on the listing pages at the last run; None if never checked
    collected: int  # ads stored for the sector, before duplicates were removed
    duplicates: int  # stored ads dropped as duplicates of another ad
    ads: list[JobAd]  # unique ads in the sector after deduplication

    @property
    def active(self) -> int:
        return sum(ad.status == ACTIVE for ad in self.ads)

    @property
    def image_ads(self) -> int:
        return sum(ad.is_image_ad for ad in self.ads)

    @property
    def text_ads(self) -> int:
        return len(self.ads) - self.image_ads

    @property
    def verdict(self) -> str:
        if not self.ads:
            return "No data yet"
        if self.text_ads / len(self.ads) >= TEXT_SHARE_TO_SCALE:
            return "Yes"
        return "No – needs OCR"

    def missing_share(self, field: str) -> float | None:
        if not self.ads:
            return None
        return sum(not MISSING_FIELDS[field](ad) for ad in self.ads) / len(self.ads)


def sector_quality(storage: Storage, site: str, sectors: Sequence[str]) -> list[SectorQuality]:
    raw_sectors = {raw.job_id: raw.meta["sectors"] for raw in storage.iter_raw(site)}
    removed = [row["removed"].split(":", 1)[1] for row in storage.read_dedup_log()
               if row["removed"].startswith(f"{site}:")]
    duplicates = Counter(sector for job_id in removed for sector in raw_sectors.get(job_id, []))
    collected = Counter(sector for sectors_of_ad in raw_sectors.values() for sector in sectors_of_ad)
    listed = storage.listing_counts().get(site, {})
    ads = storage.read_jsonl(site)
    return [
        SectorQuality(
            sector=sector,
            live_on_site=listed.get(sector, {}).get("listed"),
            collected=collected[sector],
            duplicates=duplicates[sector],
            ads=[ad for ad in ads if sector in ad.sectors],
        )
        for sector in sectors
    ]


def render(site: str, rows: list[SectorQuality], listed_at: str | None, generated_at: str) -> str:
    lines = [
        "# Data quality report",
        "",
        f"Site: **{site}** · generated {generated_at}",
        "",
        "| Sector | Live on site | Collected | Active | Duplicates removed | Image ads | Text ads "
        "| Worth scaling up without OCR? |",
        "|---|--:|--:|--:|--:|--:|--:|---|",
    ]
    for row in rows:
        total = len(row.ads)
        lines.append(
            f"| {row.sector} | {_count(row.live_on_site)} | {row.collected} | {row.active} "
            f"| {row.duplicates} | {_with_share(row.image_ads, total)} | {_with_share(row.text_ads, total)} "
            f"| {row.verdict} |"
        )
    lines += [
        "",
        "- **Live on site:** ads on the sector's listing pages"
        + (f" at the last collection run ({listed_at})." if listed_at else "; not checked yet."),
        "- **Collected:** ads stored for the sector. An ad listed under two sectors counts in both.",
        "- **Image / text ads:** after duplicates were removed. Image ads need OCR before their "
        "requirements and skills can be read.",
        f"- **OCR:** text was read from {_ocr_read(rows)} image ads.",
        f"- **Status:** {_statuses(rows)}. Expired and removed ads are kept for history; the skill "
        "profile counts active ads only.",
        "",
        "## Missing values (% of ads)",
        "",
        "| Sector | " + " | ".join(MISSING_FIELDS) + " |",
        "|---|" + "--:|" * len(MISSING_FIELDS),
    ]
    for row in rows:
        cells = [_percent(row.missing_share(field)) for field in MISSING_FIELDS]
        lines.append(f"| {row.sector} | " + " | ".join(cells) + " |")
    lines += [
        "",
        'A missing **company** means the ad says "Company Name Withheld". Description, '
        "requirements and experience stay missing for image ads whose flyer has no readable text.",
        "",
    ]
    return "\n".join(lines)


def write_report(storage: Storage, sites: str | Sequence[str], sectors: Sequence[str]) -> Path:
    """Write processed/quality_report.md: one section per site."""
    sites = [sites] if isinstance(sites, str) else list(sites)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    reports = []
    for site in sites:
        checked = [entry["checked_at"] for entry in storage.listing_counts().get(site, {}).values()]
        reports.append(render(site, sector_quality(storage, site, sectors), max(checked) if checked else None, generated_at))
    text = reports[0] if len(reports) == 1 else _combine(sites, reports, generated_at)
    path = storage.processed_dir / "quality_report.md"
    storage.processed_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _combine(sites: list[str], reports: list[str], generated_at: str) -> str:
    """Several single-site reports as one: a section per site, headings one level down."""
    parts = [f"# Data quality report\n\nSites: {', '.join(f'**{s}**' for s in sites)} · generated {generated_at}\n"]
    for site, report in zip(sites, reports):
        body = report.split("\n", 4)[4]  # drop the title, the "Site: …" line and the blank lines
        parts.append(f"## {site}\n\n" + body.replace("\n## ", "\n### "))
    return "\n".join(parts)


def _ocr_read(rows: list[SectorQuality]) -> str:
    image_ads = {ad.key: ad for row in rows for ad in row.ads if ad.is_image_ad}
    with_text = sum(bool(ad.description_text) for ad in image_ads.values())
    return f"{with_text} of {len(image_ads)}"


def _statuses(rows: list[SectorQuality]) -> str:
    ads = {ad.key: ad for row in rows for ad in row.ads}
    counts = Counter(ad.status for ad in ads.values())
    return ", ".join(f"{counts[status]} {status}" for status in STATUSES)


def _count(value: int | None) -> str:
    return "–" if value is None else str(value)


def _with_share(part: int, total: int) -> str:
    return f"{part} ({part / total:.0%})" if total else "0"


def _percent(share: float | None) -> str:
    return "–" if share is None else f"{share:.0%}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the data quality report (offline).")
    parser.add_argument("--site", default="all", help="a collected site, or 'all' (default)")
    args = parser.parse_args(argv)
    sites = [name for name, site in load_sites().items() if site.enabled] if args.site == "all" else [args.site]
    path = write_report(Storage(load_settings().data_dir), sites, load_sectors())
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
