"""Order events chronologically and flag contradictions between them."""

from datetime import date

from leaseguard.dossier.models import Contradiction, Event, EventKind

_UNDATED = date.max


def sort_events(events: list[Event]) -> list[Event]:
    """Sort by date; undated events go last so the user can date them.

    Args:
        events: Events in any order.

    Returns:
        Events in chronological order (stable for equal dates).
    """
    return sorted(events, key=lambda event: event.when or _UNDATED)


def find_contradictions(events: list[Event]) -> list[Contradiction]:
    """Flag a refund promise followed by a deduction claim from the same person.

    Args:
        events: Chronologically sorted events.

    Returns:
        One contradiction per promise that a later deduction claim reverses.
    """
    contradictions = []
    for promise in (e for e in events if e.kind is EventKind.REFUND_PROMISE and e.actor):
        later = next((e for e in events if _reverses(promise, e)), None)
        if later is not None:
            message = f"{promise.actor} promised a refund, then later claimed deductions."
            contradictions.append(Contradiction(promise, later, message))
    return contradictions


def _reverses(promise: Event, candidate: Event) -> bool:
    return (
        candidate.kind is EventKind.DEDUCTION_CLAIM
        and candidate.actor == promise.actor
        and (candidate.when or _UNDATED) >= (promise.when or _UNDATED)
    )


def first_of(events: list[Event], kind: EventKind) -> Event | None:
    """Return the earliest dated event of a kind.

    Args:
        events: Chronologically sorted events.
        kind: The kind to look for.

    Returns:
        The event, or None.
    """
    return next((e for e in events if e.kind is kind and e.when is not None), None)
