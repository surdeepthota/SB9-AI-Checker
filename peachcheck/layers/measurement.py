"""Layer 2 — Disclosure Measurement (the AdCheck module).

Not an AI model either. Only reached when layer 1 says VALID_AI_ASSERTED (the file's
own manifest admits it's AI-generated media) or a user manually flags something as a
campaign ad. This layer answers a narrower, purely mechanical question: does the
disclosure on this ad clear the specific numeric bars Georgia SB 9 §21-5-92 sets?

Every check below produces a reproducible number plus the evidence behind it (a
bounding box, a contrast ratio, a loudness reading) — never an opinion. That's the
point: a human (or a judge) should be able to redo the arithmetic by hand and get the
same pass/fail.

SB 9 §21-5-92 thresholds implemented here:
    (i)   text height  >= 30% of the vertical picture height
    (ii)  disclosure visible for >= 30% of the media's duration (video)
    (iii) reasonable color contrast (WCAG-style contrast ratio; black-on-white is a
          safe harbor, otherwise contrast must be no less than the ad's own body text)
    (iv)  audio-only media: same volume (LUFS) and same speaking rate (WPM) as the ad
          body, in every spoken language used
"""

from __future__ import annotations

from peachcheck.schema import MeasurementBlock, MeasurementResult

# The statute's own numbers — named constants so a reviewer can check them against the
# bill text in one place instead of hunting for magic numbers throughout the module.
MIN_TEXT_HEIGHT_RATIO = 0.30
MIN_VISIBLE_DURATION_RATIO = 0.30
SAFE_HARBOR_CONTRAST_RATIO = 21.0  # pure black on pure white; see _contrast_ratio()


def check_text_height(disclosure_bbox_height_px: float, frame_height_px: float) -> MeasurementResult:
    """§21-5-92(1)(B)(i): disclosure text must be at least 30% of the frame's height."""
    ratio = disclosure_bbox_height_px / frame_height_px
    return MeasurementResult(
        name="text_height_ratio",
        measured_value=round(ratio, 4),
        required_bar=MIN_TEXT_HEIGHT_RATIO,
        passed=ratio >= MIN_TEXT_HEIGHT_RATIO,
    )


def check_visible_duration(frames_with_disclosure: int, total_frames: int) -> MeasurementResult:
    """§21-5-92(1)(B)(ii): disclosure must be on-screen for >= 30% of total duration."""
    ratio = frames_with_disclosure / total_frames if total_frames else 0.0
    return MeasurementResult(
        name="visible_duration_ratio",
        measured_value=round(ratio, 4),
        required_bar=MIN_VISIBLE_DURATION_RATIO,
        passed=ratio >= MIN_VISIBLE_DURATION_RATIO,
    )


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance of an sRGB color. Pure math — see WCAG 2.x formula."""

    def _linearize(channel_8bit: int) -> float:
        c = channel_8bit / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (_linearize(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(color_a: tuple[int, int, int], color_b: tuple[int, int, int]) -> float:
    """WCAG contrast ratio between two sRGB colors; ranges from 1.0 (no contrast) to
    21.0 (black on white), which is why SAFE_HARBOR_CONTRAST_RATIO above is 21.0.
    """
    lum_a = _relative_luminance(color_a) + 0.05
    lum_b = _relative_luminance(color_b) + 0.05
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return lighter / darker


def check_contrast(
    text_color_rgb: tuple[int, int, int],
    background_color_rgb: tuple[int, int, int],
    body_text_contrast_ratio: float,
) -> MeasurementResult:
    """§21-5-92(1)(B)(iii): black-on-white is a safe harbor; otherwise the disclosure's
    contrast must be no less than the contrast used for the ad's own largest body text.
    """
    measured = _contrast_ratio(text_color_rgb, background_color_rgb)
    bar = min(SAFE_HARBOR_CONTRAST_RATIO, body_text_contrast_ratio)
    return MeasurementResult(
        name="contrast_ratio",
        measured_value=round(measured, 2),
        required_bar=round(bar, 2),
        passed=measured >= bar,
    )


def check_audio_parity(
    disclosure_lufs: float,
    body_lufs: float,
    disclosure_wpm: float,
    body_wpm: float,
    lufs_tolerance: float = 1.0,
    wpm_tolerance: float = 5.0,
) -> list[MeasurementResult]:
    """§21-5-92(2): audio-only disclosure must match the ad body's volume and speaking
    rate. Tolerances exist because "same" loudness/rate can't mean bit-identical —
    thresholds are a placeholder pending real calibration against sample ads.
    """
    volume_diff = abs(disclosure_lufs - body_lufs)
    rate_diff = abs(disclosure_wpm - body_wpm)
    return [
        MeasurementResult(
            name="audio_volume_parity_lufs",
            measured_value=round(volume_diff, 2),
            required_bar=lufs_tolerance,
            passed=volume_diff <= lufs_tolerance,
        ),
        MeasurementResult(
            name="audio_rate_parity_wpm",
            measured_value=round(rate_diff, 2),
            required_bar=wpm_tolerance,
            passed=rate_diff <= wpm_tolerance,
        ),
    ]


def run_measurement(checks: list[MeasurementResult]) -> MeasurementBlock:
    """Assemble already-computed checks into the layer's output block.

    Frame extraction, OCR (e.g. pytesseract), and LUFS/WPM extraction from actual media
    files are intentionally left to a separate ingestion step, not this module — this
    keeps the pass/fail arithmetic above testable with plain numbers, independent of
    whichever OCR/audio library ends up wired in.
    """
    return MeasurementBlock(checks=checks)
