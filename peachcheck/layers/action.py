"""Layer 5 — Civic Action.

Not an AI model. This layer never runs an inference — it only assembles what the
earlier layers already established into something a human can file with Georgia's
State Election Board (SEB). There is no API into the SEB [LOCKED], so the output here
is a complete evidence packet with submission instructions, never a fake "submit"
button.

Why the SEB specifically: under SB 9 §21-2-605(g), the Attorney General can only
prosecute after receiving a recommendation from the SEB, and §21-2-33.1(a.1) requires
the SEB to publicly release findings of any completed investigation — that publication
is the app's feedback loop back to the community page.

This layer only decides *packet eligibility*; it never decides guilt. Eligibility
requires the layer-4 gate to have passed (see judgment.gate_allows_reporting) plus a
completed exemption questionnaire, because §21-2-605(d) carves out satire, parody,
artistic expression, and bona fide journalism from the offense entirely.
"""

from __future__ import annotations

from peachcheck.schema import ActionBlock

# §21-2-605(d) exemptions. All must be answered "no" for a filing to proceed — an
# honest "yes" to any of these means the statute doesn't reach this media at all.
EXEMPTION_QUESTIONS = ("satire", "parody", "artistic_expression", "journalism")


def within_90_day_window(analysis_date_iso: str, next_election_date_iso: str) -> bool:
    """§21-2-605(b)(3): the offense only applies within 90 days of an election.

    Dates are passed in as ISO-8601 strings (not computed with datetime.now()/date.today()
    inside this function) so the check stays a pure, testable function of its inputs —
    the caller is responsible for supplying "today" and the relevant election date from
    Georgia's election calendar.
    """
    from datetime import date

    analysis_date = date.fromisoformat(analysis_date_iso)
    election_date = date.fromisoformat(next_election_date_iso)
    return 0 <= (election_date - analysis_date).days <= 90


def any_exemption_claimed(exemption_answers: dict[str, bool]) -> bool:
    """True if the user affirmed any §21-2-605(d) exemption applies."""
    missing = set(EXEMPTION_QUESTIONS) - set(exemption_answers)
    if missing:
        raise ValueError(f"Exemption questionnaire incomplete, missing: {sorted(missing)}")
    return any(exemption_answers[question] for question in EXEMPTION_QUESTIONS)


def build_action_block(
    analysis_date_iso: str,
    next_election_date_iso: str,
    exemption_answers: dict[str, bool],
    publisher: str | None,
    gate_passed: bool,
) -> ActionBlock:
    """Assemble the action block. `gate_passed` must come from
    judgment.gate_allows_reporting() — this function does not re-derive it, so the
    precision-over-recall gate lives in exactly one place.
    """
    in_window = within_90_day_window(analysis_date_iso, next_election_date_iso)
    exempt = any_exemption_claimed(exemption_answers)

    return ActionBlock(
        within_90_day_window=in_window,
        exemption_answers=dict(exemption_answers),
        publisher=publisher,
        # Eligible only if every gate holds: layer-4 corroborated strong signal,
        # inside the statutory window, and no claimed First Amendment exemption.
        packet_eligible=gate_passed and in_window and not exempt,
    )


def assemble_evidence_packet(trust_report_dict: dict) -> dict:
    """Build the exportable packet payload (still just data here; PDF/JSON rendering
    is a presentation concern that belongs outside this layer).

    Deliberately NOT a submission call — there is no SEB API to call. The packet
    includes everything a filer needs to submit by hand: identity hashes, the full
    trust report, and the computed eligibility fields above.
    """
    return {
        "packet_version": "0.1.0",
        "trust_report": trust_report_dict,
        "submission_instructions": (
            "This packet is not filed automatically. Submit it to the Georgia State "
            "Election Board per their published complaint process; retain the SHA-256 "
            "and perceptual hash above to prove which file this packet corresponds to."
        ),
    }
