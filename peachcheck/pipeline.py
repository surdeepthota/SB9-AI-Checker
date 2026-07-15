"""Orchestrator: runs the five layers in the LOCKED order and assembles a TrustReport.

    provenance -> (early exit | measurement | forensics -> judgment) -> action

This module owns the *routing* between layers — which layers run at all for a given
file — not the logic inside any one layer. Each branch below cites the section of the
project context it implements, so the control flow can be checked against the design
doc line by line. It also owns the report's headline, because the report-language
rules (never "fake", indicator counts + evidence, abstention as a first-class verdict)
must live in one audited place.
"""

from __future__ import annotations

import hashlib

from peachcheck.layers import action, forensics, judgment, measurement, provenance
from peachcheck.schema import (
    C2PAState,
    ConfidenceBand,
    FileIdentity,
    RouteStep,
    TrustReport,
)


def _sha256_of_file(file_path: str) -> str:
    digest = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_dhash(file_path: str) -> str | None:
    """Team-written perceptual hash (difference hash).

    Resize to 9x8 grayscale, compare each pixel to its right neighbor -> 64 bits.
    Unlike SHA-256, this survives re-encoding: a screenshot or re-compressed copy of
    the same picture lands within a few bits of the original, which is what the
    community-page duplicate detection needs. Returns None for non-image files.
    """
    try:
        import numpy as np
        from PIL import Image

        with Image.open(file_path) as img:
            small = img.convert("L").resize((9, 8), Image.LANCZOS)
        grid = np.asarray(small, dtype=np.int16)  # 8 rows x 9 cols
        bits = 0
        for row in range(8):
            for col in range(8):
                bits = (bits << 1) | (1 if grid[row, col] > grid[row, col + 1] else 0)
        return f"{bits:016x}"
    except Exception:
        return None


def build_identity(file_path: str, mime_type: str, analyzed_at_iso: str) -> FileIdentity:
    """Layer-0 bookkeeping: every report needs a stable identity before any layer runs."""
    return FileIdentity(
        filename=file_path.rsplit("/", 1)[-1],
        mime_type=mime_type,
        sha256=_sha256_of_file(file_path),
        perceptual_hash=compute_dhash(file_path),
        analyzed_at=analyzed_at_iso,
    )


def _band_phrase(band: ConfidenceBand | None) -> str:
    """Plain-language wording for each confidence band."""
    return {
        ConfidenceBand.LEANS_AUTHENTIC: "the checks lean toward a normal camera image",
        ConfidenceBand.ABSTAIN: "there is not enough evidence",
        ConfidenceBand.MODERATE_SIGNAL: "the checks found some signs of AI or editing",
        ConfidenceBand.STRONG_SIGNAL: "the checks found strong signs of AI or editing",
    }.get(band, "there is not enough evidence")


def _headline(report: TrustReport) -> str:
    """The one-line summary at the top of every report, under the cardinal output
    rule [LOCKED]: the app never says "fake."
    """
    prov = report.provenance
    if prov is None:
        return "Analysis incomplete — no provenance result."

    if prov.state == C2PAState.VALID_CAPTURE:
        signer = prov.signer or "an unidentified signer"
        return (
            f"The source record is valid and was signed by {signer}. It does not say AI was used, so no image guessing was needed."
        )

    if prov.state == C2PAState.TAMPERED:
        return (
            "This file changed after it was signed. Its trusted source record no longer matches the file."
        )

    if prov.state == C2PAState.VALID_AI_ASSERTED:
        if report.measurement and report.measurement.checks:
            passed = sum(1 for c in report.measurement.checks if c.passed)
            total = len(report.measurement.checks)
            return (
                "The file's own signed record says AI was used. "
                f"Its warning passed {passed} of {total} checks."
            )
        return (
            "The file's own signed record says AI was used, but PeachCheck could not finish checking its warning."
        )

    # UNTRUSTED — the canonical phrasing from the design doc.
    if report.forensics is not None:
        n = report.forensics.triggered_count
        m = report.forensics.available_count
        band = report.judgment.band if report.judgment else None
        classifier = next(
            (
                signal
                for signal in report.forensics.signals
                if signal.name == "ml_classifier" and signal.available
            ),
            None,
        )
        if classifier is not None and band in (
            ConfidenceBand.MODERATE_SIGNAL,
            ConfidenceBand.STRONG_SIGNAL,
        ):
            band_phrase = _band_phrase(band)
            return (
                f"The AI image checker gave this file {classifier.score:.0%}. "
                f"{band_phrase[0].upper() + band_phrase[1:]}. This is a clue, not proof. "
                f"{n} of {m} checks found something unusual."
            )
        return (
            f"The source is unknown. {n} of {m} checks found something unusual, and {_band_phrase(band)}."
        )
    return "The source is unknown. PeachCheck could not run the image checks."


