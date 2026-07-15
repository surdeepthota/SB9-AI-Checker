"""Routing integration: which layers run for each provenance state, the report
language rules, and the perceptual hash's survival across re-encoding."""

from PIL import Image

from peachcheck.pipeline import compute_dhash, run_pipeline
from peachcheck.schema import C2PAState, report_to_dict

ANALYZED_AT = "2026-07-12T12:00:00+00:00"


def _hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def test_dhash_survives_reencode_but_separates_different_images(tmp_path):
    from PIL import ImageDraw

    gradient = Image.new("RGB", (200, 200))
    for x in range(200):
        for y in range(200):
            gradient.putpixel((x, y), (x, y, (x + y) % 255))
    original = tmp_path / "a.png"
    reencoded = tmp_path / "a.jpg"
    gradient.save(original, "PNG")
    gradient.save(reencoded, "JPEG", quality=70)

    different = Image.new("RGB", (200, 200), (255, 255, 255))
    ImageDraw.Draw(different).ellipse((30, 30, 170, 170), fill=(0, 0, 0))
    other = tmp_path / "b.png"
    different.save(other, "PNG")

    h_orig = compute_dhash(str(original))
    h_reenc = compute_dhash(str(reencoded))
    h_other = compute_dhash(str(other))
    assert _hamming(h_orig, h_reenc) <= 6  # laundering survivability
    assert _hamming(h_orig, h_other) > 16  # discrimination


def test_untrusted_route_runs_forensics_and_judgment(tiny_jpeg):
    report = run_pipeline(tiny_jpeg, "image/jpeg", ANALYZED_AT)
    assert report.provenance.state == C2PAState.UNTRUSTED
    assert report.forensics is not None
    assert report.judgment is not None
    assert report.action is not None
    ran = {step.layer: step.ran for step in report.route}
    assert ran == {"provenance": True, "forensics": True, "measurement": False,
                   "judgment": True, "action": True}


def test_report_language_never_says_fake(tiny_jpeg):
    report = run_pipeline(tiny_jpeg, "image/jpeg", ANALYZED_AT)
    serialized = str(report_to_dict(report)).lower()
    # The cardinal rule, checked over every string any layer produced. "fake" may
    # only ever appear inside the ML-accuracy caveat wording, which is disabled in
    # unit tests — so here: nowhere at all.
    assert "fake" not in serialized


def test_headline_uses_plain_unknown_source_phrasing(tiny_jpeg):
    report = run_pipeline(tiny_jpeg, "image/jpeg", ANALYZED_AT)
    assert report.headline.startswith("The source is unknown.")
    assert "checks found something unusual" in report.headline


def test_forensics_alone_never_opens_the_reporting_path(tiny_jpeg):
    # A plain no-metadata image triggers soft signals, but with no deterministic
    # corroboration the gate must stay closed regardless of score.
    report = run_pipeline(tiny_jpeg, "image/jpeg", ANALYZED_AT)
    assert report.action.gate_passed is False
    assert report.action.packet_eligible is False


def test_serialization_is_json_safe(tiny_jpeg):
    import json

    report = run_pipeline(tiny_jpeg, "image/jpeg", ANALYZED_AT)
    payload = json.dumps(report_to_dict(report))  # raises if any enum/dataclass leaks
    assert '"untrusted"' in payload
