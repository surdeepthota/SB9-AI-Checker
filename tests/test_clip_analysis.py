"""Regression coverage for clip frame preview sizing.

peachcheck/clip_analysis.py used to embed each sampled frame at full video
resolution as a lossless PNG data URI. For a 1080x1920 vertical clip that's
~1.3MB per frame; five frames blew well past both sessionStorage's quota and
history.pushState's size limit in the browser, so the clip report would render
once from in-memory state and then vanish on the next re-render. Frame previews
now go through the same downscaling every other report evidence image uses.
"""

from PIL import Image

from peachcheck.clip_analysis import _thumbnail_data_uri


def test_frame_preview_is_downscaled_not_full_resolution():
    full_res = Image.new("RGB", (1080, 1920), (60, 90, 120))
    preview = _thumbnail_data_uri(full_res)

    assert preview.startswith("data:image/png;base64,")
    # A same-size, uncapped PNG of this image would encode to well over 100KB;
    # the downscaled thumbnail should land in the low tens of KB.
    assert len(preview) < 100_000
