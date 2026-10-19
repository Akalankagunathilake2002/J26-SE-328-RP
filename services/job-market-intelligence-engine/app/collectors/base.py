"""BaseCollector: the collect flow shared by every job site.

A site module only says where its listing pages are and how to read its pages
(``listing_url``, ``parse_listing``, ``parse_ad``). The base class does the rest:

1. read the listing pages of each requested sector,
2. pick the newest ads, up to a limit per sector,
3. download each new ad page (and its flyer image) and store it unchanged in ``raw/``.

``sync`` also keeps the status of every stored ad up to date (see ``next_status``):

- **expired:** its closing date has passed.
- **removed:** taken down before its closing date. Ads drop off category pages while still live,
  so an ad counts as removed only if it is also missing from the site's homepage, which lists the
  live ads. Only ads the homepage would list can be confirmed this way (``listed_on_homepage``);
  others stay as they are until they expire. If the homepage can't be read, or lists too few of
  the ads seen on the category pages (its layout may have changed), no ad is marked removed.
- **active:** still on the site. A removed ad that comes back is active again.

Ads are never deleted, so their history stays available for trend analysis.

``reparse`` rebuilds ad records from ``raw/`` without any network access.
"""

from __future__ import annotations

import logging
import mimetypes
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, ClassVar, Protocol
from urllib.parse import urlsplit

from app.collectors.http import CollectionError, RobotsDisallowed, SiteBlocked
from app.collectors.models import ACTIVE, EXPIRED, REMOVED, Category, JobAd, ListingEntry, SiteConfig

if TYPE_CHECKING:
    from app.collectors.storage import Storage

log = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
# The first bytes of PNG, JPEG and GIF files. (A site may answer an image request with an HTML
# error page and status 200: topjobs did, with its maintenance page, in October 2026.)
IMAGE_SIGNATURES = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8")
SRI_LANKA = timezone(timedelta(hours=5, minutes=30))  # closing dates are Sri Lankan dates (no daylight saving)
# The homepage must list at least this share of the category pages' ads that it should list.
MIN_HOMEPAGE_COVERAGE = 0.8


class Response(Protocol):
    status_code: int
    text: str
    content: bytes
    headers: dict
    url: str


class Client(Protocol):
    def get(self, url: str) -> Response: ...


@dataclass
class CollectResult:
    listed: dict[str, int] = field(default_factory=dict)  # sector → ads on its listing pages
    new_ads: dict[str, int] = field(default_factory=dict)  # sector → ads downloaded
    already_stored: int = 0  # listed again; any new sector is recorded, nothing is downloaded
    gone: int = 0  # listed, but the ad page returned 404
    skipped: list[str] = field(default_factory=list)  # URLs skipped (robots.txt, off-site, errors)
    seen: dict[str, ListingEntry] = field(default_factory=dict)  # job_id → entry, every ad on the listing pages
    repaired: int = 0  # stored ads whose missing or broken flyer was downloaded again


@dataclass
class SyncResult:
    live_on_homepage: int | None = None  # ads on the homepage; None: not read or not trusted
    active: int = 0  # stored ads that are active after the sync
    expired: list[str] = field(default_factory=list)  # job IDs that became expired in this sync
    removed: list[str] = field(default_factory=list)  # job IDs that became removed
    reactivated: list[str] = field(default_factory=list)  # expired or removed before, live again
    unconfirmed: int = 0  # active ads missing from their category page that the homepage can't confirm


def is_image(data: bytes) -> bool:
    return data.startswith(IMAGE_SIGNATURES) or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def local_date(iso_utc: str) -> str:
    """The Sri Lankan calendar date (yyyy-mm-dd) of a UTC timestamp."""
    return datetime.fromisoformat(iso_utc).astimezone(SRI_LANKA).date().isoformat()


def next_status(current: str, closing_date: str | None, today: str, *, seen: bool, homepage_checked: bool) -> str:
    """An ad's status after a sync.

    ``seen``: the ad is on a listing page or the homepage. ``homepage_checked``: the homepage was
    read, is trusted and would list this ad, so an ad missing from it really is gone.
    """
    if closing_date and closing_date < today:
        return REMOVED if current == REMOVED else EXPIRED  # taken down early stays "removed"
    if seen:
        return ACTIVE
    if current == ACTIVE and homepage_checked:
        return REMOVED
    return current  # without the homepage, missing from a category page proves nothing


