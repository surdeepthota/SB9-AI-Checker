"""Layer 3 — Forensics Panel.

This is where the project's actual AI/ML models live. It only ever runs when layer 1
comes back UNTRUSTED (no usable C2PA manifest) — a verified camera capture short-
circuits before this file is even imported, and a verified AI assertion or a tampered
hash both route elsewhere. See pipeline.py for that early-exit logic.

The panel is four independent signals, not a chain — one signal failing doesn't rule
out running the others, and none of them alone is treated as a verdict:

  1. EXIF / metadata check   — deterministic read, soft signal, free & instant
  2. Error Level Analysis     — probabilistic, team-written, catches splices
  3. FFT / frequency domain   — probabilistic, catches generator upsampling artifacts
  4. Pretrained ML classifier — probabilistic, least reliable (~80% SOTA accuracy),
                                 heaviest compute; NEVER trained in-house, only ever
                                 pretrained weights pulled from Hugging Face

Fusion across these four is deliberately a transparent, rules-based indicator count —
not a learned meta-model — so a judge (or a teammate) can read the exact logic that
turns four numbers into "how many indicators fired," see fuse_signals() at the bottom.
"""

from __future__ import annotations

from peachcheck.schema import ForensicSignal, ForensicsBlock

try:
    from PIL import Image, ImageChops  # Pillow: image loading + the ELA re-save/diff step
    import numpy as np  # FFT + array math for both ELA and the frequency-domain signal

    _IMAGE_LIBS_AVAILABLE = True
except ImportError:
    _IMAGE_LIBS_AVAILABLE = False

# AI-tool tags that show up in EXIF/XMP metadata when a generator writes them at all.
# Not exhaustive — this list is a starting point to extend as new tools are surveyed.
KNOWN_AI_TOOL_TAGS = ("midjourney", "dall-e", "dalle", "stable diffusion", "firefly")


# --------------------------------------------------------------------------------
# Signal 1: EXIF / metadata — deterministic read, soft signal
# --------------------------------------------------------------------------------
def check_metadata(exif_tags: dict[str, str]) -> ForensicSignal:
    """Real photos usually carry camera make/model/lens/GPS/timestamp; AI outputs
    usually carry none of that, and some generators leave their own tool tag instead.

    Weakness (report this honestly, don't hide it): screenshots and re-uploads strip
    metadata during re-encoding, so "no camera data" alone is a weak signal — it's
    consistent with both "this is AI-generated" and "this is a real photo someone
    screenshotted." Only an explicit AI-tool tag is strong evidence by itself.
    """
    has_camera_data = any(key in exif_tags for key in ("Make", "Model", "LensModel", "GPSInfo"))
    tool_tag_found = next(
        (tag for tag in KNOWN_AI_TOOL_TAGS if any(tag in v.lower() for v in exif_tags.values())),
        None,
    )
    triggered = tool_tag_found is not None or not has_camera_data
    explanation = (
        f'Metadata names an AI tool ("{tool_tag_found}").'
        if tool_tag_found
        else "No camera metadata found (weak on its own — re-encoding also strips this)."
        if triggered
        else "Camera metadata present and consistent with a real capture."
    )
    return ForensicSignal(
        name="metadata",
        triggered=triggered,
        raw_value=1.0 if tool_tag_found else (0.6 if triggered else 0.0),
        threshold=0.5,
        explanation=explanation,
    )


# --------------------------------------------------------------------------------
# Signal 2: Error Level Analysis — probabilistic, team-written
# --------------------------------------------------------------------------------
def compute_ela(image_path: str, resave_quality: int = 90) -> "np.ndarray":
    """Re-save the image at a known JPEG quality and diff it against the original.

    Why this works: every region of a *genuinely* single-generation JPEG compresses at
    roughly the same error level on a re-save. A region that was pasted in from a
    different source (or re-compressed separately) sits at a different error level and
    "lights up" in the diff — classic splice detection, not an "is this AI" test.
    """
    if not _IMAGE_LIBS_AVAILABLE:
        raise RuntimeError("Pillow and numpy are required: pip install -r requirements.txt")

    original = Image.open(image_path).convert("RGB")
    resaved_path = f"{image_path}.ela_tmp.jpg"
    original.save(resaved_path, "JPEG", quality=resave_quality)
    resaved = Image.open(resaved_path)

    diff = ImageChops.difference(original, resaved)
    return np.asarray(diff, dtype=np.float64)


