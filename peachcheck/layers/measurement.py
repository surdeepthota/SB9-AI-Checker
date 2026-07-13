"""Layer 2 — Disclosure Measurement (the AdCheck module).

Not an AI model either. Only reached when layer 1 says VALID_AI_ASSERTED (the file's
own manifest admits it's AI-generated media) or a user manually flags something as a
campaign ad. This layer answers a narrower, purely mechanical question: does the
disclosure on this ad clear the specific numeric bars Georgia SB 9 §21-5-92 sets?

Every check below produces a reproducible number plus the evidence behind it (a
bounding box, a contrast ratio, a loudness reading) — never an opinion. That's the
point: a human (or a judge) should be able to redo the arithmetic by hand and get the
same pass/fail.

SB 9 thresholds implemented here:
    §21-5-91(a) content items: the ad must disclose (1) who sponsored/paid for it,
          (2) each person impersonated, (3) that depicted events may not have
          occurred, (4) that AI was used. Items 1, 3, 4 are checked by transparent
          keyword rules; item 2 requires knowing who appears in the ad, which no
          measurement can do — it's flagged for the human filer instead.
    §21-5-92(1)(B)(i)   text height >= 30% of the vertical picture height
    §21-5-92(1)(B)(ii)  disclosure visible for >= 30% of the media's duration (video —
                        reported N/A for still images, this phase's scope)
    §21-5-92(1)(B)(iii) reasonable color contrast (WCAG-style contrast ratio;
                        black-on-white is a safe harbor, otherwise no less than the
                        ad's own largest text)
    §21-5-92(2)         audio-only media: same volume (LUFS) and speaking rate (WPM)

The module is split in two: pure pass/fail arithmetic on plain numbers (testable with
no OCR installed), and an ingestion section that extracts those numbers from a real
image via OCR — pytesseract if the tesseract binary exists (the Docker image installs
it), otherwise EasyOCR, otherwise an honest "OCR unavailable" note in the block.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Optional

from peachcheck.imaging import to_data_uri
from peachcheck.schema import MeasurementBlock, MeasurementResult

# The statute's own numbers — named constants so a reviewer can check them against the
# bill text in one place instead of hunting for magic numbers throughout the module.
MIN_TEXT_HEIGHT_RATIO = 0.30
MIN_VISIBLE_DURATION_RATIO = 0.30
SAFE_HARBOR_CONTRAST_RATIO = 21.0  # pure black on pure white; see _contrast_ratio()
# When the ad has no other text to compare against, the statute's "reasonable
# contrast" has no in-frame baseline; WCAG AA's 4.5:1 is the documented proxy bar.
FALLBACK_CONTRAST_BAR = 4.5


# --------------------------------------------------------------------------------
# Pure pass/fail arithmetic — no OCR, no file I/O
# --------------------------------------------------------------------------------
def check_text_height(disclosure_bbox_height_px: float, frame_height_px: float) -> MeasurementResult:
    """§21-5-92(1)(B)(i): disclosure text must be at least 30% of the frame's height."""
    ratio = disclosure_bbox_height_px / frame_height_px
    return MeasurementResult(
        name="text_height_ratio",
        measured_value=round(ratio, 4),
        required_bar=MIN_TEXT_HEIGHT_RATIO,
        passed=ratio >= MIN_TEXT_HEIGHT_RATIO,
        detail=(
            f"Disclosure text is {ratio:.1%} of the frame height; the statute "
            f"requires at least {MIN_TEXT_HEIGHT_RATIO:.0%}."
        ),
    )


