"""Shared fixtures. The unit suite must run fast and offline: the ML classifier is
forced into its honest "unavailable" degradation path here so no model weights load.
The corpus regression suite (test_corpus.py, `-m corpus`) runs everything for real.
"""

import pytest

from peachcheck.layers import forensics


@pytest.fixture(autouse=True)
def no_ml_model(request, monkeypatch):
    """Skip the Hugging Face model load in unit tests (not in `-m corpus` runs)."""
    if "corpus" in request.keywords:
        return
    monkeypatch.setattr(forensics, "_ml_pipeline", None)
    monkeypatch.setattr(forensics, "_ml_load_failed", "disabled in unit tests")


@pytest.fixture
def tiny_jpeg(tmp_path):
    """A small uniform JPEG with no metadata and no manifest."""
    from PIL import Image

    path = tmp_path / "plain.jpg"
    Image.new("RGB", (64, 64), (120, 140, 160)).save(path, "JPEG", quality=90)
    return str(path)