def check_ela(image_path: str, trigger_threshold: float = 25.0) -> ForensicSignal:
    """Flag when the ELA residual's mean intensity crosses `trigger_threshold`.

    Threshold is a placeholder pending calibration against the labeled corpus (see
    judgment.py) — the number itself isn't load-bearing yet, the *mechanism* is.
    """
    diff = compute_ela(image_path)
    mean_error = float(diff.mean())
    triggered = mean_error > trigger_threshold
    return ForensicSignal(
        name="error_level_analysis",
        triggered=triggered,
        raw_value=round(mean_error, 2),
        threshold=trigger_threshold,
        explanation=(
            "Residual compression error is unevenly distributed, consistent with a "
            "pasted-in or separately re-compressed region."
            if triggered
            else "Compression error is uniform across the image."
        ),
    )


# --------------------------------------------------------------------------------
# Signal 3: FFT / frequency domain — probabilistic
# --------------------------------------------------------------------------------
def compute_fft_high_freq_energy(image_path: str) -> float:
    """Fourier-transform the (grayscale) image and measure energy in the high-
    frequency ring. Camera sensors leave natural, roughly isotropic noise; many
    generators leave periodic grid artifacts from learned upsampling, which shows up
    as excess energy concentrated at specific high frequencies rather than spread out.
    """
    if not _IMAGE_LIBS_AVAILABLE:
        raise RuntimeError("Pillow and numpy are required: pip install -r requirements.txt")

    grayscale = np.asarray(Image.open(image_path).convert("L"), dtype=np.float64)
    spectrum = np.fft.fftshift(np.fft.fft2(grayscale))
    magnitude = np.abs(spectrum)

    height, width = magnitude.shape
    center_y, center_x = height // 2, width // 2
    y_idx, x_idx = np.ogrid[:height, :width]
    radius = np.sqrt((y_idx - center_y) ** 2 + (x_idx - center_x) ** 2)

    # "High frequency" = outer 25% of the radial spectrum by distance from center.
    outer_ring_mask = radius >= 0.75 * radius.max()
    return float(magnitude[outer_ring_mask].sum() / magnitude.sum())


def check_fft(image_path: str, trigger_threshold: float = 0.15) -> ForensicSignal:
    """Flag when high-frequency energy exceeds what natural sensor noise typically
    produces. Known weakness: newer generators specifically suppress this artifact, so
    this signal skews toward catching cheaper/older fakes rather than SOTA ones.
    """
    high_freq_ratio = compute_fft_high_freq_energy(image_path)
    triggered = high_freq_ratio > trigger_threshold
    return ForensicSignal(
        name="fft_frequency_domain",
        triggered=triggered,
        raw_value=round(high_freq_ratio, 4),
        threshold=trigger_threshold,
        explanation=(
            "Excess high-frequency energy, consistent with generator upsampling "
            "artifacts (weaker against newer generators that suppress this)."
            if triggered
            else "High-frequency energy is within the range typical of sensor noise."
        ),
    )


# --------------------------------------------------------------------------------
# Signal 4: Pretrained ML classifier — probabilistic, least reliable
# --------------------------------------------------------------------------------
def check_ml_classifier(image_path: str, trigger_threshold: float = 0.5) -> ForensicSignal:
    """Score this image with a pretrained deepfake/AI-image classifier.

    Model policy [LOCKED]: pretrained weights only, pulled from Hugging Face — we
    never train our own. Real-world state-of-the-art for this task is only ~80%
    accurate outside curated benchmarks, which is why this is the *least* trusted
    signal in the panel and, per judgment.py's gate rule, can never by itself justify
    the SB 9 reporting path.

    TODO(week 1): load a real Hugging Face pipeline here, e.g.
        from transformers import pipeline
        classifier = pipeline("image-classification", model="<chosen-model-id>")
        result = classifier(image_path)
        fake_likelihood = next(r["score"] for r in result if r["label"] == "fake")
    Model choice is an open decision — swap the model id, not this function's shape,
    once the team picks one and records the choice + accuracy figures here.
    """
    raise NotImplementedError(
        "Wire up a Hugging Face image-classification pipeline; see TODO above."
    )


# --------------------------------------------------------------------------------
# Fusion — transparent, rules-based indicator counting (not a learned meta-model)
# --------------------------------------------------------------------------------
def fuse_signals(signals: list[ForensicSignal]) -> ForensicsBlock:
    """Bundle the four signals into one block. This function intentionally does
    nothing clever: judgment.py is where triggered-count feeds into the calibrated
    score, kept separate so the forensics layer never itself renders a verdict.
    """
    return ForensicsBlock(signals=signals)
