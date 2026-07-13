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

The layer runs in two phases, matching how a real filing works:

  Phase 1 (at analysis time, pipeline.py): compute the statutory context — the 90-day
  window, whether the deterministic gate passed, and what corroborates it. The
  exemption questionnaire and publisher field stay empty; the pipeline never invents
  a user's answers.

  Phase 2 (the /packet endpoint): the user completes the §21-2-605(d) exemption
  questionnaire and names the publisher; only then is packet eligibility decided and
  the evidence packet assembled.

This layer only decides *packet eligibility*; it never decides guilt.
"""

from __future__ import annotations

from peachcheck.schema import ActionBlock
from peachcheck import election_calendar

# §21-2-605(d) exemptions. All must be answered "no" for a filing to proceed — an
# honest "yes" to any of these means the statute doesn't reach this media at all.
EXEMPTION_QUESTIONS = ("satire", "parody", "artistic_expression", "journalism")

SEB_SUBMISSION_INSTRUCTIONS = (
    "This packet is not filed automatically — PeachCheck has no submission API into "
    "the State Election Board, and pretending otherwise would be dishonest. To file: "
    "(1) download this packet as JSON; (2) submit it with a written complaint to the "
    "Georgia State Election Board per their published complaint process "
    "(sos.ga.gov, State Election Board); (3) retain the SHA-256 and perceptual hash "
    "in the packet to prove which file your complaint concerns. Under SB 9 "
    "§21-2-33.1(a.1), the Board must publicly release findings of any completed "
    "investigation."
)


def any_exemption_claimed(exemption_answers: dict[str, bool]) -> bool:
    """True if the user affirmed any §21-2-605(d) exemption applies."""
    missing = set(EXEMPTION_QUESTIONS) - set(exemption_answers)
    if missing:
        raise ValueError(f"Exemption questionnaire incomplete, missing: {sorted(missing)}")
    return any(exemption_answers[question] for question in EXEMPTION_QUESTIONS)


def build_action_block(
    analysis_date_iso: str,
    gate_passed: bool,
    deterministic_corroboration: list[str],
) -> ActionBlock:
    """Phase 1: statutory context at analysis time. `gate_passed` must come from
    judgment.gate_allows_reporting() (or be True for a TAMPERED provenance state,
    where the broken hash itself is the deterministic evidence) — this function does
    not re-derive it, so the precision-over-recall gate lives in exactly one place.
    """
    window = election_calendar.window_status(analysis_date_iso)

    if not gate_passed:
        guidance = (
            "This analysis does not meet the bar for the SB 9 reporting path: only a "
            "strong, deterministically corroborated finding ever does, and forensic "
            "suspicion alone never files. No action is recommended."
        )
    elif not window["within_90_day_window"]:
        opens = window["window_opens"]
        guidance = (
            "The findings are strong enough for the reporting path, but today is "
            f"outside the statute's 90-day pre-election window"
            + (
                f" — the window for the {window['next_election_name']} "
                f"({window['next_election_date']}) opens {opens}."
                if opens
                else "."
            )
            + " You can still assemble and retain the evidence packet now."
        )
    else:
        guidance = (
            "The findings are deterministically corroborated and today falls inside "
            "the 90-day window. Complete the exemption questionnaire and publisher "
            "field to assemble an evidence packet for the State Election Board."
        )

    return ActionBlock(
        within_90_day_window=window["within_90_day_window"],
        next_election_date=window["next_election_date"],
        next_election_name=window["next_election_name"],
        window_opens=window["window_opens"],
        days_until_election=window["days_until_election"],
        deterministic_corroboration=list(deterministic_corroboration),
        gate_passed=gate_passed,
        guidance=guidance,
        # Questionnaire and publisher are user inputs, filled in phase 2 (/packet).
        packet_eligible=False,
    )


def finalize_action(
    action: ActionBlock,
    exemption_answers: dict[str, bool],
    publisher: str | None,
) -> ActionBlock:
    """Phase 2: fold the user's questionnaire answers and publisher into the block
    and decide packet eligibility. Eligible only if every gate holds: layer-4
    corroborated strong signal (or tampered provenance), inside the statutory window,
    and no claimed First Amendment exemption.
    """
    exempt = any_exemption_claimed(exemption_answers)
    eligible = action.gate_passed and bool(action.within_90_day_window) and not exempt

    if exempt:
        guidance = (
            "An exemption was claimed (satire, parody, artistic expression, or "
            "journalism). §21-2-605(d) carves this media out of the offense entirely, "
            "so no SEB filing is appropriate. The analysis record is still yours to keep."
        )
    elif eligible:
        guidance = SEB_SUBMISSION_INSTRUCTIONS
    else:
        guidance = action.guidance  # unchanged: gate or window already explained it

    return ActionBlock(
        within_90_day_window=action.within_90_day_window,
        next_election_date=action.next_election_date,
        next_election_name=action.next_election_name,
        window_opens=action.window_opens,
        days_until_election=action.days_until_election,
        deterministic_corroboration=list(action.deterministic_corroboration),
        gate_passed=action.gate_passed,
        exemption_answers=dict(exemption_answers),
        publisher=publisher,
        packet_eligible=eligible,
        guidance=guidance,
    )


def assemble_evidence_packet(trust_report_dict: dict, action: ActionBlock) -> dict:
    """Build the exportable packet payload (still just data here; the API layer turns
    it into a downloadable JSON response).

    Deliberately NOT a submission call — there is no SEB API to call. The packet
    includes everything a filer needs to submit by hand: identity hashes, the full
    trust report, the questionnaire answers, and the computed eligibility fields.
    """
    identity = trust_report_dict.get("identity", {})
    return {
        "packet_version": "0.2.0",
        "packet_eligible": action.packet_eligible,
        "file_sha256": identity.get("sha256"),
        "file_perceptual_hash": identity.get("perceptual_hash"),
        "analyzed_at": identity.get("analyzed_at"),
        "publisher": action.publisher,
        "exemption_answers": dict(action.exemption_answers),
        "statutory_window": {
            "within_90_day_window": action.within_90_day_window,
            "next_election_date": action.next_election_date,
            "next_election_name": action.next_election_name,
            "days_until_election": action.days_until_election,
        },
        "deterministic_corroboration": list(action.deterministic_corroboration),
        "trust_report": trust_report_dict,
        "submission_instructions": SEB_SUBMISSION_INSTRUCTIONS,
    }
