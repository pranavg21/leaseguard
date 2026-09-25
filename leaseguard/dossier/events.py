"""Deterministic event detection: which messages matter in a deposit dispute."""

from collections.abc import Mapping
from types import MappingProxyType

from leaseguard.dossier.models import Event, EventKind, Message
from leaseguard.parsing import parse_amount

# Checked in order: the first kind whose phrases appear wins, so a message that
# both promises a refund and deducts money is classed as a deduction, and a tenant's
# demand to "refund the deposit as promised" is a demand, not a promise.
EVENT_PHRASES: Mapping[EventKind, tuple[str, ...]] = MappingProxyType(
    {
        EventKind.DEDUCTION_CLAIM: (
            "deduct",
            "damage charge",
            "painting charge",
            "cleaning charge",
            "will adjust",
            "cut from",
            "not refundable",
            "withhold",
        ),
        EventKind.REFUND: (
            "refunded",
            "returned rs",
            "returned ₹",
            "received refund",
            "refund credited",
            "transferred back",
        ),
        EventKind.DEMAND: (
            "legal notice",
            "please return",
            "please refund",
            "request you to return",
            "request you to refund",
            "reminder",
            "still pending",
        ),
        EventKind.REFUND_PROMISE: (
            "will return",
            "will refund",
            "will transfer",
            "shall return",
            "shall refund",
            "return your deposit",
            "full deposit",
        ),
        EventKind.MOVE_OUT: (
            "vacate",
            "vacated",
            "handed over",
            "keys received",
            "returned the keys",
            "moved out",
            "move out",
            "move-out",
        ),
        EventKind.PAYMENT: (
            "paid ",
            "payment of rs",
            "payment of ₹",
            "have transferred",
            "transferred rs",
            "transferred ₹",
        ),
    }
)


def classify_message(text: str) -> EventKind | None:
    """Return the event kind a message expresses, or None if it is not relevant.

    Args:
        text: Message text.

    Returns:
        The first matching event kind in priority order.
    """
    lowered = text.lower()
    return next((kind for kind, phrases in EVENT_PHRASES.items() if any(p in lowered for p in phrases)), None)


def to_event(message: Message, kind: EventKind, summary: str = "") -> Event:
    """Turn a message into an event that quotes it verbatim.

    Args:
        message: The source message.
        kind: The event kind.
        summary: Optional neutral one-line summary.

    Returns:
        The event, carrying the message date and any rupee amount it states.
    """
    amount = parse_amount(message.text)
    return Event(message.when, kind, message.sender, message.text, message.annexure, amount, summary)