class BaseCollector(ABC):
    site: ClassVar[str]

    def __init__(
        self,
        config: SiteConfig,
        client: Client,
        storage: Storage,
        now: Callable[[], str] = utc_now,
    ) -> None:
        if config.name != self.site:
            raise ValueError(f"{type(self).__name__} collects {self.site}, not {config.name}")
        self.config = config
        self.client = client
        self.storage = storage
        self.now = now

    # --- What each site module provides ----------------------------------------------------------

    @abstractmethod
    def listing_url(self, category: Category) -> str:
        """URL of the listing page for one of the site's categories."""

    @abstractmethod
    def parse_listing(self, html: str, sector: str, category: Category) -> list[ListingEntry]:
        """Ads shown on a listing page."""

    @abstractmethod
    def parse_ad(self, html: str, entry: ListingEntry) -> JobAd:
        """An ad record from its own page (sectors and storage details are filled in by the caller)."""

    def homepage_url(self) -> str | None:
        """A page listing every live ad of the site, used to confirm removals. None if there is none."""
        return None

    def parse_live_ids(self, html: str) -> set[str]:
        """Job IDs of the ads on the homepage (needed only if ``homepage_url`` returns a URL)."""
        raise NotImplementedError

    def listed_on_homepage(self, url: str) -> bool:
        """Whether the homepage lists this ad while it is live, so its absence there means it is gone."""
        return True

    # --- Shared flow -----------------------------------------------------------------------------

    def listings(self, sector: str) -> list[ListingEntry]:
        entries: list[ListingEntry] = []
        for category in self.config.categories.get(sector, ()):
            url = self.listing_url(category)
            try:
                entries += self.parse_listing(self.client.get(url).text, sector, category)
            except RobotsDisallowed:
                log.warning("robots.txt disallows %s; category skipped", url)
        return entries

    @staticmethod
    def select(entries: Iterable[ListingEntry], limit: int | None) -> list[ListingEntry]:
        """One entry per job, newest posting first (undated last), at most ``limit``."""
        unique: dict[str, ListingEntry] = {}
        for entry in entries:
            unique.setdefault(entry.job_id, entry)
        newest_first = sorted(unique.values(), key=lambda e: e.posted_date or "", reverse=True)
        return newest_first if limit is None else newest_first[:limit]

    def collect(self, sectors: Iterable[str], limit: int | None = None) -> CollectResult:
        """Download ads not stored yet, up to ``limit`` new ads per sector."""
        result = CollectResult()
        for sector in sectors:
            downloaded = 0
            listed = self.select(self.listings(sector), limit=None)
            result.listed[sector] = len(listed)
            for entry in listed:
                result.seen.setdefault(entry.job_id, entry)
                if self.storage.find_raw(self.site, entry.job_id):
                    self.storage.add_listing(entry)  # same ad, possibly listed under another sector
                    result.already_stored += 1
                    self._repair_flyer(entry.job_id, result)
                elif (limit is None or downloaded < limit) and self._download(entry, result):
                    downloaded += 1
            result.new_ads[sector] = downloaded
        return result

    def sync(self, sectors: Iterable[str], limit: int | None = None) -> tuple[CollectResult, SyncResult]:
        """Download new ads (up to ``limit`` per sector), then update the status of every stored ad."""
        live = self.live_ids()
        collected = self.collect(sectors, limit)
        return collected, self.update_statuses(collected.seen, live)

    def live_ids(self) -> set[str] | None:
        """Job IDs of every ad live on the site, read from its homepage. None if it can't be read."""
        url = self.homepage_url()
        if url is None:
            return None
        try:
            response = self.client.get(url)
        except SiteBlocked:
            raise
        except CollectionError as exc:
            log.warning("%s: homepage not read (%s); no ad will be marked removed", self.site, type(exc).__name__)
            return None
        if response.status_code != 200:
            log.warning("%s: homepage returned %s; no ad will be marked removed", self.site, response.status_code)
            return None
        return self.parse_live_ids(response.text)

    def update_statuses(self, seen: dict[str, ListingEntry], live: set[str] | None) -> SyncResult:
        """Set each stored ad's status from what is on the site now, and remember the changes."""
        now = self.now()
        today = local_date(now)
        live = live or set()
        checkable = {job_id for job_id, entry in seen.items() if self.listed_on_homepage(entry.url)}
        homepage_read = bool(checkable) and len(checkable & live) / len(checkable) >= MIN_HOMEPAGE_COVERAGE
        if live and not homepage_read:
            log.warning(
                "%s: the homepage lists too few of the ads on the category pages (layout changed?); "
                "no ad will be marked removed", self.site,
            )
        result = SyncResult(live_on_homepage=len(live) if homepage_read else None)

        for raw in self.storage.iter_raw(self.site):
            meta, listing = raw.meta, raw.meta["listing"]
            entry = seen.get(raw.job_id)
            changed = False
            if entry and entry.closing_date and entry.closing_date > (listing.get("closing_date") or ""):
                listing["closing_date"] = entry.closing_date  # extended on the site
                changed = True
            on_site = entry is not None or raw.job_id in live
            if on_site:
                meta["last_seen_at"] = now
                changed = True

            if "status" not in meta:  # stored before statuses were tracked
                meta["status"] = ACTIVE
                changed = True
            current = meta["status"]
            homepage_checked = homepage_read and self.listed_on_homepage(listing["url"])
            status = next_status(
                current, listing.get("closing_date"), today, seen=on_site, homepage_checked=homepage_checked
            )
            if status == ACTIVE and not on_site and homepage_read and not homepage_checked:
                result.unconfirmed += 1
            if status != current:
                meta["status"] = status
                meta["status_changed_at"] = now
                meta.setdefault("status_history", []).append({"status": status, "at": now})
                changed = True
                {ACTIVE: result.reactivated, EXPIRED: result.expired, REMOVED: result.removed}[status].append(
                    raw.job_id
                )
            result.active += status == ACTIVE
            if changed:
                self.storage.save_meta(raw)
        return result

    def _download(self, entry: ListingEntry, result: CollectResult) -> bool:
        try:
            page = self.client.get(entry.url)
        except SiteBlocked:
            raise  # the site asked us to stop
        except CollectionError as exc:
            result.skipped.append(f"{entry.url} ({type(exc).__name__})")
            return False
        if page.status_code == 404:
            result.gone += 1
            return False

        ad = self.parse_ad(page.text, entry)
        image, extension = None, None
        if ad.image_url:
            image, extension = self._download_image(ad.image_url, result)
        self.storage.save_raw(
            entry, page.text, self.now(), image=image, image_extension=extension, image_url=ad.image_url
        )
        return True

    def _repair_flyer(self, job_id: str, result: CollectResult) -> None:
        """Download the flyer again for a stored ad whose flyer is missing or isn't an image (one
        request, only for those ads; nothing else about the ad is fetched again)."""
        raw = self.storage.raw_ad(self.site, job_id)
        if raw is None:
            return
        if raw.image_path is not None:
            if raw.image_path.is_file() and is_image(raw.image_path.read_bytes()[:16]):
                return
            url = raw.meta.get("image_url") or self.parse_ad(raw.html, ListingEntry(**raw.meta["listing"])).image_url
        else:
            url = raw.meta.get("image_url")  # set when the first download failed; absent for text ads
        if not url:
            return
        image, extension = self._download_image(url, result)
        if image is not None:
            self.storage.save_image(raw, image, extension)
            result.repaired += 1
        elif raw.image_path is not None:  # a file that isn't an image is useless: drop it, retry next sync
            self.storage.forget_image(raw, url)

    def _download_image(self, url: str, result: CollectResult) -> tuple[bytes | None, str | None]:
        try:
            response = self.client.get(url)
        except SiteBlocked:
            raise
        except CollectionError as exc:  # e.g. a flyer hosted on another site
            result.skipped.append(f"{url} ({type(exc).__name__})")
            return None, None
        if response.status_code != 200:
            return None, None
        if not is_image(response.content):
            result.skipped.append(f"{url} (not an image: the site sent something else)")
            return None, None
        return response.content, image_extension(url, response.headers.get("Content-Type"))

    def reparse(self) -> list[JobAd]:
        """Rebuild every stored ad of this site from raw/ (no network).

        The status is the one set by the last sync, except that an ad whose closing date has
        passed since then is already reported as expired.
        """
        today = local_date(self.now())
        ads = []
        for raw in self.storage.iter_raw(self.site):
            meta = raw.meta
            entry = ListingEntry(**meta["listing"])
            ad = self.parse_ad(raw.html, entry)
            ad.sectors = list(meta["sectors"])
            ad.categories = list(meta["categories"])
            ad.collected_at = meta["collected_at"]
            ad.image_path = str(raw.image_path) if raw.image_path else None
            # A sync may have seen a later closing date on the listing page than the stored ad page.
            ad.closing_date = max(filter(None, [ad.closing_date, entry.closing_date]), default=None)
            ad.status = next_status(
                meta.get("status", ACTIVE), ad.closing_date, today, seen=False, homepage_checked=False
            )
            ad.last_seen_at = meta.get("last_seen_at", meta["collected_at"])
            ad.status_changed_at = meta.get("status_changed_at")
            ads.append(ad)
        return ads


def image_extension(url: str, content_type: str | None) -> str:
    suffix = PurePosixPath(urlsplit(url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    return guessed if guessed in IMAGE_EXTENSIONS else ".img"
