"""Georgia election calendar — the deterministic date table behind the 90-day check.

§21-2-605(b)(3) makes the criminal offense apply only "within 90 days of an election,"
so the evidence packet must compute that window against real dates, not guesses.
Dates below are the statewide 2026 Georgia election calendar (Secretary of State
published schedule). County/municipal special elections are out of scope for this
phase and noted honestly in the packet.

This module is pure data + date arithmetic: no I/O, no "today()" calls — callers pass
the analysis date in, so every function here is reproducible from its inputs alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

WINDOW_DAYS = 90  # §21-2-605(b)(3)


@dataclass(frozen=True)
class Election:
    date_iso: str
    name: str

    @property
    def as_date(self) -> date:
        return date.fromisoformat(self.date_iso)


# Statewide 2026 dates. Kept chronological; extend this table as later cycles are added.
GEORGIA_ELECTIONS: tuple[Election, ...] = (
    Election("2026-05-19", "General Primary"),
    Election("2026-06-16", "General Primary Runoff"),
    Election("2026-11-03", "General Election"),
    Election("2026-12-01", "General Election Runoff (if required)"),
)


def within_window(analysis_date_iso: str, election_date_iso: str) -> bool:
    """§21-2-605(b)(3): true when the analysis date falls within 90 days *before*
    (or on) the election date. Pure function of its inputs — the caller supplies
    "today", never this module.
    """
    analysis_date = date.fromisoformat(analysis_date_iso)
    election_date = date.fromisoformat(election_date_iso)
    return 0 <= (election_date - analysis_date).days <= WINDOW_DAYS


def next_election(analysis_date_iso: str) -> Optional[Election]:
    """First election on or after the analysis date, or None if the table is exhausted."""
    analysis_date = date.fromisoformat(analysis_date_iso)
    for election in GEORGIA_ELECTIONS:
        if election.as_date >= analysis_date:
            return election
    return None


def window_status(analysis_date_iso: str) -> dict:
    """Everything the action layer needs about the 90-day window, in one call.

    Returns a dict (not a dataclass) because this feeds straight into ActionBlock
    fields — see action.build_action_block.
    """
    analysis_date = date.fromisoformat(analysis_date_iso)
    election = next_election(analysis_date_iso)
    if election is None:
        return {
            "within_90_day_window": False,
            "next_election_date": None,
            "next_election_name": None,
            "window_opens": None,
            "days_until_election": None,
        }

    days_until = (election.as_date - analysis_date).days
    within = within_window(analysis_date_iso, election.date_iso)
    window_opens = election.as_date - timedelta(days=WINDOW_DAYS)
    return {
        "within_90_day_window": within,
        "next_election_date": election.date_iso,
        "next_election_name": election.name,
        "window_opens": None if within else window_opens.isoformat(),
        "days_until_election": days_until,
    }
