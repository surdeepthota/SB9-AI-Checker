"""Layer 4: band edges, the abstain region, and the reporting gate."""

import pytest

from peachcheck.layers.judgment import band_for_score, build_judgment, gate_allows_reporting
from peachcheck.schema import ConfidenceBand


@pytest.mark.parametrize(
    "score,band",
    [
        (0.0, ConfidenceBand.LEANS_AUTHENTIC),
        (0.29, ConfidenceBand.LEANS_AUTHENTIC),
        (0.30, ConfidenceBand.ABSTAIN),
        (0.50, ConfidenceBand.ABSTAIN),
        (0.69, ConfidenceBand.ABSTAIN),
        (0.70, ConfidenceBand.MODERATE_SIGNAL),
        (0.89, ConfidenceBand.MODERATE_SIGNAL),
        (0.90, ConfidenceBand.STRONG_SIGNAL),
        (1.0, ConfidenceBand.STRONG_SIGNAL),
    ],
)
def test_band_edges(score, band):
    assert band_for_score(score) == band


def test_abstain_is_the_widest_band():
    widths = {
        ConfidenceBand.LEANS_AUTHENTIC: 0.30,
        ConfidenceBand.ABSTAIN: 0.40,
        ConfidenceBand.MODERATE_SIGNAL: 0.20,
        ConfidenceBand.STRONG_SIGNAL: 0.10,
    }
    assert max(widths, key=widths.get) == ConfidenceBand.ABSTAIN


def test_out_of_range_scores_rejected():
    with pytest.raises(ValueError):
        band_for_score(1.5)
    with pytest.raises(ValueError):
        band_for_score(-0.1)


def test_identity_calibration_is_labeled_uncalibrated():
    judgment = build_judgment(raw_score=0.8)
    assert judgment.calibration_version == "v0-identity"
    assert judgment.calibrated_score == judgment.raw_score


def test_gate_requires_strong_band_AND_deterministic_corroboration():
    strong = build_judgment(raw_score=0.95)
    moderate = build_judgment(raw_score=0.8)
    abstain = build_judgment(raw_score=0.5)

    assert gate_allows_reporting(strong, has_deterministic_corroboration=True)
    # Strong alone is not enough — forensics never files by itself.
    assert not gate_allows_reporting(strong, has_deterministic_corroboration=False)
    # Corroboration alone is not enough either without the strong band.
    assert not gate_allows_reporting(moderate, has_deterministic_corroboration=True)
    # An abstain contributes nothing, no matter what.
    assert not gate_allows_reporting(abstain, has_deterministic_corroboration=True)
