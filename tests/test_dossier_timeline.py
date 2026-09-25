"""Tests for leaseguard/dossier/timeline.py."""

from datetime import date

from leaseguard.dossier.models import EventKind
from leaseguard.dossier.timeline import find_contradictions, first_of, sort_events
from tests.dossier_fixtures import event

PROMISE = event(EventKind.REFUND_PROMISE, date(2026, 3, 12))
CLAIM = event(EventKind.DEDUCTION_CLAIM, date(2026, 3, 20))


def test_sort_puts_undated_last() -> None:
    undated = event(EventKind.DEMAND)
    assert sort_events([undated, CLAIM, PROMISE]) == [PROMISE, CLAIM, undated]


def test_promise_then_deduction_is_a_contradiction() -> None:
    [found] = find_contradictions([PROMISE, CLAIM])
    assert found.earlier is PROMISE
    assert found.later is CLAIM
    assert "Ravi" in found.message


def test_no_contradiction_for_other_person_or_earlier_claim() -> None:
    other = event(EventKind.DEDUCTION_CLAIM, date(2026, 3, 20), actor="Agent")
    early = event(EventKind.DEDUCTION_CLAIM, date(2026, 3, 1))
    assert find_contradictions([PROMISE, other]) == []
    assert find_contradictions([early, PROMISE]) == []
    assert find_contradictions([event(EventKind.REFUND_PROMISE, date(2026, 1, 1), actor=""), CLAIM]) == []


def test_first_of_skips_undated() -> None:
    assert first_of([event(EventKind.MOVE_OUT), PROMISE], EventKind.REFUND_PROMISE) is PROMISE
    assert first_of([event(EventKind.MOVE_OUT)], EventKind.MOVE_OUT) is None
