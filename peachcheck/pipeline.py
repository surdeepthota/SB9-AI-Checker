"""Orchestrator: runs the five layers in the LOCKED order and assembles a TrustReport.

    provenance -> (early exit | measurement | forensics -> judgment) -> action

This module owns the *routing* between layers — which layers run at all for a given
file — not the logic inside any one layer. Each branch below cites the section of the
project context it implements, so the control flow can be checked against the design
doc line by line.
"""

from __future__ import annotations

import hashlib

from peachcheck.layers import action, provenance
from peachcheck.schema import C2PAState, FileIdentity, TrustReport


def _sha256_of_file(file_path: str) -> str:
    """Real, working hash computation — no stub needed here, unlike the model-backed
    layers, since hashlib has no external dependency.
    """
    digest = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_identity(file_path: str, mime_type: str, analyzed_at_iso: str) -> FileIdentity:
    """Layer-0 bookkeeping: every report needs a stable identity before any layer runs.

    perceptual_hash is left None here — it needs an image/video-specific perceptual
    hashing library (e.g. imagehash) that isn't wired up yet; see FileIdentity's
    docstring in schema.py for why it matters (duplicate detection across re-encodes).
    """
    return FileIdentity(
        filename=file_path.rsplit("/", 1)[-1],
        mime_type=mime_type,
        sha256=_sha256_of_file(file_path),
        analyzed_at=analyzed_at_iso,
    )


def run_pipeline(file_path: str, mime_type: str, analyzed_at_iso: str) -> TrustReport:
    """Run layer 1 for real, then route to whichever later layers the four-state
    table (provenance.py) says apply.

    Layers 2 and 3 need real inputs this scaffold doesn't produce yet — OCR'd frames
    for measurement, extracted image data for forensics. Those calls are marked with
    TODOs below rather than faked, so nobody mistakes a placeholder for a real result.
    """
    report = TrustReport(identity=build_identity(file_path, mime_type, analyzed_at_iso))

    report.provenance = provenance.verify_provenance(file_path)

    if report.provenance.state == C2PAState.VALID_CAPTURE:
        # Verified camera capture: early exit, per section 5.1's routing table.
        # No forensics, no judgment, no action — the report is already complete.
        return report

    if report.provenance.state == C2PAState.TAMPERED:
        # Highest-signal state: skip straight to the evidence packet. No forensics or
        # judgment layer needed — the tampered hash itself is the deterministic
        # corroboration the layer-4 gate would otherwise require.
        report.action = action.build_action_block(
            analysis_date_iso=analyzed_at_iso[:10],
            next_election_date_iso=_TODO_next_election_date(),
            exemption_answers=_TODO_exemption_answers(),
            publisher=_TODO_publisher(),
            gate_passed=True,
        )
        return report

    if report.provenance.state == C2PAState.VALID_AI_ASSERTED:
        # TODO(week 2): call layers.measurement.run_measurement() with real OCR'd
        # bounding boxes / contrast samples / audio LUFS+WPM extracted from file_path.
        # report.measurement = measurement.run_measurement([...])
        return report

    # UNTRUSTED: no usable manifest -> forensics panel, then judgment.
    # TODO(week 3): call layers.forensics.check_metadata / check_ela / check_fft /
    # check_ml_classifier on file_path, fuse with fuse_signals(), then feed the
    # classifier's raw score into judgment.build_judgment().
    # report.forensics = forensics.fuse_signals([...])
    # report.judgment = judgment.build_judgment(raw_score=...)
    # if report.judgment is not None:
    #     gate_passed = judgment.gate_allows_reporting(
    #         report.judgment, has_deterministic_corroboration=...
    #     )
    #     report.action = action.build_action_block(..., gate_passed=gate_passed)
    return report


def _TODO_next_election_date() -> str:
    """Placeholder until the Georgia election-calendar lookup is wired in."""
    raise NotImplementedError("Wire up the Georgia election calendar lookup.")


def _TODO_exemption_answers() -> dict[str, bool]:
    """Placeholder until the guided exemption questionnaire (UI) feeds real answers."""
    raise NotImplementedError("Wire up the exemption questionnaire UI.")


def _TODO_publisher() -> str | None:
    """Placeholder until the packet UI captures who published the media."""
    raise NotImplementedError("Wire up the publisher-capture UI field.")
