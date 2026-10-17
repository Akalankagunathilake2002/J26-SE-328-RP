"""BaseCollector: the collect flow shared by every job site.

A site module only says where its listing pages are and how to read its pages
(``listing_url``, ``parse_listing``, ``parse_ad``). The base class does the rest:

1. read the listing pages of each requested sector,
2. pick the newest ads, up to a limit per sector,
3. download each new ad page (and its flyer image) and store it unchanged in ``raw/``.

``reparse`` rebuilds ad records from ``raw/`` without any network access.
"""

from __future__ import annotations

import logging
import mimetypes
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, ClassVar, Protocol
from urllib.parse import urlsplit

from app.collectors.http import CollectionError, RobotsDisallowed, SiteBlocked
from app.collectors.models import Category, JobAd, ListingEntry, SiteConfig

if TYPE_CHECKING:
    from app.collectors.storage import Storage

log = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


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


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


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
                if self.storage.find_raw(self.site, entry.job_id):
                    self.storage.add_listing(entry)  # same ad, possibly listed under another sector
                    result.already_stored += 1
                elif (limit is None or downloaded < limit) and self._download(entry, result):
                    downloaded += 1
            result.new_ads[sector] = downloaded
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
        self.storage.save_raw(entry, page.text, self.now(), image=image, image_extension=extension)
        return True

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
        return response.content, image_extension(url, response.headers.get("Content-Type"))

    def reparse(self) -> list[JobAd]:
        """Rebuild every stored ad of this site from raw/ (no network)."""
        ads = []
        for raw in self.storage.iter_raw(self.site):
            entry = ListingEntry(**raw.meta["listing"])
            ad = self.parse_ad(raw.html, entry)
            ad.sectors = list(raw.meta["sectors"])
            ad.categories = list(raw.meta["categories"])
            ad.collected_at = raw.meta["collected_at"]
            ad.image_path = str(raw.image_path) if raw.image_path else None
            ads.append(ad)
        return ads


def image_extension(url: str, content_type: str | None) -> str:
    suffix = PurePosixPath(urlsplit(url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    return guessed if guessed in IMAGE_EXTENSIONS else ".img"
