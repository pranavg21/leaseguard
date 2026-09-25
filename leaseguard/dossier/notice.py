"""Draft pre-litigation demand notice, built only from verified facts."""

from datetime import date

from leaseguard.constants import NOTICE_REPLY_DAYS
from leaseguard.dossier.models import Dossier, Event, EventKind
from leaseguard.dossier.timeline import first_of
from leaseguard.formatting import indian_rupees

BLANK = "____________________"
NOTE = "Draft prepared by LeaseGuard for review by you or a lawyer before sending. It is not legal advice."


def rupees(amount: int | None) -> str:
    """Format rupees for the notice, leaving a blank to fill when the amount is unknown.

    Args:
        amount: Whole rupees, or None.

    Returns:
        For example ``Rs. 1,50,000``.
    """
    return f"Rs. {BLANK}" if amount is None else indian_rupees(amount)


def _on(event: Event | None) -> str:
    return event.when.strftime("%d %B %Y") if event and event.when else BLANK


def fact_lines(dossier: Dossier) -> list[str]:
    """State the key facts, each tied to an annexure.

    Args:
        dossier: The dossier.

    Returns:
        Numbered-ready fact sentences.
    """
    events = dossier.events
    move_out = first_of(events, EventKind.MOVE_OUT)
    promise = first_of(events, EventKind.REFUND_PROMISE)
    ledger = dossier.ledger
    source = f", as shown in the {ledger.deposit_source}" if ledger.deposit is not None else ""
    facts = [f"I paid you a security deposit of {rupees(ledger.deposit)}{source}."]
    if move_out:
        facts.append(
            f"I vacated the premises and handed over possession on {_on(move_out)} (Annexure {move_out.annexure})."
        )
    if promise:
        facts.append(f"On {_on(promise)} you agreed in writing to refund the deposit (Annexure {promise.annexure}).")
    facts += [
        f"{c.later.actor} later claimed deductions (Annexure {c.later.annexure}), contradicting that promise."
        for c in dossier.contradictions
    ]
    facts.append(f"To date you have refunded {rupees(dossier.ledger.refunded)}.")
    return facts


def build_notice(dossier: Dossier, today: date) -> list[str]:
    """Draft the demand notice as paragraphs.

    Args:
        dossier: The dossier.
        today: The date to print on the notice.

    Returns:
        Paragraphs in order, beginning with the drafting note.
    """
    parties = dossier.parties
    facts = [f"{n}. {line}" for n, line in enumerate(fact_lines(dossier), start=1)]
    return [
        NOTE,
        f"Date: {today.strftime('%d %B %Y')}",
        f"To: {parties.landlord or BLANK}",
        f"Subject: Demand for refund of security deposit for {parties.property_address or BLANK}",
        *facts,
        (
            f"I call upon you to pay {rupees(dossier.ledger.outstanding)} within {NOTICE_REPLY_DAYS} days of receiving "
            "this notice, failing which I may pursue the remedies available to me in law, at your cost."
        ),
        f"Yours faithfully, {parties.tenant or BLANK}",
    ]
