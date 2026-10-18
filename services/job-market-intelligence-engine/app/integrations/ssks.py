"""Client for the Shared Skill Knowledge Service (services/shared-skill-knowledge).

Set SKILLBRIDGE_SSKS_URL to use it, e.g. http://localhost:8080/ssks (through the API gateway).

- ``lookup`` normalizes skill names with POST /ssks/normalize/skills, 100 per request by default
  (the endpoint accepts up to 500, but compares every unmatched name with all its skills: about
  0.06 s per name, measured in October 2026, so 500 names take about 30 s).
  Results are cached in processed/ssks_cache.json: matched IDs are kept, other results are checked
  again after ``recheck_days`` (SSKS learns new skills and aliases over time).
- If SSKS can't be reached, names without a cached result come back as "pending" and the run
  continues; they are looked up again on the next run.
- ``submit_candidate`` proposes a new skill (POST /ssks/candidates/entities). A 409 means SSKS
  already has it, or it is already waiting for review.

Match types: ``exact`` (canonical name), ``alias`` (verified alias), ``fuzzy`` (only a suggestion,
never counted), ``unmatched``, ``pending`` (not looked up yet).
"""

from __future__ import annotations

import json
import logging
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

import requests

from app.collectors.base import utc_now

log = logging.getLogger(__name__)

BATCH_LIMIT = 500  # the most POST /normalize/skills accepts
COUNTED = ("exact", "alias")
METHOD_TO_TYPE = {"CANONICAL_NAME": "exact", "VERIFIED_ALIAS": "alias"}


class SSKSUnavailable(Exception):
    pass


@dataclass(frozen=True)
class SSKSMatch:
    match_type: str  # exact | alias | fuzzy | unmatched | pending
    ssk_id: str | None = None
    preferred_name: str | None = None
    suggestion: str | None = None  # best fuzzy suggestion (for review only)

    @property
    def counted(self) -> bool:
        return self.match_type in COUNTED


PENDING = SSKSMatch("pending")


def normalize_key(name: str) -> str:
    """The same normalization SSKS uses: Unicode NFKC, case folded, single spaces."""
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())


class SSKSClient:
    def __init__(
        self,
        base_url: str,
        cache_path: Path | None = None,
        session: requests.Session | None = None,
        timeout: float = 120.0,
        recheck_days: int = 7,
        now: Callable[[], str] = utc_now,
        batch_size: int = 100,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.batch_size = min(batch_size, BATCH_LIMIT)
        self.cache_path = cache_path
        self.session = session or requests.Session()
        self.timeout = timeout
        self.recheck = timedelta(days=recheck_days)
        self.now = now
        self.reachable: bool | None = None  # None until SSKS was asked something
        self._cache: dict[str, dict] = self._load_cache()

    # --- normalization ---------------------------------------------------------------------------

    def lookup(self, names: Iterable[str]) -> dict[str, SSKSMatch]:
        """The SSKS match of each name. Never raises: unreachable means "pending"."""
        names = list(dict.fromkeys(n for n in names if n and n.strip()))
        keys = {name: normalize_key(name) for name in names}
        to_ask = list(dict.fromkeys(key for key in keys.values() if self._needs_lookup(key)))
        if to_ask and self.reachable is not False:  # once unreachable, don't retry in this run
            try:
                self._ask(to_ask)
                self.reachable = True
            except SSKSUnavailable as exc:
                log.warning("SSKS not reachable (%s): %d skills stay pending until the next run", exc, len(to_ask))
                self.reachable = False
            self._save_cache()
        return {name: self._match(keys[name]) for name in names}

    def _needs_lookup(self, key: str) -> bool:
        cached = self._cache.get(key)
        if cached is None:
            return True
        if cached["match_type"] in COUNTED:
            return False  # SSKS IDs are stable
        checked = datetime.fromisoformat(cached["checked_at"])
        return datetime.fromisoformat(self.now()) - checked >= self.recheck

    def _ask(self, keys: list[str]) -> None:
        checked_at = self.now()
        for i in range(0, len(keys), self.batch_size):
            batch = keys[i:i + self.batch_size]
            response = self._post("/normalize/skills", {"items": batch})
            if response.status_code != 200:
                raise SSKSUnavailable(f"normalize returned {response.status_code}")
            for item in response.json()["results"]:
                match = _from_result(item)
                self._cache[normalize_key(item["input_name"])] = {**asdict(match), "checked_at": checked_at}

    def _match(self, key: str) -> SSKSMatch:
        cached = self._cache.get(key)
        if cached is None:
            return PENDING
        return SSKSMatch(**{k: v for k, v in cached.items() if k != "checked_at"})

    # --- candidates ------------------------------------------------------------------------------

    def submit_candidate(self, payload: dict) -> str:
        """Propose a new skill or role. Returns "created", or "exists" if SSKS already knows it."""
        response = self._post("/candidates/entities", payload)
        if response.status_code == 201:
            return "created"
        if response.status_code == 409:
            return "exists"
        raise SSKSUnavailable(f"candidate submission returned {response.status_code}: {response.text[:200]}")

    # --- helpers ---------------------------------------------------------------------------------

    def _post(self, path: str, payload: dict):
        try:
            return self.session.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise SSKSUnavailable(type(exc).__name__) from exc

    def _load_cache(self) -> dict[str, dict]:
        if self.cache_path and self.cache_path.is_file():
            return json.loads(self.cache_path.read_text(encoding="utf-8")).get("skills", {})
        return {}

    def _save_cache(self) -> None:
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps({"skills": self._cache}, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8"
            )


def _from_result(item: dict) -> SSKSMatch:
    if item["status"] == "MATCHED":
        return SSKSMatch(METHOD_TO_TYPE[item["matching_method"]], item["canonical_id"], item["preferred_name"])
    if item["status"] == "SUGGESTED":
        best = item["suggestions"][0] if item.get("suggestions") else {}
        return SSKSMatch("fuzzy", suggestion=best.get("preferred_name"))
    return SSKSMatch("unmatched")
