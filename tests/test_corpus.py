"""The corpus settles arguments: every bundled sample must land in its ground-truth
provenance state, with the real ML model and OCR engine engaged.

Run explicitly (slow — loads model weights):  pytest -m corpus
Excluded from the default suite by pytest.ini.
"""

import csv
import os

import pytest

from peachcheck.pipeline import run_pipeline

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE, "corpus", "metadata.csv")
SAMPLES = os.path.join(BASE, "corpus", "samples")


def _corpus_rows():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="") as f:
        return [
            row
            for row in csv.DictReader(f)
            if os.path.exists(os.path.join(SAMPLES, row["filename"]))
        ]


@pytest.mark.corpus
@pytest.mark.parametrize("row", _corpus_rows(), ids=lambda r: r["filename"])
def test_sample_lands_in_ground_truth_state(row):
    path = os.path.join(SAMPLES, row["filename"])
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    report = run_pipeline(path, mime, "2026-07-12T12:00:00+00:00", is_campaign_ad=True)
    assert report.provenance.state.value == row["c2pa_state"], report.headline


@pytest.mark.corpus
def test_compliant_ad_passes_all_disclosure_bars():
    path = os.path.join(SAMPLES, "peachcheck-ad-compliant.jpg")
    if not os.path.exists(path):
        pytest.skip("demo corpus not generated")
    report = run_pipeline(path, "image/jpeg", "2026-07-12T12:00:00+00:00")
    assert report.measurement is not None
    assert report.measurement.all_passed, [
        (c.name, c.measured_value) for c in report.measurement.checks if not c.passed
    ]


@pytest.mark.corpus
def test_laundered_copy_keeps_perceptual_hash():
    original = os.path.join(SAMPLES, "peachcheck-ad-compliant.jpg")
    stripped = os.path.join(SAMPLES, "peachcheck-ad-stripped.jpg")
    if not (os.path.exists(original) and os.path.exists(stripped)):
        pytest.skip("demo corpus not generated")
    from peachcheck.pipeline import compute_dhash

    a, b = compute_dhash(original), compute_dhash(stripped)
    assert bin(int(a, 16) ^ int(b, 16)).count("1") <= 6