def run_pipeline(
    file_path: str,
    mime_type: str,
    analyzed_at_iso: str,
    is_campaign_ad: bool = False,
) -> TrustReport:
    """Run layer 1 for real, then route to whichever later layers the four-state
    table (provenance.py) says apply.

    `is_campaign_ad` is the user's own assertion that this media is a campaign ad —
    it additionally routes UNTRUSTED files through disclosure measurement (§21-5-91
    reaches user-asserted campaign ads, not just files whose manifest confesses).
    """
    report = TrustReport(identity=build_identity(file_path, mime_type, analyzed_at_iso))
    analysis_date = analyzed_at_iso[:10]

    report.provenance = provenance.verify_provenance(file_path)
    report.route.append(
        RouteStep(
            layer="provenance",
            ran=True,
            reason=f"Always runs first; result: {report.provenance.state.value}.",
        )
    )

    if report.provenance.state == C2PAState.VALID_CAPTURE:
        # Verified capture: early exit, per section 5.1's routing table.
        # No forensics, no judgment, no action — the report is already complete.
        for layer, why in (
            ("measurement", "Skipped — no AI assertion, so SB 9 disclosure rules don't attach."),
            ("forensics", "Skipped — provenance is verified; no ML runs on this file."),
            ("judgment", "Skipped — nothing probabilistic to calibrate."),
            ("action", "Skipped — no finding to act on."),
        ):
            report.route.append(RouteStep(layer=layer, ran=False, reason=why))
        report.headline = _headline(report)
        return report

    if report.provenance.state == C2PAState.TAMPERED:
        # Highest-signal state: skip straight to the evidence packet. No forensics or
        # judgment layer needed — the tampered hash itself is the deterministic
        # corroboration the layer-4 gate would otherwise require.
        report.route.append(
            RouteStep(layer="measurement", ran=False, reason="Skipped — tampered manifest routes straight to civic action.")
        )
        report.route.append(
            RouteStep(layer="forensics", ran=False, reason="Skipped — the broken hash is already deterministic evidence; ML adds nothing.")
        )
        report.route.append(
            RouteStep(layer="judgment", ran=False, reason="Skipped — no probabilistic score to calibrate.")
        )
        report.action = action.build_action_block(
            analysis_date_iso=analysis_date,
            gate_passed=True,
            deterministic_corroboration=["tampered_c2pa_hash"],
        )
        report.route.append(
            RouteStep(layer="action", ran=True, reason="Tampered provenance qualifies for the reporting path by itself.")
        )
        report.headline = _headline(report)
        return report

    if report.provenance.state == C2PAState.VALID_AI_ASSERTED:
        # The §21-5-91 compliance question: the file admits it's AI-generated media,
        # so measure its disclosure against the statute's format thresholds.
        report.measurement = measurement.measure_still_image(file_path)
        report.route.append(
            RouteStep(layer="measurement", ran=True, reason="Signed AI assertion triggers SB 9 disclosure measurement.")
        )
        report.route.append(
            RouteStep(layer="forensics", ran=False, reason="Skipped — the file's own manifest already answers the generation question.")
        )
        report.route.append(
            RouteStep(layer="judgment", ran=False, reason="Skipped — disclosure measurement is deterministic; there is no score to calibrate.")
        )

        # A failed disclosure measurement on self-declared AI media is a deterministic
        # compliance finding under the civil regime (§§21-5-91/92) — both facts come
        # from measurement, not ML, so the reporting path can open on them.
        corroboration = ["signed_ai_assertion"]
        failed = [c.name for c in report.measurement.checks if not c.passed]
        gate_passed = bool(failed)
        if failed:
            corroboration.append("failed_disclosure_measurement:" + ",".join(failed))
        report.action = action.build_action_block(
            analysis_date_iso=analysis_date,
            gate_passed=gate_passed,
            deterministic_corroboration=corroboration if gate_passed else [],
        )
        report.route.append(
            RouteStep(
                layer="action",
                ran=True,
                reason=(
                    "Disclosure shortfalls are deterministic findings; statutory context computed."
                    if gate_passed
                    else "Disclosure checks passed — nothing to act on, context computed for completeness."
                ),
            )
        )
        report.headline = _headline(report)
        return report

    # UNTRUSTED: no usable manifest -> forensics panel, then judgment.
    report.forensics = forensics.run_panel(file_path)
    report.route.append(
        RouteStep(layer="forensics", ran=True, reason='No verifiable provenance ("unknown provenance") routes to the forensic panel.')
    )

    if is_campaign_ad:
        report.measurement = measurement.measure_still_image(file_path)
        report.route.append(
            RouteStep(layer="measurement", ran=True, reason="User asserted this is a campaign ad, so disclosure measurement applies.")
        )
    else:
        report.route.append(
            RouteStep(layer="measurement", ran=False, reason="Skipped — no AI assertion and not asserted to be a campaign ad.")
        )

    fused = report.forensics.fused_score
    if fused is not None:
        triggered = [s.name for s in report.forensics.signals if s.available and s.triggered]
        rationale = (
            f"Fused score {fused:.2f} from {report.forensics.available_count} signals "
            f"({report.forensics.fusion_rule}) "
            + (f"Triggered: {', '.join(triggered)}." if triggered else "No signals triggered.")
        )
        report.judgment = judgment.build_judgment(raw_score=fused, rationale=rationale)
        report.route.append(
            RouteStep(layer="judgment", ran=True, reason="Probabilistic panel output requires calibration and banding.")
        )
    else:
        report.route.append(
            RouteStep(layer="judgment", ran=False, reason="Skipped — no forensic signal produced a usable score.")
        )

    # Deterministic corroboration available on this route: an explicit AI-tool tag in
    # metadata (hard, self-declared) or a failed disclosure measurement (if it ran).
    corroboration: list[str] = []
    for signal in report.forensics.signals:
        if forensics.metadata_names_ai_tool(signal):
            corroboration.append("metadata_names_ai_tool")
    if report.measurement is not None:
        failed = [c.name for c in report.measurement.checks if not c.passed]
        if failed:
            corroboration.append("failed_disclosure_measurement:" + ",".join(failed))

    gate_passed = (
        judgment.gate_allows_reporting(report.judgment, bool(corroboration))
        if report.judgment is not None
        else False
    )
    report.action = action.build_action_block(
        analysis_date_iso=analysis_date,
        gate_passed=gate_passed,
        deterministic_corroboration=corroboration if gate_passed else [],
    )
    report.route.append(
        RouteStep(
            layer="action",
            ran=True,
            reason=(
                "Strong corroborated signal opened the reporting path; statutory context computed."
                if gate_passed
                else "Reporting gate closed (forensics alone never files); statutory context computed for transparency."
            ),
        )
    )
    report.headline = _headline(report)
    return report
