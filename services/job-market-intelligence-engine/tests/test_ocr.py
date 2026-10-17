"""OCR of flyer images. Most tests use a stand-in reader; one uses the real Tesseract if installed."""

import json
import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.collectors import run
from app.collectors.config import Settings
from app.collectors.models import JobAd, ListingEntry
from app.collectors.storage import Storage
from app.processing import ocr
from app.processing.ocr import add_ocr_text, cache_path, read_image, tesseract_available

FIXTURES = Path(__file__).parent / "fixtures" / "topjobs"
FLYER_TEXT = "Requirements:\nDegree in HR\n2+ years experience in payroll\nApply to hr@upcot.lk"


class FakeReader:
    def __init__(self, text=FLYER_TEXT):
        self.text = text
        self.calls = 0

    def __call__(self, path):
        self.calls += 1
        return self.text


def image_ad(tmp_path, job_id="1", **fields):
    image = tmp_path / f"{job_id}.png"
    if not image.exists():  # rewriting it would make it "newer" than its cached text
        image.write_bytes(b"\x89PNG")
    return JobAd(site="topjobs", job_id=job_id, url=f"https://x/{job_id}", is_image_ad=True,
                 image_path=str(image), **fields)


def test_image_ad_gets_its_flyer_text_without_personal_data(tmp_path):
    ad = image_ad(tmp_path)
    stats = add_ocr_text([ad])

    assert stats.read == 0 and stats.failed == 1  # not a real PNG: counted, run continues
    ad = image_ad(tmp_path)
    stats = add_ocr_text([ad], reader=FakeReader())
    assert stats.read == 1
    assert "Degree in HR" in ad.description_text
    assert "hr@upcot.lk" not in ad.description_text and "[email removed]" in ad.description_text


def test_raw_text_is_cached_privately_and_cleaned_on_every_use(tmp_path):
    ad = image_ad(tmp_path)
    add_ocr_text([ad], reader=FakeReader())

    cache = cache_path(Path(ad.image_path))
    assert cache == tmp_path / "1.ocr.txt"  # next to the flyer, in the private raw/ layer
    assert "hr@upcot.lk" in cache.read_text()  # raw, so better cleaning rules apply later


def test_each_flyer_is_read_once_then_cached(tmp_path):
    reader = FakeReader()
    add_ocr_text([image_ad(tmp_path)], reader=reader)
    stats = add_ocr_text([image_ad(tmp_path)], reader=reader)

    assert reader.calls == 1 and stats.cached == 1


def test_a_newer_flyer_is_read_again(tmp_path):
    reader = FakeReader()
    ad = image_ad(tmp_path)
    add_ocr_text([ad], reader=reader)
    os.utime(cache_path(Path(ad.image_path)), (1, 1))  # cache older than the flyer

    add_ocr_text([image_ad(tmp_path)], reader=reader)
    assert reader.calls == 2


def test_text_ads_and_flyers_without_text(tmp_path):
    text_ad = JobAd(site="topjobs", job_id="2", url="https://x/2", description_text="Java")
    banner = image_ad(tmp_path, job_id="3")
    stats = add_ocr_text([text_ad, banner], reader=FakeReader(text="  \n "))

    assert text_ad.description_text == "Java"  # untouched
    assert banner.description_text is None and stats.no_text == 1


def test_missing_flyer_is_skipped(tmp_path):
    ad = JobAd(site="topjobs", job_id="4", url="https://x/4", is_image_ad=True, image_path=str(tmp_path / "gone.png"))
    assert add_ocr_text([ad], reader=FakeReader()).failed == 1


@pytest.mark.skipif(not tesseract_available(), reason="Tesseract is not installed")
def test_real_tesseract_reads_a_flyer(tmp_path):
    image = Image.new("RGB", (900, 200), "white")
    ImageDraw.Draw(image).text((30, 60), "Minimum 2 years experience", fill="black",
                               font=ImageFont.load_default(size=48))
    path = tmp_path / "flyer.png"
    image.save(path)
    assert "experience" in read_image(path).lower()


def test_collection_pipeline_uses_flyer_text(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    url = ("https://www.topjobs.lk/employer/JobAdvertismentServlet?rid=0&ac=DEFZZZ&jc=0001560048"
           "&ec=DEFZZZ&pg=applicant/vacancybyfunctionalarea.jsp")
    entry = ListingEntry("topjobs", "0001560048", url, "HR", "HAT")
    storage.save_raw(entry, (FIXTURES / "ad.html").read_text(), "2026-10-17T10:00:00+00:00",
                     image=b"\x89PNG", image_extension=".png")
    monkeypatch.setattr(run, "tesseract_available", lambda: True)
    monkeypatch.setattr(run, "add_ocr_text", lambda ads: ocr.add_ocr_text(ads, reader=FakeReader()))

    assert run.main(["--site", "topjobs", "--reparse"], settings=Settings(tmp_path, None)) == 0

    [record] = [json.loads(line) for line in (tmp_path / "processed" / "topjobs.jsonl").read_text().splitlines()]
    assert record["is_image_ad"] and record["experience_level"] == "2+ years"
    assert record["requirements_text"].startswith("Degree in HR")
    assert "hr@upcot.lk" not in record["description_text"]
    assert "OCR:** text was read from 1 of 1 image ads" in (tmp_path / "processed" / "quality_report.md").read_text()
