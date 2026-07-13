"""Layer 4 — Calibrated Confidence.

The honesty mechanism that makes a probabilistic detector safe to show a voter. A
model's raw score is just a number the classifier happened to output; a *calibrated*
score means what it says — among all files scored around 0.8, roughly 80% actually
turn out to be synthetic. This layer's whole job is closing that gap, and its second
job is to gate the pipeline so forensics alone can never trigger a civic-action filing.

Band boundaries [LOCKED, values pending Week 10 tuning against the labeled corpus]:

    0.00 - 0.30   LEANS_AUTHENTIC
    0.30 - 0.70   ABSTAIN            <- deliberately the WIDEST band. This is the
                                         region where calibration data shows the
                                         detector can't beat a coin flip; "insufficient
                                         evidence" is a legitimate verdict here, not a
                                         failure to produce one.
    0.70 - 0.90   MODERATE_SIGNAL
    0.90 - 1.00   STRONG_SIGNAL

Gate rule [LOCKED]: only STRONG_SIGNAL *corroborated by something deterministic*
(a tampered C2PA hash, a hard metadata contradiction, or a failed disclosure
measurement) may ever nudge the app toward the SB 9 reporting path. An ABSTAIN
contributes nothing, no matter how suspicious a human reviewer feels. This is a
precision-over-recall choice: a false accusation against real media is the worst
failure mode here, because it feeds the "liar's dividend."
"""

from __future__ import annotations

from peachcheck.schema import ConfidenceBand, JudgmentBlock

# Band edges as (upper_bound, band) pairs, checked in order. Kept as data rather than
# nested if/elif so the Week 10 tuning pass is a one-line diff, not a logic rewrite.
_BAND_EDGES: list[tuple[float, ConfidenceBand]] = [
    (0.30, ConfidenceBand.LEANS_AUTHENTIC),
    (0.70, ConfidenceBand.ABSTAIN),
    (0.90, ConfidenceBand.MODERATE_SIGNAL),
    (1.01, ConfidenceBand.STRONG_SIGNAL),  # 1.01, not 1.0, so a score of exactly 1.0 still matches
]


def band_for_score(calibrated_score: float) -> ConfidenceBand:
    """Map a calibrated score in [0, 1] to its confidence band."""
    if not 0.0 <= calibrated_score <= 1.0:
        raise ValueError(f"calibrated_score must be in [0, 1], got {calibrated_score}")
    for upper_bound, band in _BAND_EDGES:
        if calibrated_score < upper_bound:
            return band
    raise AssertionError("unreachable: _BAND_EDGES must cover the full [0, 1] range")


def calibrate(raw_score: float, calibration_version: str = "v0-identity") -> float:
    """Convert a raw classifier score into a calibrated one.

    TODO(week 10): replace the identity mapping below with either Platt scaling or an
    empirical-bins lookup, fit on a held-out slice of the labeled corpus:
        1. bin raw scores into deciles
        2. compute per-bin accuracy (fraction actually synthetic) on held-out data
        3. fit a monotonic mapping raw -> accuracy (Platt scaling, or the bins directly)
    Until that fit exists, this is an identity mapping — explicitly NOT calibrated,
    which is why calibration_version defaults to "v0-identity" rather than a real
    version string. Never report a JudgmentBlock's calibrated_score as trustworthy
    while calibration_version is "v0-identity".
    """
    del calibration_version  # unused until the real fit lands; kept in the signature
    return raw_score


def build_judgment(
    raw_score: float,
    calibration_version: str = "v0-identity",
    rationale: str | None = None,
) -> JudgmentBlock:
    """Run a raw forensics score through calibration and banding.

    `rationale` is a plain-language line about where the raw score came from (which
    signals fired, with what weights) — written by the caller, because only the
    caller knows the fusion context. It rides along so the UI never reconstructs it.
    """
    calibrated = calibrate(raw_score, calibration_version)
    return JudgmentBlock(
        raw_score=raw_score,
        calibrated_score=calibrated,
        band=band_for_score(calibrated),
        calibration_version=calibration_version,
        rationale=rationale,
    )


def gate_allows_reporting(judgment: JudgmentBlock, has_deterministic_corroboration: bool) -> bool:
    """The gate between the judgment layer and civic action.

    `has_deterministic_corroboration` must come from outside this layer — a tampered
    C2PA hash (provenance.py), a hard metadata contradiction (forensics.py), or a
    failed disclosure measurement (measurement.py). Forensics scores alone, no matter
    how high, never satisfy this on their own; that's the whole point of the gate.
    """
    return judgment.band == ConfidenceBand.STRONG_SIGNAL and has_deterministic_corroboration
