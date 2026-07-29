"""Layer 3 — Forensics Panel.

This is where the project's probabilistic signals live. It only ever runs when layer 1
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
                                 pretrained weights pulled from Hugging Face. Runs two
                                 pretrained models and takes the higher reading — they
                                 miss different generators, so this catches more than
                                 either alone without raising real-photo scores.

Fusion across these four is deliberately transparent and rules-based — not a learned
meta-model. It uses a weighted panel score with a direct-evidence floor so a strong
AI-classifier result or explicit generator tag cannot be incorrectly averaged away by
quiet splice checks. See fuse_signals() at the bottom.
"""

from __future__ import annotations

import io
import threading
from typing import Optional

from peachcheck.imaging import to_data_uri as _to_data_uri
from peachcheck.schema import ForensicSignal, ForensicsBlock

try:
    from PIL import Image, ImageChops  # Pillow: image loading + the ELA re-save/diff step
    from PIL import ExifTags
    import numpy as np  # FFT + array math for both ELA and the frequency-domain signal

    _IMAGE_LIBS_AVAILABLE = True
except ImportError:
    _IMAGE_LIBS_AVAILABLE = False

# AI-tool tags that show up in EXIF/XMP/PNG-text metadata when a generator writes them
# at all. Not exhaustive — this list is a starting point to extend as tools are surveyed.
KNOWN_AI_TOOL_TAGS = (
    "midjourney",
    "dall-e",
    "dalle",
    "dall·e",
    "stable diffusion",
    "firefly",
    "imagen",
    "flux.1",
    "grok image",
    "gpt-image",
)

# Hugging Face models for signal 4. Pretrained weights only [LOCKED] — never trained
# in-house. Two models run as an ensemble (max of both probabilities) because they
# miss different things: umm-maybe/AI-image-detector's training data predates modern
# generators like Gemini/Imagen and Midjourney v6, so it badly underscores their
# output; haywoodsloan/ai-image-detector-deploy is more recent and catches some of
# what the first misses. Neither alone is reliable — see check_ml_classifier.
ML_MODEL_ID = "umm-maybe/AI-image-detector"
ML_MODEL_ID_SECONDARY = "haywoodsloan/ai-image-detector-deploy"

# Fusion weights [LOCKED as rules-based]. They produce the panel's corroborating score.
# The direct AI-generation evidence is also retained as a floor: a high classifier
# score or explicit generator tag must not be treated as negative merely because ELA
# (a splice detector) stays quiet on a fully generated image.
FUSION_WEIGHTS = {
    "metadata": 0.20,
    "error_level_analysis": 0.25,
    "fft_frequency_domain": 0.15,
    "ml_classifier": 0.40,
}


# --------------------------------------------------------------------------------
# Signal 1: EXIF / metadata — deterministic read, soft signal
# --------------------------------------------------------------------------------
def extract_metadata_text(image_path: str) -> tuple[dict[str, str], str]:
    """Pull EXIF tags plus any free-text metadata (PNG text chunks, XMP) from the file.

    Returns (exif_tags, extra_text) where extra_text is a lowercase blob searched for
    generator tool names — some generators write their name into PNG tEXt/XMP rather
    than EXIF proper.
    """
    exif_tags: dict[str, str] = {}
    extra_parts: list[str] = []
    try:
        with Image.open(image_path) as img:
            raw_exif = img.getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                    exif_tags[str(tag)] = str(value)
            for key, value in (img.info or {}).items():
                if isinstance(value, (str, bytes)):
                    text = value.decode("utf-8", "ignore") if isinstance(value, bytes) else value
                    extra_parts.append(f"{key}={text}")
    except Exception:
        pass
    return exif_tags, " ".join(extra_parts).lower()


def evaluate_metadata(exif_tags: dict[str, str], extra_text: str = "") -> ForensicSignal:
    """Real photos usually carry camera make/model/lens/GPS/timestamp; AI outputs
    usually carry none of that, and some generators leave their own tool tag instead.

    Weakness (report this honestly, don't hide it): screenshots and re-uploads strip
    metadata during re-encoding, so "no camera data" alone is a weak signal — it's
    consistent with both "this is AI-generated" and "this is a real photo someone
    screenshotted." Only an explicit AI-tool tag is strong evidence by itself.
    """
    has_camera_data = any(key in exif_tags for key in ("Make", "Model", "LensModel", "GPSInfo"))
    searchable = " ".join(v.lower() for v in exif_tags.values()) + " " + extra_text
    tool_tag_found = next((tag for tag in KNOWN_AI_TOOL_TAGS if tag in searchable), None)

    triggered = tool_tag_found is not None or not has_camera_data
    # Score ladder: explicit AI-tool tag = 1.0 (hard, self-declared evidence);
    # missing camera data = 0.6 (soft — re-encoding also produces this); camera
    # data present = 0.0.
    score = 1.0 if tool_tag_found else (0.6 if triggered else 0.0)
    explanation = (
        f'Metadata names an AI tool ("{tool_tag_found}") — a hard, self-declared indicator.'
        if tool_tag_found
        else "No camera metadata found (weak on its own — re-encoding also strips this)."
        if triggered
        else "Camera metadata present and consistent with a real capture."
    )
    return ForensicSignal(
        name="metadata",
        triggered=triggered,
        raw_value=score,
        threshold=0.5,
        score=score,
        explanation=explanation,
    )


