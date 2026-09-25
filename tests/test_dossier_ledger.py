"""Tests for leaseguard/dossier/ledger.py."""

from datetime import date

from leaseguard.dossier.ledger import build_ledger, checklist, deposit_from_lease, limitation_deadline
from leaseguard.dossier.models import EventKind, EvidenceFile, EvidenceKind, Ledger
from leaseguard.sample import SAMPLE_LEASE
from tests.dossier_fixtures import event


def test_deposit_from_lease() -> None:
    assert deposit_from_lease(SAMPLE_LEASE) == 250_000
    assert deposit_from_lease(None) is None
    assert deposit_from_lease("No money terms here.") is None


def test_ledger_prefers_lease_then_payments_then_promise() -> None:
    payment = event(EventKind.PAYMENT, amount=40_000)
    payment = type(payment)(payment.when, payment.kind, "", "Paid Rs. 40,000 security deposit", "A-2", 40_000)
    promise = event(EventKind.REFUND_PROMISE, amount=30_000)
    refund = event(EventKind.REFUND, amount=5_000)
    claim = event(EventKind.DEDUCTION_CLAIM, amount=7_000)
    assert build_ledger([payment], SAMPLE_LEASE).deposit_source == "rental agreement"
    assert build_ledger([payment, refund, claim], None) == Ledger(40_000, "payment evidence", 5_000, 7_000)
    assert build_ledger([promise], None).deposit_source == "landlord's message"
    assert build_ledger([], None) == Ledger(None, "not found", 0, 0)


def test_limitation_counts_from_move_out_or_promise() -> None:
    move = event(EventKind.MOVE_OUT, date(2026, 3, 10))
    promise = event(EventKind.REFUND_PROMISE, date(2026, 4, 1))
    assert limitation_deadline([move, promise]) == date(2029, 3, 10)
    assert limitation_deadline([promise]) == date(2029, 4, 1)
    assert limitation_deadline([event(EventKind.DEMAND)]) is None


def test_checklist_reports_each_gap() -> None:
    image = EvidenceFile("A-1", "p.png", EvidenceKind.IMAGE, "a" * 64, 1, "b" * 64, "")
    gaps = checklist([image], [event(EventKind.PAYMENT)], Ledger(None, "not found", 0, 0))
    assert len(gaps) == 6
    complete = [event(k, date(2026, 1, 1)) for k in (EventKind.MOVE_OUT, EventKind.DEMAND)]
    assert checklist([], complete, Ledger(1, "x", 0, 0)) == []
