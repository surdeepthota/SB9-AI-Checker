"""Trust-report schema — the single contract every pipeline layer writes into.

Design rule: the UI only ever *reads* this structure; it never re-derives a verdict.
That means every field here has to be something a layer can state plainly, with the
evidence to back it up, rather than a bare score. See TrustReport for the assembled
report and the per-layer blocks below it.

Nothing in this module talks to a model or a file on disk — it is pure data.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


SCHEMA_VERSION = "0.2.0"


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
    perceptual_hash: Optional[str] = None  # team-written dHash; see pipeline.compute_dhash
    analyzed_at: Optional[str] = None  # ISO-8601 timestamp; set by the caller, not this module.
    schema_version: str = SCHEMA_VERSION


@dataclass
class ProvenanceBlock:
    """Output of layer 1 (provenance.py). Deterministic — no model inference happens here."""

    state: C2PAState
    signer: Optional[str] = None
    claim_generator: Optional[str] = None  # the tool that wrote the manifest, per its own claim
    trust_list_result: Optional[bool] = None  # True only if the cert chains to the C2PA trust list
    assertions: list[str] = field(default_factory=list)  # assertion labels, e.g. "c2pa.actions.v2"
    digital_source_type: Optional[str] = None  # e.g. "trainedAlgorithmicMedia"
    failed_assertion: Optional[str] = None  # populated only when state is TAMPERED
    explanation: Optional[str] = None  # one plain-language line for the report reader


@dataclass
class MeasurementResult:
    """One SB 9 §21-5-92 disclosure threshold check, e.g. the 30%-text-height rule."""

    name: str
    measured_value: float
    required_bar: float
    passed: bool
    detail: Optional[str] = None  # plain-language reading of the number
    evidence_ref: Optional[str] = None  # data-URI of an annotated frame with the bounding box drawn


@dataclass
class MeasurementBlock:
    """Output of layer 2 (measurement.py). Deterministic — OCR + geometry, no ML judgment."""

    checks: list[MeasurementResult] = field(default_factory=list)
    disclosure_text: Optional[str] = None  # the OCR'd disclosure line the checks were run against
    note: Optional[str] = None  # e.g. "OCR engine unavailable" or "duration check N/A for stills"

    @property
    def all_passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def any_failed(self) -> bool:
        return any(not check.passed for check in self.checks)


@dataclass
class ForensicSignal:
    """One indicator from the forensics panel (layer 3). See layers/forensics.py for
    what each signal actually measures — this is deliberately generic so the four
    signal types (metadata / ELA / FFT / classifier) can share one shape.

    `score` is the signal's own suspicion contribution normalized to [0, 1]; the
    fusion rule in forensics.fuse_signals combines these with fixed, readable weights.
    `raw_value` keeps the underlying measurement (mean error, energy ratio, model
    probability) so a reader can re-check the arithmetic.
    """

    name: str
    triggered: bool
    raw_value: float
    threshold: float
    explanation: str  # one line, written for a non-technical reader per the report-language rules
    score: float = 0.0  # normalized suspicion in [0, 1]
    available: bool = True  # False when the signal could not run (e.g. model not installed)
    evidence_ref: Optional[str] = None  # data-URI visual (ELA heatmap, FFT spectrum)


@dataclass
class ForensicsBlock:
    """Output of layer 3. Only ever populated when provenance is UNTRUSTED — see
    pipeline.py for the early-exit logic that skips this layer otherwise.
    """

    signals: list[ForensicSignal] = field(default_factory=list)
    fused_score: Optional[float] = None  # rules-based fusion, see forensics.fuse_signals
    fusion_rule: Optional[str] = None  # human-readable statement of the exact weights used

    @property
    def triggered_count(self) -> int:
        return sum(1 for s in self.signals if s.available and s.triggered)

    @property
    def available_count(self) -> int:
        return sum(1 for s in self.signals if s.available)


@dataclass
class JudgmentBlock:
    """Output of layer 4 (judgment.py): the calibrated-confidence honesty mechanism.

    raw_score is whatever the forensics fusion produced; calibrated_score is that
    number after Platt scaling / empirical-bin correction, so it means what it says
    (see judgment.py's module docstring for the calibration definition).
    """

    raw_score: Optional[float] = None
    calibrated_score: Optional[float] = None
    band: Optional[ConfidenceBand] = None
    calibration_version: Optional[str] = None
    rationale: Optional[str] = None  # which signals drove the score, in plain language


@dataclass
class ActionBlock:
    """Output of layer 5 (action.py): whether this report could move toward an SB 9
    evidence packet, and the statutory context a filer would need.

    The exemption questionnaire and publisher field are filled by the /packet flow,
    *after* analysis — a user answers them, the pipeline never invents them. Until
    then they stay None/empty and packet_eligible stays False.
    """

    within_90_day_window: Optional[bool] = None
    next_election_date: Optional[str] = None
    next_election_name: Optional[str] = None
    window_opens: Optional[str] = None  # date the 90-day window opens, if not yet open
    days_until_election: Optional[int] = None
    deterministic_corroboration: list[str] = field(default_factory=list)  # e.g. ["tampered_c2pa_hash"]
    gate_passed: bool = False  # judgment.gate_allows_reporting result (or auto-True for TAMPERED)
    exemption_answers: dict[str, bool] = field(default_factory=dict)  # satire/parody/art/journalism
    publisher: Optional[str] = None
    packet_eligible: bool = False
    guidance: Optional[str] = None  # plain-language next step for the reader


@dataclass
class RouteStep:
    """One entry in the pipeline's routing log: which layer ran (or was skipped) and why.

    This exists so the UI can show the layered-trust story — "forensics never ran
    because the capture was verified" is itself a finding worth displaying.
    """

    layer: str  # "provenance" | "measurement" | "forensics" | "judgment" | "action"
    ran: bool
    reason: str


@dataclass
class TrustReport:
    """The assembled, cross-layer report. This is the only object the UI reads.

    `headline` is generated by pipeline.py under the report-language rules (section 7
    of the design doc): never "fake", indicator counts + evidence, abstention as a
    first-class verdict. Centralizing it server-side keeps the language rules in one
    audited place instead of scattered across UI components.
    """

    identity: FileIdentity
    provenance: Optional[ProvenanceBlock] = None
    measurement: Optional[MeasurementBlock] = None
    forensics: Optional[ForensicsBlock] = None
    judgment: Optional[JudgmentBlock] = None
    action: Optional[ActionBlock] = None
    route: list[RouteStep] = field(default_factory=list)
    headline: Optional[str] = None


def _to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses/enums into plain JSON-safe structures."""
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def report_to_dict(report: TrustReport) -> dict:
    """Serialize a TrustReport to the exact JSON shape the UI and evidence packet use.

    dataclasses.asdict already recurses, but leaves Enum members intact — this wrapper
    exists to flatten those to their .value strings so the wire format is stable.
    """
    return _to_jsonable(report)