def check_metadata(image_path: str) -> ForensicSignal:
    """File-facing wrapper: read the metadata, then run the pure evaluation above."""
    exif_tags, extra_text = extract_metadata_text(image_path)
    return evaluate_metadata(exif_tags, extra_text)


def metadata_names_ai_tool(signal: ForensicSignal) -> bool:
    """True when the metadata signal found an explicit generator tag — the "hard
    metadata contradiction" that counts as deterministic corroboration for the
    layer-4 gate (see judgment.gate_allows_reporting).
    """
    return signal.name == "metadata" and signal.score >= 1.0


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

    with Image.open(image_path) as original_file:
        original = original_file.convert("RGB")
    # Re-save into memory, not next to the user's file — no temp-file litter.
    resave_buf = io.BytesIO()
    original.save(resave_buf, "JPEG", quality=resave_quality)
    resave_buf.seek(0)
    resaved = Image.open(resave_buf).convert("RGB")

    diff = ImageChops.difference(original, resaved)
    return np.asarray(diff, dtype=np.float64)


def render_ela_heatmap(diff: "np.ndarray") -> "Image.Image":
    """Amplify the ELA residual into a viewable evidence image. The interesting
    information is *relative* brightness between regions, so normalize to the frame's
    own maximum rather than an absolute scale.
    """
    peak = diff.max() or 1.0
    amplified = np.clip(diff / peak * 255.0, 0, 255).astype("uint8")
    return Image.fromarray(amplified)


def check_ela(image_path: str, trigger_threshold: float = 0.35) -> ForensicSignal:
    """Flag when the ELA residual's mean intensity crosses `trigger_threshold`.

    Threshold calibrated against the demo corpus (see corpus/metadata.csv): the
    "untrusted" samples measure mean residuals of 0.22-0.48, and the synthetic
    splice fixture in tests/test_forensics.py measures ~1.0 against a ~0.0 uniform
    baseline. The old placeholder (25.0) sat far above every value either dataset
    can produce, so the signal could never trigger regardless of input.
    """
    diff = compute_ela(image_path)
    mean_error = float(diff.mean())
    triggered = mean_error > trigger_threshold
    return ForensicSignal(
        name="error_level_analysis",
        triggered=triggered,
        raw_value=round(mean_error, 2),
        threshold=trigger_threshold,
        # Suspicion saturates at twice the trigger threshold — readable, linear rule.
        score=round(min(mean_error / (2 * trigger_threshold), 1.0), 3),
        explanation=(
            "Residual compression error is unevenly distributed, consistent with a "
            "pasted-in or separately re-compressed region."
            if triggered
            else "Compression error is uniform across the image."
        ),
        evidence_ref=_to_data_uri(render_ela_heatmap(diff)),
    )


# --------------------------------------------------------------------------------
# Signal 3: FFT / frequency domain — probabilistic
# --------------------------------------------------------------------------------
def compute_fft_spectrum(image_path: str) -> "np.ndarray":
    """Centered 2-D FFT magnitude of the grayscale image."""
    if not _IMAGE_LIBS_AVAILABLE:
        raise RuntimeError("Pillow and numpy are required: pip install -r requirements.txt")

    with Image.open(image_path) as img:
        grayscale = np.asarray(img.convert("L"), dtype=np.float64)
    spectrum = np.fft.fftshift(np.fft.fft2(grayscale))
    return np.abs(spectrum)


def compute_fft_high_freq_energy(magnitude: "np.ndarray") -> float:
    """Measure energy in the high-frequency ring of the spectrum. Camera sensors
    leave natural, roughly isotropic noise; many generators leave periodic grid
    artifacts from learned upsampling, which shows up as excess energy concentrated
    at specific high frequencies rather than spread out.
    """
    height, width = magnitude.shape
    center_y, center_x = height // 2, width // 2
    y_idx, x_idx = np.ogrid[:height, :width]
    radius = np.sqrt((y_idx - center_y) ** 2 + (x_idx - center_x) ** 2)

    # "High frequency" = outer 25% of the radial spectrum by distance from center.
    outer_ring_mask = radius >= 0.75 * radius.max()
    total = magnitude.sum() or 1.0
    return float(magnitude[outer_ring_mask].sum() / total)


