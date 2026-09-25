"""Tests for leaseguard/dossier/next_steps.py."""

from datetime import date

from leaseguard.dossier.models import Dossier, Event, EventKind, Ledger
from leaseguard.dossier.next_steps import CERTIFICATE_STEP, LOK_ADALAT_STEP, demand_step, dossier_steps, forum_step
from leaseguard.steps import FREE_LEGAL_AID
from tests.dossier_fixtures import PARTIES, event


def make(events: list[Event], checklist: list[str], deadline: date | None) -> Dossier:
    return Dossier(PARTIES, [], events, [], Ledger(50_000, "x", 0, 0), deadline, checklist)


def test_full_plan_order() -> None:
    steps = dossier_steps(make([], ["Add proof of move-out."], date(2029, 8, 31)))
    assert [s.title for s in steps] == [
        "Fill the gaps in your evidence",
        "Send the demand notice",
        CERTIFICATE_STEP.title,
        LOK_ADALAT_STEP.title,
        "If there is no refund, choose the forum with a lawyer",
        FREE_LEGAL_AID.title,
    ]


def test_demand_already_made_is_acknowledged() -> None:
    step = demand_step(make([event(EventKind.DEMAND, date(2026, 9, 16), "Priya")], [], None))
    assert step.title == "Keep proof of your demand"
    assert "16 September 2026" in step.detail
    assert "15 days" in demand_step(make([], [], None)).detail


def test_forum_step_mentions_deadline_and_not_consumer_commission() -> None:
    with_deadline = forum_step(make([], [], date(2029, 8, 31)))
    assert "31 August 2029" in with_deadline.detail
    assert "not the consumer commission" in with_deadline.detail
    assert "File well before" not in forum_step(make([], [], None)).detail
    assert dossier_steps(make([], [], None))[0].title == "Send the demand notice"
