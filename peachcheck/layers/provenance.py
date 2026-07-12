"""Layer 1 — Provenance Gate.

Not an AI model. This layer is a C2PA *validator*: it reads a signed manifest that a
creation tool (camera, editor, or generator) embedded in the file, checks the
cryptographic signature against the C2PA trust list, and recomputes content hashes to
confirm nothing changed after signing. It answers "what does this file's own signed
history say happened to it?" — never "does this look fake?".

Library: c2pa-python (backend) reads the JUMBF container embedded in the file and
verifies the COSE signature. Kept as an optional import (see _read_manifest) so the
rest of this module — most importantly `route()`, the actual decision logic — can be
read, tested, and reasoned about without the dependency installed.

Four-state routing table [LOCKED — see project context, section 5.1]:

    state              meaning                                   -> next step
    -----------------  ----------------------------------------- ------------------
    VALID_CAPTURE      signed, camera origin                      early exit, no ML
    VALID_AI_ASSERTED  signed, digitalSourceType=trainedAlgorithmicMedia
                                                                   -> measurement layer
    TAMPERED           signature or hash check failed post-signing -> straight to
                                                                      evidence packet
    UNTRUSTED          no manifest / can't verify                 -> forensics panel,
                                                                      labeled "unknown
                                                                      provenance"

Honest caveat (goes in the UI, not just here): C2PA confirms manifest *integrity*, not
truthfulness, and messaging apps strip manifests on re-encode. So UNTRUSTED must never
be reported as "fake" — it means "nothing to check," not "something to hide."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from peachcheck.schema import C2PAState, ProvenanceBlock

try:
    # Real dependency for Week 1: `pip install c2pa-python`. Not required to import
    # this module — only to call verify_provenance() against a real file.
    import c2pa  # type: ignore[import-not-found]

    _C2PA_AVAILABLE = True
except ImportError:
    _C2PA_AVAILABLE = False


@dataclass
class RawManifest:
    """What we get back after reading and cryptographically checking a C2PA manifest.

    This is the seam between "talk to the c2pa-python library" and "decide what it
    means" — routing logic in `route()` only ever touches this shape, never the
    library's own return types, so a library upgrade can't silently change the
    decision table below it.
    """

    has_manifest: bool
    signature_valid: bool = False       # COSE signature checks out against the trust list
    hashes_match: bool = False          # recomputed content hashes match the manifest's claim
    digital_source_type: Optional[str] = None  # e.g. "trainedAlgorithmicMedia", "digitalCapture"
    signer: Optional[str] = None
    assertions: list[str] = field(default_factory=list)
    failed_assertion: Optional[str] = None  # which assertion broke, if hashes_match is False


def _read_manifest(file_path: str) -> RawManifest:
    """Read and cryptographically validate the embedded C2PA manifest, if any."""
    if not _C2PA_AVAILABLE:
        raise RuntimeError(
            "c2pa-python is not installed. Run `pip install -r requirements.txt`, "
            "or call route() directly with a hand-built RawManifest for testing."
        )
    
    try:
        reader = c2pa.Reader.try_create(file_path)
    except Exception:
        # Invalid file format or completely unreadable
        return RawManifest(has_manifest=False)

    if reader is None:
        return RawManifest(has_manifest=False)

    manifest_data = reader.get_active_manifest() or {}
    val_results = reader.get_validation_results() or {}
    
    # Defaults assuming it parsed
    signature_valid = True
    hashes_match = True
    failed_assertion = None
    
    # Any validation errors present?
    errors = val_results.get("errors", [])
    if errors:
        for err in errors:
            code = err.get("code", "")
            if "signature" in code:
                signature_valid = False
            elif "hash" in code or "hashedURI.mismatch" in code:
                hashes_match = False
                failed_assertion = err.get("url")

    # Extract assertions
    assertions_list = manifest_data.get("assertions", [])
    assertions_urls = [a.get("url", "") for a in assertions_list]
    
    # Look for digitalSourceType
    digital_source_type = None
    for assertion in assertions_list:
        # Typically found in c2pa.actions
        if "c2pa.actions" in assertion.get("label", ""):
            actions = assertion.get("data", {}).get("actions", [])
            for action_dict in actions:
                dst = action_dict.get("digitalSourceType")
                if dst:
                    # Usually a URI, grab the last part e.g. "trainedAlgorithmicMedia"
                    digital_source_type = str(dst).split("/")[-1]

    # Look for signer info
    signer = None
    sig_info = manifest_data.get("signature_info", {})
    if sig_info:
        signer = sig_info.get("issuer")

    return RawManifest(
        has_manifest=True,
        signature_valid=signature_valid,
        hashes_match=hashes_match,
        digital_source_type=digital_source_type,
        signer=signer,
        assertions=assertions_urls,
        failed_assertion=failed_assertion,
    )


def route(raw: RawManifest) -> ProvenanceBlock:
    """Pure decision logic for the four-state routing table. No I/O, no model calls —
    safe to unit-test directly against hand-built RawManifest fixtures.
    """
    if not raw.has_manifest or not raw.signature_valid:
        # No signed manifest, or a signature that doesn't chain to the trust list:
        # either way there is nothing verifiable here. This is NOT evidence of
        # synthesis — say "unknown provenance," never "fake".
        return ProvenanceBlock(state=C2PAState.UNTRUSTED)

    if not raw.hashes_match:
        # Signed, but content hashes no longer match the manifest's claim: proof of
        # post-signing alteration. This is the single highest-signal state the
        # provenance layer can produce, so it skips straight to the evidence packet
        # rather than passing through forensics at all.
        return ProvenanceBlock(
            state=C2PAState.TAMPERED,
            signer=raw.signer,
            trust_list_result=True,
            assertions=raw.assertions,
            failed_assertion=raw.failed_assertion,
        )

    if raw.digital_source_type == "trainedAlgorithmicMedia":
        # The file has "confessed" to being AI-generated media, by its own signed
        # testimony -> this is exactly the §21-5-90 trigger for disclosure measurement.
        return ProvenanceBlock(
            state=C2PAState.VALID_AI_ASSERTED,
            signer=raw.signer,
            trust_list_result=True,
            assertions=raw.assertions,
        )

    # Signed, hashes match, and no AI assertion: a verified camera capture.
    # Pipeline.py treats this as an early exit — no ML ever runs on this file.
    return ProvenanceBlock(
        state=C2PAState.VALID_CAPTURE,
        signer=raw.signer,
        trust_list_result=True,
        assertions=raw.assertions,
    )


def verify_provenance(file_path: str) -> ProvenanceBlock:
    """Public entry point: read the file's manifest, then route on it."""
    raw = _read_manifest(file_path)
    return route(raw)