def render_fft_spectrum(magnitude: "np.ndarray") -> "Image.Image":
    """Log-scaled spectrum as a viewable evidence image (bright center = low
    frequencies; structured spokes/rings away from center are the artifacts the
    signal looks for)."""
    log_mag = np.log1p(magnitude)
    peak = log_mag.max() or 1.0
    scaled = (log_mag / peak * 255.0).astype("uint8")
    return Image.fromarray(scaled)


def check_fft(image_path: str, trigger_threshold: float = 0.03) -> ForensicSignal:
    """Flag when high-frequency energy exceeds what natural sensor noise typically
    produces. Known weakness: newer generators specifically suppress this artifact, so
    this signal skews toward catching cheaper/older fakes rather than SOTA ones.

    Threshold calibrated against the demo corpus: "untrusted" samples measure
    high-frequency ratios of 0.023-0.036, tightly clustered just under the old
    placeholder's headroom. 0.15 (a value only the synthetic noise fixture in
    tests/test_forensics.py ever reaches) left the signal dormant on every real
    image; 0.03 sits inside the corpus's own spread so the signal can actually fire.
    """
    magnitude = compute_fft_spectrum(image_path)
    high_freq_ratio = compute_fft_high_freq_energy(magnitude)
    triggered = high_freq_ratio > trigger_threshold
    return ForensicSignal(
        name="fft_frequency_domain",
        triggered=triggered,
        raw_value=round(high_freq_ratio, 4),
        threshold=trigger_threshold,
        score=round(min(high_freq_ratio / (2 * trigger_threshold), 1.0), 3),
        explanation=(
            "Excess high-frequency energy, consistent with generator upsampling "
            "artifacts (weaker against newer generators that suppress this)."
            if triggered
            else "High-frequency energy is within the range typical of sensor noise."
        ),
        evidence_ref=_to_data_uri(render_fft_spectrum(magnitude)),
    )


# --------------------------------------------------------------------------------
# Signal 4: Pretrained ML classifier — probabilistic, least reliable
# --------------------------------------------------------------------------------
_ml_pipelines: dict[str, object] = {}
_ml_load_failed: dict[str, str] = {}
_ml_init_lock = threading.Lock()


def _load_ml_pipeline(model_id: str):
    """Lazy, cached model load per model id — weights should download once, not per
    request, and an environment without transformers/torch should degrade to an
    honest "signal unavailable" rather than crash the whole panel. The lock matters
    because endpoints run in FastAPI's threadpool: without it, two concurrent first
    requests would both see nothing cached and load the weights twice.
    """
    if model_id in _ml_pipelines or model_id in _ml_load_failed:
        return
    with _ml_init_lock:
        if model_id in _ml_pipelines or model_id in _ml_load_failed:
            return
        try:
            from transformers import pipeline as hf_pipeline

            _ml_pipelines[model_id] = hf_pipeline("image-classification", model=model_id)
        except Exception as exc:  # ImportError, download failure, etc.
            _ml_load_failed[model_id] = f"{type(exc).__name__}: {exc}"


def _artificial_probability(model_id: str, image_path: str) -> float | None:
    """Run one model and return its "artificial" probability, or None if the model
    isn't available in this environment.
    """
    _load_ml_pipeline(model_id)
    pipeline_ = _ml_pipelines.get(model_id)
    if pipeline_ is None:
        return None
    results = pipeline_(image_path)
    return next(
        (r["score"] for r in results if r["label"].lower() in ("artificial", "fake", "ai")),
        0.0,
    )