def check_visible_duration(frames_with_disclosure: int, total_frames: int) -> MeasurementResult:
    """§21-5-92(1)(B)(ii): disclosure must be on-screen for >= 30% of total duration."""
    ratio = frames_with_disclosure / total_frames if total_frames else 0.0
    return MeasurementResult(
        name="visible_duration_ratio",
        measured_value=round(ratio, 4),
        required_bar=MIN_VISIBLE_DURATION_RATIO,
        passed=ratio >= MIN_VISIBLE_DURATION_RATIO,
        detail=(
            f"Disclosure visible in {ratio:.1%} of sampled frames; the statute "
            f"requires at least {MIN_VISIBLE_DURATION_RATIO:.0%}."
        ),
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
    bar_description: str = "the ad's own largest text, capped at the 21:1 black-on-white safe harbor",
) -> MeasurementResult:
    """§21-5-92(1)(B)(iii): black-on-white is a safe harbor; otherwise the disclosure's
    contrast must be no less than the contrast used for the ad's own largest body text.

    `bar_description` names where the bar came from in the human-readable detail —
    the ingestion path passes a different description when the ad has no other text
    and the WCAG-AA proxy bar applies.
    """
    measured = _contrast_ratio(text_color_rgb, background_color_rgb)
    bar = min(SAFE_HARBOR_CONTRAST_RATIO, body_text_contrast_ratio)
    return MeasurementResult(
        name="contrast_ratio",
        measured_value=round(measured, 2),
        required_bar=round(bar, 2),
        passed=measured >= bar,
        detail=(
            f"Disclosure contrast measures {measured:.1f}:1 against a required bar "
            f"of {bar:.1f}:1 ({bar_description})."
        ),
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
    """Assemble already-computed checks into the layer's output block."""
    return MeasurementBlock(checks=checks)


# --------------------------------------------------------------------------------
# Disclosure-content detection — transparent keyword rules for §21-5-91(a)
# --------------------------------------------------------------------------------
# These rules are deliberately simple string patterns, documented here in one place,
# so the "did the ad disclose X" decision is auditable — no classifier involved.
# `\s*` (not `\s+`) between words because OCR engines sometimes drop the space
# between two words entirely ("NOTHAVE").
AI_USE_PATTERN = re.compile(
    r"(\bai\b|artificial\s*intelligence).{0,60}?(generat|creat|made|produc|used)"
    r"|(generat|creat|made|produc)\w*\s*(by|with|using)\s*(\bai\b|artificial\s*intelligence)",
    re.IGNORECASE | re.DOTALL,
)
EVENTS_CAVEAT_PATTERN = re.compile(
    r"may\s*not\s*have\s*(actually\s*)?occur|did\s*not\s*(actually\s*)?occur|not\s+(a\s+)?real\s+event",
    re.IGNORECASE,
)
SPONSOR_PATTERN = re.compile(
    r"paid\s*for\s*by|sponsored\s*by",
    re.IGNORECASE,
)


def normalize_ocr_text(text: str) -> str:
    """Undo the OCR confusions that would otherwise defeat the patterns above.

    The only rewrite performed is the classic capital-I/lowercase-l swap in the
    standalone token "AI" ("Al" as read by OCR). Deliberately narrow — broad fuzzy
    matching would undermine the point of these being auditable string rules.
    """
    return re.sub(r"\bA[lI1](?=\b|[.,;:!])", "AI", text)


@dataclass
class OcrLine:
    """One OCR'd text line with its bounding box in pixels (left, top, width, height)."""

    text: str
    left: int
    top: int
    width: int
    height: int


def is_disclosure_line(text: str) -> bool:
    """A line counts as disclosure language if it states AI use, the events caveat,
    or the sponsor — the §21-5-91(a) content items. Sponsor lines are included
    because the statute's disclosure is one block containing all of them, and the
    30% height bar applies to that block as displayed.
    """
    return bool(
        AI_USE_PATTERN.search(text)
        or EVENTS_CAVEAT_PATTERN.search(text)
        or SPONSOR_PATTERN.search(text)
    )


def find_disclosure_lines(lines: list[OcrLine]) -> list[OcrLine]:
    """Locate disclosure lines, tolerating phrases wrapped across two lines.

    A phrase like "GENERATED WITH ARTIFICIAL / INTELLIGENCE" matches neither line
    alone, so each line is also tested joined with the next line below it (in
    top-to-bottom order); a window match flags both lines.
    """
    ordered = sorted(lines, key=lambda line: line.top)
    flagged: set[int] = set()
    for i, line in enumerate(ordered):
        if is_disclosure_line(line.text):
            flagged.add(i)
        elif (
            i + 1 < len(ordered)
            # The window only counts when the match *spans* the line break — if the
            # next line matches on its own, joining would wrongly drag this line
            # (e.g. an unrelated slogan above the disclosure) into the block.
            and not is_disclosure_line(ordered[i + 1].text)
            and is_disclosure_line(line.text + " " + ordered[i + 1].text)
        ):
            flagged.add(i)
            flagged.add(i + 1)
    if not flagged:
        return []
    # Lines sandwiched between flagged lines belong to the same displayed block —
    # mid-sentence wraps don't match any pattern alone. _disclosure_block's vertical
    # clustering still splits genuinely separate runs afterward.
    return ordered[min(flagged) : max(flagged) + 1]


# --------------------------------------------------------------------------------
# Ingestion — OCR a real still image and run the checks above on the numbers
# --------------------------------------------------------------------------------
_easyocr_reader = None
_ocr_engine: Optional[str] = None  # resolved lazily: "tesseract" | "easyocr" | None
# Endpoints run in FastAPI's threadpool, so lazy engine/reader init must be locked —
# otherwise two concurrent first requests would each build the heavy easyocr reader.
_ocr_init_lock = threading.Lock()


def _resolve_ocr_engine() -> Optional[str]:
    """Pick the best OCR engine present in this environment, once."""
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine
    with _ocr_init_lock:
        if _ocr_engine is not None:
            return _ocr_engine
        try:
            import pytesseract

            pytesseract.get_tesseract_version()  # raises if the binary is missing
            _ocr_engine = "tesseract"
            return _ocr_engine
        except Exception:
            pass
        try:
            import easyocr  # noqa: F401

            _ocr_engine = "easyocr"
            return _ocr_engine
        except Exception:
            _ocr_engine = ""  # sentinel: resolution ran, nothing found
        return _ocr_engine


def _ocr_lines(image_path: str) -> tuple[list[OcrLine], Optional[str]]:
    """OCR the image into lines with pixel bounding boxes.

    Returns (lines, engine_name). engine_name is None when no OCR engine is available,
    which the caller must surface honestly rather than reporting "no text found".
    """
    engine = _resolve_ocr_engine()
    if not engine:
        return [], None

    if engine == "tesseract":
        import pytesseract
        from PIL import Image

        with Image.open(image_path) as img:
            data = pytesseract.image_to_data(
                img.convert("RGB"), output_type=pytesseract.Output.DICT
            )
        # Group word boxes into lines by tesseract's own (block, paragraph, line) ids.
        grouped: dict[tuple[int, int, int], list[int]] = {}
        for i, word in enumerate(data["text"]):
            if word.strip():
                key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                grouped.setdefault(key, []).append(i)
        lines = []
        for indices in grouped.values():
            words = [data["text"][i] for i in indices]
            lefts = [data["left"][i] for i in indices]
            tops = [data["top"][i] for i in indices]
            rights = [data["left"][i] + data["width"][i] for i in indices]
            bottoms = [data["top"][i] + data["height"][i] for i in indices]
            lines.append(
                OcrLine(
                    text=" ".join(words),
                    left=min(lefts),
                    top=min(tops),
                    width=max(rights) - min(lefts),
                    height=max(bottoms) - min(tops),
                )
            )
        return lines, "tesseract"

    # EasyOCR path: readtext already returns line/region-level detections.
    global _easyocr_reader
    import os

    # EasyOCR downloads its models with urllib, which on framework Python builds
    # (notably python.org macOS installs) has no root-CA bundle wired up. Point it
    # at certifi's bundle so the one-time model download can verify TLS.
    try:
        import certifi

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass
    import easyocr

    if _easyocr_reader is None:
        with _ocr_init_lock:
            if _easyocr_reader is None:
                _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    lines = []
    for box, text, _conf in _easyocr_reader.readtext(image_path):
        xs = [int(p[0]) for p in box]
        ys = [int(p[1]) for p in box]
        lines.append(
            OcrLine(
                text=text,
                left=min(xs),
                top=min(ys),
                width=max(xs) - min(xs),
                height=max(ys) - min(ys),
            )
        )
    return lines, "easyocr"


def _bbox_extremes(image, line: OcrLine) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Estimate the text and background colors inside a line's box.

    Proxy method (documented for the write-up): within the box, the darkest 5% of
    pixels approximate the text color and the brightest 95th percentile approximates
    the background (or vice versa — contrast is symmetric). This avoids needing exact
    glyph segmentation while staying a pure, reproducible computation.
    """
    import numpy as np

    crop = image.convert("L").crop(
        (line.left, line.top, line.left + line.width, line.top + line.height)
    )
    values = np.asarray(crop, dtype=np.uint8).ravel()
    if values.size == 0:
        return (0, 0, 0), (0, 0, 0)
    dark = int(np.percentile(values, 5))
    bright = int(np.percentile(values, 95))
    return (dark, dark, dark), (bright, bright, bright)


def _bbox_contrast(image, line: OcrLine) -> float:
    dark, bright = _bbox_extremes(image, line)
    return _contrast_ratio(dark, bright)


def _disclosure_block(disclosure_lines: list[OcrLine]) -> OcrLine:
    """Merge vertically-contiguous disclosure lines into one block and return the
    tallest such block as a synthetic OcrLine (union bounding box).

    Why a block, not a single line: a disclosure rendered across several lines is
    still one disclosure — §21-5-92's 30% bar applies to "the text" as displayed.
    Lines only merge when the vertical gap between them is modest (≤ 2.5× the median
    line height — ordinary paragraph leading), so a stray mention elsewhere in the
    frame can't stretch the box.
    """
    ordered = sorted(disclosure_lines, key=lambda line: line.top)
    median_height = sorted(line.height for line in ordered)[len(ordered) // 2]
    max_gap = 2.5 * median_height

    clusters: list[list[OcrLine]] = [[ordered[0]]]
    for line in ordered[1:]:
        prev = clusters[-1][-1]
        if line.top - (prev.top + prev.height) <= max_gap:
            clusters[-1].append(line)
        else:
            clusters.append([line])

    def union(cluster: list[OcrLine]) -> OcrLine:
        left = min(l.left for l in cluster)
        top = min(l.top for l in cluster)
        right = max(l.left + l.width for l in cluster)
        bottom = max(l.top + l.height for l in cluster)
        return OcrLine(
            text=" ".join(l.text for l in cluster),
            left=left,
            top=top,
            width=right - left,
            height=bottom - top,
        )

    return max((union(c) for c in clusters), key=lambda block: block.height)


def _annotate_evidence(image, disclosure_lines: list[OcrLine], frame_height: int) -> str:
    """Draw measurement boxes on a copy of the frame and return it as a data-URI.

    This is the "visual proof" requirement from the design doc: the report shows the
    exact box the height percentage was computed from, so the number is checkable.
    """
    from PIL import ImageDraw

    annotated = image.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)
    stroke = max(2, frame_height // 300)
    for line in disclosure_lines:
        box = (line.left, line.top, line.left + line.width, line.top + line.height)
        draw.rectangle(box, outline=(16, 185, 129), width=stroke)
        label = f"{line.height / frame_height:.1%} of frame height"
        draw.text((line.left, max(0, line.top - 14 - stroke)), label, fill=(16, 185, 129))

    return to_data_uri(annotated, max_dim=720)


def measure_still_image(image_path: str) -> MeasurementBlock:
    """Full layer-2 run for a still image: OCR, find disclosure language, measure it
    against the §21-5-91/§21-5-92 bars, and attach visual evidence.
    """
    from PIL import Image

    try:
        lines, engine = _ocr_lines(image_path)
    except Exception as exc:
        # A broken OCR install (or a failed one-time model download) must degrade to
        # an honest note, not sink the whole analysis.
        return MeasurementBlock(
            checks=[],
            note=(
                "Disclosure measurement could not run: the OCR engine failed "
                f"({type(exc).__name__}: {exc})."
            ),
        )
    if engine is None:
        return MeasurementBlock(
            checks=[],
            note=(
                "OCR engine unavailable in this environment — disclosure measurement "
                "could not run. Install tesseract or easyocr to enable this layer."
            ),
        )

    with Image.open(image_path) as img:
        frame = img.convert("RGB")
    frame_height = frame.height

    for line in lines:
        line.text = normalize_ocr_text(line.text)
    # Reading order for the full-text pattern checks: top-to-bottom, so a phrase
    # wrapped across lines stays contiguous in the joined string.
    all_text = " ".join(line.text for line in sorted(lines, key=lambda l: l.top))
    disclosure_lines = find_disclosure_lines(lines)

    checks: list[MeasurementResult] = []

    # -- §21-5-91(a) content items (keyword rules; see patterns above) --
    ai_stated = bool(AI_USE_PATTERN.search(all_text))
    checks.append(
        MeasurementResult(
            name="content_ai_use_stated",
            measured_value=1.0 if ai_stated else 0.0,
            required_bar=1.0,
            passed=ai_stated,
            detail=(
                "The ad states that AI was used."
                if ai_stated
                else "No statement that AI was used was found in the ad's text."
            ),
        )
    )
    events_stated = bool(EVENTS_CAVEAT_PATTERN.search(all_text))
    checks.append(
        MeasurementResult(
            name="content_events_caveat_stated",
            measured_value=1.0 if events_stated else 0.0,
            required_bar=1.0,
            passed=events_stated,
            detail=(
                "The ad states depicted events may not have actually occurred."
                if events_stated
                else "No 'events may not have occurred' caveat was found."
            ),
        )
    )
    sponsor_stated = bool(SPONSOR_PATTERN.search(all_text))
    checks.append(
        MeasurementResult(
            name="content_sponsor_named",
            measured_value=1.0 if sponsor_stated else 0.0,
            required_bar=1.0,
            passed=sponsor_stated,
            detail=(
                "A sponsor/'paid for by' statement is present."
                if sponsor_stated
                else "No sponsor or 'paid for by' statement was found."
            ),
        )
    )

    # -- §21-5-92(1)(B) format thresholds --
    evidence_uri = None
    if disclosure_lines:
        block = _disclosure_block(disclosure_lines)
        checks.append(check_text_height(block.height, frame_height))

        body_lines = [line for line in lines if line not in disclosure_lines]
        if body_lines:
            largest_body = max(body_lines, key=lambda line: line.height)
            body_contrast = _bbox_contrast(frame, largest_body)
        else:
            body_contrast = FALLBACK_CONTRAST_BAR
        text_color, background_color = _bbox_extremes(frame, block)
        checks.append(
            check_contrast(
                text_color,
                background_color,
                body_contrast,
                bar_description=(
                    "the ad's own largest text"
                    if body_lines
                    else "WCAG AA proxy — the ad has no other text to compare against"
                ),
            )
        )
        evidence_uri = _annotate_evidence(frame, [block], frame_height)
        for check in checks:
            if check.name == "text_height_ratio":
                check.evidence_ref = evidence_uri
    else:
        # No disclosure language found at all: the height check fails at 0% rather
        # than being skipped — absence of a required disclosure is the finding.
        checks.append(
            MeasurementResult(
                name="text_height_ratio",
                measured_value=0.0,
                required_bar=MIN_TEXT_HEIGHT_RATIO,
                passed=False,
                detail="No disclosure language was detected anywhere in the frame.",
            )
        )

    disclosure_text = " / ".join(line.text for line in disclosure_lines) or None
    return MeasurementBlock(
        checks=checks,
        disclosure_text=disclosure_text,
        note=(
            f"OCR engine: {engine}. Duration check (§21-5-92(1)(B)(ii)) is not "
            "applicable to still images. Impersonated-person disclosure "
            "(§21-5-91(a)(2)) cannot be measured automatically — it requires knowing "
            "who appears in the ad, and is flagged for the human filer instead."
        ),
    )
