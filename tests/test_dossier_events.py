"""Tests for leaseguard/dossier/events.py."""

from datetime import date

import pytest

from leaseguard.dossier.events import EVENT_PHRASES, classify_message, to_event
from leaseguard.dossier.models import EventKind, Message


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("I will return your full deposit in a week", EventKind.REFUND_PROMISE),
        ("Will return deposit but I am deducting Rs. 5,000", EventKind.DEDUCTION_CLAIM),
        ("Refund credited Rs. 10,000", EventKind.REFUND),
        ("Please refund the deposit as promised", EventKind.DEMAND),
        ("This is a reminder that the full deposit is pending", EventKind.DEMAND),
        ("I have vacated the flat today", EventKind.MOVE_OUT),
        ("Paid Rs. 50,000 towards deposit", EventKind.PAYMENT),
        ("UPI Payment Receipt", None),
        ("Good morning", None),
    ],
)
def test_classify_message(text: str, kind: EventKind | None) -> None:
    assert classify_message(text) is kind


def test_every_kind_has_phrases() -> None:
    assert set(EVENT_PHRASES) == set(EventKind)


def test_to_event_copies_message_verbatim() -> None:
    message = Message("A-2", date(2026, 1, 1), "Ravi", "I am deducting Rs. 20,000")
    event = to_event(message, EventKind.DEDUCTION_CLAIM, "Landlord deducts")
    assert event.quote == message.text
    assert event.amount == 20_000
    assert event.annexure == "A-2"
    assert event.summary == "Landlord deducts"
