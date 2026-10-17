"""PoliteClient: the only way the collectors talk to a job site.

Every request:

- stays on the site's own host (robots.txt is per host),
- is checked against robots.txt (see ``robots.py``),
- waits a random 3–5 seconds after the previous request (longer if robots.txt sets a Crawl-delay),
- is retried with exponential backoff on network errors and 5xx responses.

An HTTP 403 or 429 stops the whole site: the site is asking us to stop, so we do.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Protocol
from urllib.parse import urlsplit

import requests

from app.collectors.robots import RobotsPolicy

USER_AGENT_PRODUCT = "SkillBridge-Research-Bot"
USER_AGENT = USER_AGENT_PRODUCT + "/0.1 (SLIIT student project; academic research)"


class CollectionError(Exception):
    """Base class for errors that stop or skip a request."""


class RobotsDisallowed(CollectionError):
    pass


class SiteBlocked(CollectionError):
    """The site answered 403 or 429; nothing more is requested from it in this run."""


class OffSiteURL(CollectionError):
    pass


class FetchFailed(CollectionError):
    pass


class Session(Protocol):
    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> requests.Response: ...


def build_user_agent(contact: str | None = None) -> str:
    """The User-Agent names the project; a contact address is added if one is set."""
    if not contact:
        return USER_AGENT
    return USER_AGENT.removesuffix(")") + f"; contact: {contact})"


class PoliteClient:
    def __init__(
        self,
        base_url: str,
        contact: str | None = None,
        *,
        min_delay: float = 3.0,
        max_delay: float = 5.0,
        max_retries: int = 3,
        backoff_seconds: float = 5.0,
        timeout: float = 30.0,
        session: Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
    ) -> None:
        parts = urlsplit(base_url)
        self.scheme, self.host = parts.scheme, parts.netloc
        self.user_agent = build_user_agent(contact)
        self.min_delay, self.max_delay = min_delay, max_delay
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.timeout = timeout
        self.session = session or requests.Session()
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()
        self._robots: RobotsPolicy | None = None
        self._last_request_at: float | None = None
        self.blocked_reason: str | None = None

    def get(self, url: str) -> requests.Response:
        """Fetch a page or image on this site. 404s are returned; the caller decides what they mean."""
        self._check_host(url)
        if self.blocked_reason:
            raise SiteBlocked(self.blocked_reason)
        if not self.robots.allowed(url):
            raise RobotsDisallowed(url)
        response = self._fetch(url)
        self._check_host(response.url)  # a redirect must not take us to another site
        return response

    @property
    def robots(self) -> RobotsPolicy:
        if self._robots is None:
            self._robots = self._load_robots()
        return self._robots

    def _load_robots(self) -> RobotsPolicy:
        try:
            response = self._fetch(f"{self.scheme}://{self.host}/robots.txt")
        except FetchFailed:
            return RobotsPolicy.disallow_all()  # robots.txt can't be reached: treat the site as off-limits
        if 400 <= response.status_code < 500:
            return RobotsPolicy.allow_all()  # RFC 9309: no robots.txt means no restrictions
        content_type = response.headers.get("Content-Type", "")
        if "html" in content_type or response.text.lstrip().startswith("<"):
            return RobotsPolicy.allow_all()  # redirected to an error page (topjobs.lk does this)
        return RobotsPolicy.from_text(response.text, self.user_agent)

    def _fetch(self, url: str) -> requests.Response:
        error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._wait_turn()
            try:
                response = self.session.get(
                    url, headers={"User-Agent": self.user_agent}, timeout=self.timeout
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                error = exc
            else:
                if response.status_code in (403, 429):
                    self.blocked_reason = f"HTTP {response.status_code} for {url}"
                    raise SiteBlocked(self.blocked_reason)
                if response.status_code < 500:
                    return response
                error = FetchFailed(f"HTTP {response.status_code}")
            if attempt < self.max_retries:
                self._sleep(self.backoff_seconds * 2**attempt)
        raise FetchFailed(f"{url}: {error}")

    def _wait_turn(self) -> None:
        delay = self._rng.uniform(self.min_delay, self.max_delay)
        if self._robots is not None and self._robots.crawl_delay:
            delay = max(delay, self._robots.crawl_delay)
        if self._last_request_at is not None:
            remaining = delay - (self._clock() - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request_at = self._clock()

    def _check_host(self, url: str) -> None:
        if urlsplit(url).netloc != self.host:
            raise OffSiteURL(f"{url} is not on {self.host}")