def check_ml_classifier(image_path: str, trigger_threshold: float = 0.5) -> ForensicSignal:
    """Score this image with an ensemble of two pretrained AI-image classifiers.

    Model policy [LOCKED]: pretrained weights only — we never train our own. A single
    pretrained detector badly underscores images from generators newer than its
    training data (e.g. umm-maybe/AI-image-detector can score a real Gemini-generated
    image as low as ~9% "artificial"); running a second, more recent model and taking
    the max of both catches some of what either one alone misses, without raising
    real-photo scores (verified against the demo corpus's camera captures). This is
    still the *least* trusted signal in the panel — real-world state-of-the-art for
    this task is only ~80% accurate outside curated benchmarks even with an ensemble
    — and, per judgment.py's gate rule, can never by itself justify the SB 9
    reporting path.
    """
    scored = {
        model_id: _artificial_probability(model_id, image_path)
        for model_id in (ML_MODEL_ID, ML_MODEL_ID_SECONDARY)
    }
    available_scores = {k: v for k, v in scored.items() if v is not None}

    if not available_scores:
        failures = "; ".join(f"{k}: {v}" for k, v in _ml_load_failed.items())
        return ForensicSignal(
            name="ml_classifier",
            triggered=False,
            raw_value=0.0,
            threshold=trigger_threshold,
            score=0.0,
            available=False,
            explanation=(
                "Classifier not run — both models are unavailable in this environment "
                f"({failures}). The panel's other signals still apply; "
                "the fused score renormalizes over what actually ran."
            ),
        )

    best_model_id, artificial_prob = max(available_scores.items(), key=lambda kv: kv[1])
    triggered = artificial_prob > trigger_threshold
    ran_both = len(available_scores) > 1
    return ForensicSignal(
        name="ml_classifier",
        triggered=triggered,
        raw_value=round(artificial_prob, 4),
        threshold=trigger_threshold,
        score=round(artificial_prob, 4),
        explanation=(
            (
                f"Two pretrained classifiers scored this image; the higher reading "
                f"({best_model_id.split('/')[-1]}) put it at {artificial_prob:.0%} "
                "likely AI-generated."
                if ran_both
                else f"Pretrained classifier ({best_model_id}) scores this "
                f"{artificial_prob:.0%} likely AI-generated."
            )
            + " Treated as one indicator, never a fact — detectors of this kind run "
            "~80% accuracy in the wild, and can score notably lower on images from "
            "generators newer than their training data."
        ),
    )


# --------------------------------------------------------------------------------
# Fusion — transparent weighted panel + direct-evidence floor (not a learned meta-model)
# --------------------------------------------------------------------------------
def fuse_signals(signals: list[ForensicSignal]) -> ForensicsBlock:
    """Combine the panel with fixed, readable rules.

    First compute the renormalized weighted panel score. Then preserve the strongest
    *direct* AI-generation evidence as a floor: the ML classifier's own probability,
    or 1.0 when metadata explicitly names an AI generator. Quiet ELA/FFT results are
    not proof of authenticity and therefore cannot suppress that direct evidence.

    fused = max(weighted_panel, ml_probability, explicit_generator_tag)

    This remains auditable by hand and does not turn the result into a fact: the
    reporting gate still requires deterministic corroboration outside a probabilistic
    classifier.
    """
    available = [s for s in signals if s.available]
    total_weight = sum(FUSION_WEIGHTS.get(s.name, 0.0) for s in available)
    if not available or total_weight == 0:
        weighted_panel = None
    else:
        weighted_panel = round(
            sum(FUSION_WEIGHTS.get(s.name, 0.0) * s.score for s in available) / total_weight,
            4,
        )

    direct_floors = [
        s.score
        for s in available
        if s.name == "ml_classifier" or metadata_names_ai_tool(s)
    ]
    candidates = ([weighted_panel] if weighted_panel is not None else []) + direct_floors
    fused = round(max(candidates), 4) if candidates else None

    weights_used = ", ".join(
        f"{s.name}×{FUSION_WEIGHTS.get(s.name, 0.0):.2f}" for s in available
    )
    return ForensicsBlock(
        signals=signals,
        fused_score=fused,
        fusion_rule=(
            f"Renormalized weighted panel ({weights_used}); direct AI evidence "
            "(classifier probability or explicit generator tag) is a floor and cannot "
            "be reduced by quiet splice/frequency checks. Fixed rules, no learned fusion."
        ),
    )


def run_panel(image_path: str) -> ForensicsBlock:
    """Run all four signals independently and fuse them. A signal that crashes is
    reported as unavailable rather than sinking the panel — failure of one indicator
    is itself information, not an excuse to show the user a stack trace.
    """
    signals: list[ForensicSignal] = []
    for check in (check_metadata, check_ela, check_fft, check_ml_classifier):
        try:
            signals.append(check(image_path))
        except Exception as exc:
            name = {
                "check_metadata": "metadata",
                "check_ela": "error_level_analysis",
                "check_fft": "fft_frequency_domain",
                "check_ml_classifier": "ml_classifier",
            }[check.__name__]
            signals.append(
                ForensicSignal(
                    name=name,
                    triggered=False,
                    raw_value=0.0,
                    threshold=0.0,
                    score=0.0,
                    available=False,
                    explanation=f"Signal failed to run ({type(exc).__name__}) and was excluded.",
                )
            )
    return fuse_signals(signals)
