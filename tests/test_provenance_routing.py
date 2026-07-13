"""The four-state routing table, tested exactly as designed: pure decisions on
hand-built RawManifest fixtures, no c2pa library or files needed."""

from peachcheck.layers.provenance import RawManifest, route
from peachcheck.schema import C2PAState


def test_no_manifest_is_untrusted_never_fake():
    block = route(RawManifest(has_manifest=False))
    assert block.state == C2PAState.UNTRUSTED
    assert "fake" not in (block.explanation or "").lower()


def test_invalid_signature_is_untrusted():
    block = route(RawManifest(has_manifest=True, signature_valid=False, hashes_match=True))
    assert block.state == C2PAState.UNTRUSTED
    assert block.trust_list_result is False


def test_expired_credential_is_untrusted():
    block = route(
        RawManifest(has_manifest=True, signature_valid=True, hashes_match=True, cert_expired=True)
    )
    assert block.state == C2PAState.UNTRUSTED


def test_hash_mismatch_is_tampered_with_named_assertion():
    block = route(
        RawManifest(
            has_manifest=True,
            signature_valid=True,
            hashes_match=False,
            trusted_signer=True,
            failed_assertion="assertion.dataHash.mismatch",
            signer="Any Signer",
        )
    )
    assert block.state == C2PAState.TAMPERED
    assert block.failed_assertion == "assertion.dataHash.mismatch"


def test_signature_failure_beats_hash_failure():
    # If the signature itself is bad, hash claims are meaningless — must not report
    # TAMPERED (which implies a *valid* signature over changed content).
    block = route(
        RawManifest(has_manifest=True, signature_valid=False, hashes_match=False)
    )
    assert block.state == C2PAState.UNTRUSTED


def test_ai_assertion_routes_to_measurement_state():
    for dst in ("trainedAlgorithmicMedia", "compositeWithTrainedAlgorithmicMedia"):
        block = route(
            RawManifest(
                has_manifest=True,
                signature_valid=True,
                hashes_match=True,
                trusted_signer=True,
                digital_source_type=dst,
            )
        )
        assert block.state == C2PAState.VALID_AI_ASSERTED
        assert block.digital_source_type == dst


def test_valid_capture_state():
    block = route(
        RawManifest(
            has_manifest=True,
            signature_valid=True,
            hashes_match=True,
            trusted_signer=True,
            digital_source_type="digitalCapture",
            signer="Truepic",
        )
    )
    assert block.state == C2PAState.VALID_CAPTURE
    assert block.signer == "Truepic"


def test_untrusted_signer_is_reported_not_hidden():
    block = route(
        RawManifest(
            has_manifest=True, signature_valid=True, hashes_match=True, trusted_signer=False
        )
    )
    assert block.state == C2PAState.VALID_CAPTURE
    assert block.trust_list_result is False
    assert "trust list" in block.explanation
