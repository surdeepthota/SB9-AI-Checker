"""Layer 5: the 90-day window, the exemption questionnaire, and packet eligibility."""

import pytest

from peachcheck import election_calendar
from peachcheck.election_calendar import within_window
from peachcheck.layers.action import (
    any_exemption_claimed,
    assemble_evidence_packet,
    build_action_block,
    finalize_action,
)

ALL_NO = {"satire": False, "parody": False, "artistic_expression": False, "journalism": False}


def test_within_window_boundaries():
    assert within_window("2026-08-05", "2026-11-03")  # exactly 90 days
    assert not within_window("2026-08-04", "2026-11-03")  # 91 days
    assert within_window("2026-11-03", "2026-11-03")  # election day
    assert not within_window("2026-11-04", "2026-11-03")  # after the election


def test_next_election_selection():
    assert election_calendar.next_election("2026-07-12").date_iso == "2026-11-03"
    assert election_calendar.next_election("2026-05-01").date_iso == "2026-05-19"
    assert election_calendar.next_election("2027-06-01") is None


def test_window_status_reports_when_window_opens():
    status = election_calendar.window_status("2026-07-12")
    assert status["within_90_day_window"] is False
    assert status["window_opens"] == "2026-08-05"
    assert status["days_until_election"] == 114


def test_incomplete_questionnaire_raises():
    with pytest.raises(ValueError):
        any_exemption_claimed({"satire": False})


def test_eligibility_requires_gate_window_and_no_exemption():
    inside_window = build_action_block("2026-09-01", gate_passed=True, deterministic_corroboration=["tampered_c2pa_hash"])
    assert inside_window.within_90_day_window

    eligible = finalize_action(inside_window, ALL_NO, publisher="A Campaign Committee")
    assert eligible.packet_eligible

    exempt = finalize_action(inside_window, {**ALL_NO, "satire": True}, publisher=None)
    assert not exempt.packet_eligible
    assert "satire" in exempt.guidance.lower() or "exemption" in exempt.guidance.lower()

    gate_closed = build_action_block("2026-09-01", gate_passed=False, deterministic_corroboration=[])
    assert not finalize_action(gate_closed, ALL_NO, publisher=None).packet_eligible

    outside_window = build_action_block("2026-07-01", gate_passed=True, deterministic_corroboration=["tampered_c2pa_hash"])
    assert not finalize_action(outside_window, ALL_NO, publisher=None).packet_eligible


def test_packet_has_hashes_and_no_submit_pretense():
    action = finalize_action(
        build_action_block("2026-09-01", gate_passed=True, deterministic_corroboration=["tampered_c2pa_hash"]),
        ALL_NO,
        publisher="Someone",
    )
    packet = assemble_evidence_packet(
        {"identity": {"sha256": "abc", "perceptual_hash": "def", "analyzed_at": "t"}},
        action,
    )
    assert packet["file_sha256"] == "abc"
    assert packet["file_perceptual_hash"] == "def"
    assert "not filed automatically" in packet["submission_instructions"]
