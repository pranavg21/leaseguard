"""Tests for leaseguard/dossier/notice.py."""

from datetime import date

import pytest

from leaseguard.dossier.models import Dossier, EventKind, Ledger, Parties
from leaseguard.dossier.notice import BLANK, build_notice, fact_lines, rupees
from leaseguard.dossier.timeline import find_contradictions
from tests.dossier_fixtures import PARTIES, event


@pytest.mark.parametrize(
    ("amount", "text"),
    [
        (5, "Rs. 5"),
        (1000, "Rs. 1,000"),
        (150_000, "Rs. 1,50,000"),
        (12_345_678, "Rs. 1,23,45,678"),
        (None, f"Rs. {BLANK}"),
    ],
)
def test_rupees_uses_indian_grouping(amount: int | None, text: str) -> None:
    assert rupees(amount) == text


def make_dossier(parties: Parties = PARTIES, deposit: int | None = 50_000) -> Dossier:
    events = [
        event(EventKind.MOVE_OUT, date(2026, 3, 10), "Priya"),
        event(EventKind.REFUND_PROMISE, date(2026, 3, 12)),
        event(EventKind.DEDUCTION_CLAIM, date(2026, 3, 20)),
    ]
    return Dossier(parties, [], events, find_contradictions(events), Ledger(deposit, "rental agreement", 0, 0), None)


def test_facts_cite_annexures() -> None:
    facts = fact_lines(make_dossier())
    assert facts[0] == "I paid you a security deposit of Rs. 50,000, as shown in the rental agreement."
    assert "10 March 2026 (Annexure A-1)" in facts[1]
    assert "contradicting" in facts[3]


def test_notice_structure_and_blanks() -> None:
    notice = build_notice(make_dossier(Parties("", "", ""), None), date(2026, 9, 24))
    assert notice[0].startswith("Draft")
    assert notice[1] == "Date: 24 September 2026"
    assert notice[2] == f"To: {BLANK}"
    assert "security deposit of Rs." in notice[4]
    assert "shown in the" not in notice[4]
    assert "within 15 days" in notice[-2]
