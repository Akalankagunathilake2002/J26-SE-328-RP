"""Command line: collect job ads, then rebuild the processed data.

    python -m app.collectors.run --site topjobs --sector HR --limit 25
    python -m app.collectors.run --site all --sector all --limit 25
    python -m app.collectors.run --site all --reparse     # offline: rebuild processed/ from raw/

Every run ends by refreshing data/processed/quality_report.md.

The User-Agent names the project. Set SKILLBRIDGE_CONTACT (in the environment or the service's
.env file) to add a contact address to it.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from app.collectors.base import BaseCollector, CollectResult, utc_now
from app.collectors.config import Settings, load_sectors, load_settings, load_sites
from app.collectors.dedup import deduplicate
from app.collectors.http import PoliteClient, SiteBlocked
from app.collectors.models import JobAd, SiteConfig
from app.collectors.report import write_report
from app.collectors.storage import Storage
from app.collectors.text_utils import clean_ad
from app.collectors.topjobs import TopjobsCollector

COLLECTORS: dict[str, type[BaseCollector]] = {"topjobs": TopjobsCollector}

log = logging.getLogger("collectors")


class OfflineClient:
    """Used by --reparse: nothing may be fetched while rebuilding from raw/."""

    def get(self, url: str):
        raise RuntimeError(f"--reparse must not fetch {url}")


def parse_args(argv: Sequence[str] | None, sectors: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect job ads and rebuild the processed data.")
    parser.add_argument("--site", default="all", help="a site from config/sector_mapping.yaml, or 'all'")
    parser.add_argument("--sector", default="all", choices=[*sectors, "all"])
    parser.add_argument("--limit", type=int, default=25, help="new ads per sector (default: 25)")
    parser.add_argument("--reparse", action="store_true", help="no network: rebuild processed/ from raw/")
    return parser.parse_args(argv)


def choose_sites(requested: str, sites: dict[str, SiteConfig]) -> list[str]:
    """Sites to run. Raises ValueError with a readable reason if the request can't be run."""
    if requested == "all":
        return [name for name, site in sites.items() if site.enabled and name in COLLECTORS]
    if requested not in sites:
        raise ValueError(f"Unknown site '{requested}'. Known sites: {', '.join(sites)}")
    site = sites[requested]
    if not site.enabled:
        raise ValueError(f"{requested} is not collected: {site.disabled_reason}")
    if requested not in COLLECTORS:
        raise ValueError(f"There is no collector for {requested} yet.")
    return [requested]


def main(
    argv: Sequence[str] | None = None,
    settings: Settings | None = None,
    sites: dict[str, SiteConfig] | None = None,
) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sector_names = load_sectors()
    args = parse_args(argv, sector_names)
    settings = settings or load_settings()
    sites = sites if sites is not None else load_sites()
    sectors = sector_names if args.sector == "all" else [args.sector]

    try:
        names = choose_sites(args.site, sites)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    storage = Storage(settings.data_dir)
    exit_code = 0
    if not args.reparse:
        for name in names:
            client = PoliteClient(sites[name].base_url, settings.contact)
            collector = COLLECTORS[name](sites[name], client, storage)
            try:
                result = collector.collect(sectors, args.limit)
            except SiteBlocked as exc:
                log.error("%s: stopped, the site asked us to stop (%s)", name, exc)
                exit_code = 1
                continue
            log_result(name, result)
            storage.record_listing_counts(name, result.listed, utc_now())

    ads = [ad for name in names for ad in COLLECTORS[name](sites[name], OfflineClient(), storage).reparse()]
    write_processed(storage, names, ads)
    for name in names:
        log.info("%s: data quality report in %s", name, write_report(storage, name, sector_names))
    return exit_code


def log_result(site: str, result: CollectResult) -> None:
    for sector, new in result.new_ads.items():
        listed = result.listed.get(sector, 0)
        log.info("%s / %s: %d listed, %d new ads downloaded", site, sector, listed, new)
        if listed == 0:
            log.warning(
                "%s / %s: no ads found on the listing pages. The page layout may have changed; "
                "save a listing page and check the site's parse_listing.", site, sector
            )
    log.info(
        "%s: %d already stored, %d gone (404), %d skipped",
        site, result.already_stored, result.gone, len(result.skipped),
    )
    for skipped in result.skipped:
        log.info("  skipped %s", skipped)


def write_processed(storage: Storage, sites: list[str], ads: list[JobAd]) -> None:
    """Clean every ad (personal data removed), drop duplicates, and write processed/."""
    unique, removed = deduplicate([clean_ad(ad) for ad in ads])
    for site in sites:
        storage.write_jsonl(site, [ad for ad in unique if ad.site == site])
    storage.write_combined_csv(unique)
    storage.write_dedup_log(record.as_row() for record in removed)
    log.info("processed: %d unique ads (%d duplicates removed) in %s", len(unique), len(removed), storage.processed_dir)


if __name__ == "__main__":
    sys.exit(main())
