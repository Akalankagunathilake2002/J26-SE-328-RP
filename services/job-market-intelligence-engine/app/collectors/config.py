"""Run settings: the site/sector mapping and environment variables.

Environment variables (or a git-ignored ``.env`` file in the service folder):

- ``SKILLBRIDGE_CONTACT``: optional contact address added to the User-Agent.
- ``SKILLBRIDGE_DATA_DIR``: where raw/ and processed/ are written. Default: ``<service>/data``.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.collectors.models import Category, SiteConfig

SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAPPING = SERVICE_ROOT / "config" / "sector_mapping.yaml"
DEFAULT_ENV_FILE = SERVICE_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    contact: str | None


def load_settings(env: Mapping[str, str] | None = None, env_file: Path = DEFAULT_ENV_FILE) -> Settings:
    """Settings from ``env`` (default: the process environment), falling back to ``env_file``."""
    values = {**read_env_file(env_file), **(os.environ if env is None else env)}
    return Settings(
        data_dir=Path(values.get("SKILLBRIDGE_DATA_DIR") or SERVICE_ROOT / "data"),
        contact=values.get("SKILLBRIDGE_CONTACT") or None,
    )


def read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def load_sectors(path: Path = DEFAULT_MAPPING) -> list[str]:
    return list(yaml.safe_load(path.read_text(encoding="utf-8"))["sectors"])


def load_sites(path: Path = DEFAULT_MAPPING) -> dict[str, SiteConfig]:
    """Every site in the mapping, enabled or not, with its categories per sector."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    sites = {}
    for name, site in data["sites"].items():
        categories = {
            sector: tuple(
                Category(name=item["name"], code=item.get("code"), id=item.get("id"))
                for item in site["categories"].get(sector, [])
            )
            for sector in data["sectors"]
        }
        sites[name] = SiteConfig(
            name=name,
            enabled=bool(site["enabled"]),
            base_url=site["base_url"].rstrip("/"),
            categories=categories,
            disabled_reason=site.get("disabled_reason"),
        )
    return sites
