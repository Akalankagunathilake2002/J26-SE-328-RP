"""Two storage layers under one data directory (git-ignored).

``raw/<site>/<sector>/<job_id>.html``
    Ad pages exactly as downloaded, plus the flyer image (``<job_id>.png``/``.jpg``) and
    ``<job_id>.meta.json`` with the listing details. Everything can be re-parsed offline from here.
    Keep raw/ private: pages contain recruiters' contact details as published.

``processed/``
    ``<site>.jsonl`` and ``combined.csv`` (cleaned ad records), ``dedup_log.csv``,
    ``listing_counts.json`` (ads on each sector's listing pages at the last run) and
    ``quality_report.md``.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

from app.collectors.models import FIELDS, JobAd, ListingEntry


@dataclass
class RawAd:
    site: str
    job_id: str
    html_path: Path
    image_path: Path | None
    meta: dict

    @property
    def html(self) -> str:
        return self.html_path.read_text(encoding="utf-8")


class Storage:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.raw_dir = self.root / "raw"
        self.processed_dir = self.root / "processed"

    # --- raw/ --------------------------------------------------------------------------------------

    def find_raw(self, site: str, job_id: str) -> Path | None:
        """The stored page of an ad, whichever sector folder it was first saved under."""
        return next((self.raw_dir / site).glob(f"*/{job_id}.html"), None)

    def save_raw(
        self,
        entry: ListingEntry,
        html: str,
        collected_at: str,
        *,
        image: bytes | None = None,
        image_extension: str | None = None,
    ) -> Path:
        folder = self.raw_dir / entry.site / entry.sector
        folder.mkdir(parents=True, exist_ok=True)
        html_path = folder / f"{entry.job_id}.html"
        html_path.write_text(html, encoding="utf-8")

        image_file = None
        if image is not None:
            image_file = f"{entry.job_id}{image_extension or '.img'}"
            (folder / image_file).write_bytes(image)

        meta = {
            "listing": asdict(entry),
            "sectors": [entry.sector],
            "categories": [entry.category],
            "collected_at": collected_at,
            "image_file": image_file,
        }
        self._write_meta(html_path, meta)
        return html_path

    def add_listing(self, entry: ListingEntry) -> bool:
        """Record that a stored ad is also listed under another sector/category. True if anything new."""
        html_path = self.find_raw(entry.site, entry.job_id)
        if html_path is None:
            raise FileNotFoundError(f"{entry.site}:{entry.job_id} is not stored")
        meta = self._read_meta(html_path)
        changed = False
        for key, value in (("sectors", entry.sector), ("categories", entry.category)):
            if value not in meta[key]:
                meta[key].append(value)
                changed = True
        if changed:
            self._write_meta(html_path, meta)
        return changed

    def iter_raw(self, site: str | None = None) -> Iterator[RawAd]:
        sites = [site] if site else sorted(p.name for p in self.raw_dir.glob("*") if p.is_dir())
        for name in sites:
            for html_path in sorted((self.raw_dir / name).glob("*/*.html")):
                meta = self._read_meta(html_path)
                image_file = meta.get("image_file")
                yield RawAd(
                    site=name,
                    job_id=html_path.stem,
                    html_path=html_path,
                    image_path=html_path.parent / image_file if image_file else None,
                    meta=meta,
                )

    @staticmethod
    def _meta_path(html_path: Path) -> Path:
        return html_path.with_suffix(".meta.json")

    def _read_meta(self, html_path: Path) -> dict:
        return json.loads(self._meta_path(html_path).read_text(encoding="utf-8"))

    def _write_meta(self, html_path: Path, meta: dict) -> None:
        self._meta_path(html_path).write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # --- processed/ --------------------------------------------------------------------------------

    def write_jsonl(self, site: str, ads: Iterable[JobAd]) -> Path:
        path = self._processed_path(f"{site}.jsonl")
        with path.open("w", encoding="utf-8") as out:
            for ad in sorted(ads, key=lambda a: a.job_id):
                out.write(json.dumps(ad.to_dict(), ensure_ascii=False) + "\n")
        return path

    def read_jsonl(self, site: str) -> list[JobAd]:
        path = self.processed_dir / f"{site}.jsonl"
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as lines:
            return [JobAd.from_dict(json.loads(line)) for line in lines if line.strip()]

    def write_combined_csv(self, ads: Iterable[JobAd]) -> Path:
        """All sites in one table; list fields are joined with "; "."""
        path = self._processed_path("combined.csv")
        with path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=FIELDS)
            writer.writeheader()
            for ad in sorted(ads, key=lambda a: a.key):
                row = ad.to_dict()
                row["sectors"] = "; ".join(ad.sectors)
                row["categories"] = "; ".join(ad.categories)
                writer.writerow(row)
        return path

    def write_dedup_log(self, rows: Iterable[dict]) -> Path:
        path = self._processed_path("dedup_log.csv")
        with path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=["kept", "removed", "reason", "score"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def read_dedup_log(self) -> list[dict]:
        path = self.processed_dir / "dedup_log.csv"
        if not path.exists():
            return []
        with path.open(encoding="utf-8", newline="") as rows:
            return list(csv.DictReader(rows))

    def record_listing_counts(self, site: str, counts: dict[str, int], checked_at: str) -> Path:
        """Remember how many ads each sector's listing pages showed (kept per sector across runs)."""
        path = self._processed_path("listing_counts.json")
        data = self.listing_counts()
        for sector, listed in counts.items():
            data.setdefault(site, {})[sector] = {"listed": listed, "checked_at": checked_at}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def listing_counts(self) -> dict:
        path = self.processed_dir / "listing_counts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def _processed_path(self, name: str) -> Path:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        return self.processed_dir / name
