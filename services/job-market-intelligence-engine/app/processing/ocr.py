"""Text from image flyers, read with Tesseract OCR (offline).

Almost every topjobs ad is a single flyer image, so its requirements can only be read after OCR.
Each stored flyer is read once. The raw OCR text is cached next to the flyer in the private raw/
layer (``<job_id>.ocr.txt``), because, like the flyer itself, it can contain contact details.
Personal data is removed every time the text is used, so improved cleaning rules apply to
already-read flyers without reading them again. A flyer replaced by a newer download is read again.

Known OCR errors to keep in mind when analysing the text: dashes are often lost ("1–6 years"
becomes "16 years"; experience over 15 years is therefore ignored), "A/L" may read as "AIL",
decorative graphics produce stray characters, and two-column layouts interleave lines.
English only: Sinhala and Tamil flyers would need extra Tesseract language packs.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import pytesseract
from PIL import Image

from app.collectors.models import JobAd
from app.collectors.text_utils import scrub_personal_data

LANGUAGE = "eng"

log = logging.getLogger(__name__)


@dataclass
class OcrStats:
    read: int = 0  # flyers read with Tesseract in this run
    cached: int = 0  # flyers whose text was already cached
    no_text: int = 0  # flyers with no readable text (e.g. logo-only banners)
    failed: int = 0  # flyers that could not be opened or read


def tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        return False
    return True


def read_image(path: Path) -> str:
    """Raw OCR text of one image (greyscale reads more reliably than colour flyers)."""
    with Image.open(path) as image:
        return pytesseract.image_to_string(image.convert("L"), lang=LANGUAGE)


def cache_path(flyer: Path) -> Path:
    """Raw OCR text is cached next to its flyer: raw/<site>/<sector>/<job_id>.ocr.txt."""
    return flyer.with_suffix(".ocr.txt")


def cached_text(flyer: Path) -> str | None:
    """The cached text, unless the flyer on disk is newer than it."""
    path = cache_path(flyer)
    if not path.exists() or path.stat().st_mtime < flyer.stat().st_mtime:
        return None
    return path.read_text(encoding="utf-8")


def add_ocr_text(ads: Iterable[JobAd], reader: Callable[[Path], str] = read_image) -> OcrStats:
    """Fill in the description of each image ad from its flyer, without personal data."""
    stats = OcrStats()
    for ad in ads:
        if not ad.is_image_ad or not ad.image_path or ad.description_text:
            continue
        flyer = Path(ad.image_path)
        if not flyer.is_file():
            log.warning("Flyer missing for %s: %s", ad.key, flyer)
            stats.failed += 1
            continue
        raw_text = cached_text(flyer)
        if raw_text is None:
            try:
                raw_text = reader(flyer)
            except Exception as exc:  # a corrupt or unsupported image must not stop the run
                log.warning("OCR failed for %s: %s", ad.key, exc)
                stats.failed += 1
                continue
            cache_path(flyer).write_text(raw_text, encoding="utf-8")
            stats.read += 1
        else:
            stats.cached += 1
        ad.description_text = scrub_personal_data(raw_text)
        if not ad.description_text:
            stats.no_text += 1
    return stats
