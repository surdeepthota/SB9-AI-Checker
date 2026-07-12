"""Trust-report schema (v0) — the single contract every pipeline layer writes into.

Design rule: the UI only ever *reads* this structure; it never re-derives a verdict.
That means every field here has to be something a layer can state plainly, with the
evidence to back it up, rather than a bare score. See TrustReport for the assembled
report and the per-layer blocks below it.

Nothing in this module talks to a model or a file on disk — it is pure data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


SCHEMA_VERSION = "0.1.0"


class C2PAState(Enum):
    """The four routing states from the provenance gate (layer 1).

    Ordered roughly by how much the app is willing to trust them, not alphabetically —
    see layers/provenance.py for the routing logic that consumes this enum.
    """

    VALID_CAPTURE = "valid_capture"        # Signed manifest, camera origin -> early exit, no ML runs.
    VALID_AI_ASSERTED = "valid_ai_asserted"  # Signed manifest, digitalSourceType=trainedAlgorithmicMedia.
    TAMPERED = "tampered"                  # Signature/hash check failed post-signing -> highest signal.
    UNTRUSTED = "untrusted"                # No manifest or unverifiable -> "unknown provenance", never "fake".


class ConfidenceBand(Enum):
    """Calibrated-confidence bands from the judgment layer (layer 4).

    Boundaries are provisional ("pending Week 10 tuning" per the design doc) and live
    in judgment.py, not here — this enum is just the vocabulary the report speaks.
    """

    LEANS_AUTHENTIC = "leans_authentic"
    ABSTAIN = "abstain"                # Deliberately the widest band. "No verdict" is a legitimate output.
    MODERATE_SIGNAL = "moderate_signal"
    STRONG_SIGNAL = "strong_signal"


@dataclass
class FileIdentity:
    """Identity block: what file was analyzed and when.

    Both hashes are kept because they answer different questions: SHA-256 proves this
    exact byte sequence was seen before; the perceptual hash still matches after a
    re-encode (e.g. a screenshot or a re-compressed re-upload), which is what the
    community-page duplicate-detection feature in action.py relies on.
    """

    filename: str
    mime_type: str
    sha256: str
    perceptual_hash: Optional[str] = None
    analyzed_at: Optional[str] = None  # ISO-8601 timestamp; set by the caller, not this module.
    schema_version: str = SCHEMA_VERSION


@dataclass
class ProvenanceBlock:
    """Output of layer 1 (provenance.py). Deterministic — no model inference happens here."""

    state: C2PAState
    signer: Optional[str] = None
    trust_list_result: Optional[bool] = None
    assertions: list[str] = field(default_factory=list)  # e.g. ["digitalSourceType:trainedAlgorithmicMedia"]
    failed_assertion: Optional[str] = None  # populated only when state is TAMPERED


@dataclass
class MeasurementResult:
    """One SB 9 §21-5-92 disclosure threshold check, e.g. the 30%-text-height rule."""

    name: str
    measured_value: float
    required_bar: float
    passed: bool
    evidence_ref: Optional[str] = None  # e.g. path to an annotated frame with the bounding box drawn


@dataclass
class MeasurementBlock:
    """Output of layer 2 (measurement.py). Deterministic — OCR + geometry, no ML judgment."""

    checks: list[MeasurementResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(check.passed for check in self.checks)


@dataclass
class ForensicSignal:
    """One indicator from the forensics panel (layer 3). See layers/forensics.py for
    what each signal actually measures — this is deliberately generic so the four
    signal types (metadata / ELA / FFT / classifier) can share one shape.
    """

    name: str
    triggered: bool
    raw_value: float
    threshold: float
    explanation: str  # one line, written for a non-technical reader per the report-language rules


@dataclass
class ForensicsBlock:
    """Output of layer 3. Only ever populated when provenance is UNTRUSTED — see
    pipeline.py for the early-exit logic that skips this layer otherwise.
    """

    signals: list[ForensicSignal] = field(default_factory=list)

    @property
    def triggered_count(self) -> int:
        return sum(1 for s in self.signals if s.triggered)


@dataclass
class JudgmentBlock:
    """Output of layer 4 (judgment.py): the calibrated-confidence honesty mechanism.

    raw_score is whatever the forensics classifier produced; calibrated_score is that
    number after Platt scaling / empirical-bin correction, so it means what it says
    (see judgment.py's module docstring for the calibration definition).
    """

    raw_score: Optional[float] = None
    calibrated_score: Optional[float] = None
    band: Optional[ConfidenceBand] = None
    calibration_version: Optional[str] = None


@dataclass
class ActionBlock:
    """Output of layer 5 (action.py): whether this report is eligible for an SB 9
    evidence packet, and the inputs a packet would need if so.
    """

    within_90_day_window: Optional[bool] = None
    exemption_answers: dict[str, bool] = field(default_factory=dict)  # satire/parody/art/journalism
    publisher: Optional[str] = None
    packet_eligible: bool = False


@dataclass
class TrustReport:
    """The assembled, cross-layer report. This is the only object the UI reads."""

    identity: FileIdentity
    provenance: Optional[ProvenanceBlock] = None
    measurement: Optional[MeasurementBlock] = None
    forensics: Optional[ForensicsBlock] = None
    judgment: Optional[JudgmentBlock] = None
    action: Optional[ActionBlock] = None
