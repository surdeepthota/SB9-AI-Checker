"""Layer 3: the metadata rules, the team-written ELA and FFT signals on synthetic
images with known properties, and the transparent fusion arithmetic."""

from PIL import Image

from peachcheck.layers.forensics import (
    FUSION_WEIGHTS,
    check_ela,
    check_fft,
    check_metadata,
    check_ml_classifier,
    evaluate_metadata,
    fuse_signals,
    metadata_names_ai_tool,
    run_panel,
)
from peachcheck.schema import ForensicSignal


# ---- signal 1: metadata ----
def test_camera_metadata_does_not_trigger():
    signal = evaluate_metadata({"Make": "NIKON", "Model": "Z6", "GPSInfo": "..."})
    assert not signal.triggered
    assert signal.score == 0.0


def test_missing_metadata_is_a_weak_signal():
    signal = evaluate_metadata({})
    assert signal.triggered
    assert signal.score == 0.6  # soft: re-encoding also strips metadata
    assert "weak" in signal.explanation.lower()


def test_ai_tool_tag_is_a_hard_signal():
    signal = evaluate_metadata({"Software": "Midjourney v6"})
    assert signal.triggered
    assert signal.score == 1.0
    assert metadata_names_ai_tool(signal)


def test_png_text_chunk_tag_is_found(tmp_path):
    from PIL import PngImagePlugin

    path = tmp_path / "sd.png"
    meta = PngImagePlugin.PngInfo()
    meta.add_text("parameters", "Model: Stable Diffusion XL")
    Image.new("RGB", (32, 32)).save(path, "PNG", pnginfo=meta)
    signal = check_metadata(str(path))
    assert metadata_names_ai_tool(signal)


# ---- signal 2: ELA ----
def test_ela_uniform_image_scores_low(tiny_jpeg):
    signal = check_ela(tiny_jpeg)
    assert not signal.triggered
    assert signal.evidence_ref.startswith("data:image/png;base64,")


def test_ela_spliced_image_scores_higher_than_uniform(tmp_path, tiny_jpeg):
    import numpy as np

    rng_free_noise = Image.effect_noise((64, 64), 60).convert("RGB")
    base = Image.open(tiny_jpeg).convert("RGB")
    base.paste(rng_free_noise.crop((0, 0, 32, 32)), (16, 16))
    spliced_path = tmp_path / "spliced.jpg"
    base.save(spliced_path, "JPEG", quality=95)

    uniform = check_ela(tiny_jpeg)
    spliced = check_ela(str(spliced_path))
    assert spliced.raw_value > uniform.raw_value


# ---- signal 3: FFT ----
def test_fft_noise_has_more_high_freq_energy_than_flat(tmp_path, tiny_jpeg):
    noisy_path = tmp_path / "noisy.png"
    Image.effect_noise((64, 64), 80).convert("RGB").save(noisy_path, "PNG")
    flat = check_fft(tiny_jpeg)
    noisy = check_fft(str(noisy_path))
    assert noisy.raw_value > flat.raw_value
    assert noisy.evidence_ref.startswith("data:image/png;base64,")


# ---- signal 4: classifier degradation (model disabled by conftest) ----
def test_classifier_unavailable_degrades_honestly(tiny_jpeg):
    signal = check_ml_classifier(tiny_jpeg)
    assert not signal.available
    assert not signal.triggered
    assert "unavailable" in signal.explanation.lower()


# ---- fusion ----
def _signal(name, score, available=True):
    return ForensicSignal(
        name=name, triggered=score > 0.5, raw_value=score, threshold=0.5,
        score=score, available=available, explanation="test",
    )


def test_direct_classifier_evidence_is_not_averaged_away():
    signals = [
        _signal("metadata", 1.0),
        _signal("error_level_analysis", 0.5),
        _signal("fft_frequency_domain", 0.0),
        _signal("ml_classifier", 0.8),
    ]
    block = fuse_signals(signals)
    # Both the classifier (0.8) and explicit AI-tool metadata (1.0) are direct
    # evidence floors; quiet indirect signals cannot dilute either one.
    assert block.fused_score == 1.0


def test_strong_classifier_survives_quiet_splice_and_fft_checks():
    signals = [
        _signal("metadata", 0.6),
        _signal("error_level_analysis", 0.008),
        _signal("fft_frequency_domain", 0.113),
        _signal("ml_classifier", 0.92),
    ]
    block = fuse_signals(signals)
    assert block.fused_score == 0.92


def test_fusion_renormalizes_when_classifier_unavailable():
    signals = [
        _signal("metadata", 1.0),
        _signal("error_level_analysis", 1.0),
        _signal("fft_frequency_domain", 1.0),
        _signal("ml_classifier", 0.0, available=False),
    ]
    block = fuse_signals(signals)
    # all available signals maxed -> fused must be 1.0, not dragged down by the
    # missing signal's zero
    assert block.fused_score == 1.0
    assert block.available_count == 3


def test_fusion_weights_sum_to_one():
    assert abs(sum(FUSION_WEIGHTS.values()) - 1.0) < 1e-9


def test_run_panel_never_raises_on_odd_input(tmp_path):
    # A text file with a .jpg name: every signal should degrade, none should raise.
    bad = tmp_path / "not_an_image.jpg"
    bad.write_text("hello")
    block = run_panel(str(bad))
    assert len(block.signals) == 4
