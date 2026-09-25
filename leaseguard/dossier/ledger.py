"""Deposit reconciliation, limitation reminder and missing-evidence checklist."""

from datetime import date

from leaseguard.constants import LIMITATION_YEARS
from leaseguard.dossier.dates import add_years
from leaseguard.dossier.models import Event, EventKind, EvidenceFile, EvidenceKind, Ledger
from leaseguard.dossier.timeline import first_of
from leaseguard.parsing import parse_amount


def _sum(events: list[Event], kind: EventKind) -> int:
    return sum(e.amount or 0 for e in events if e.kind is kind)


def deposit_from_lease(lease_text: str | None) -> int | None:
    """Return the rupee deposit stated in the lease, if any.

    Args:
        lease_text: The rental agreement, or None.

    Returns:
        The amount stated in the first sentence that mentions a deposit.
    """
    for sentence in (lease_text or "").split("\n"):
        if "deposit" in sentence.lower() and (amount := parse_amount(sentence)):
            return amount
    return None


def build_ledger(events: list[Event], lease_text: str | None) -> Ledger:
    """Reconcile the deposit against refunds and deductions.

    Sources in order of preference: the lease, deposit payments in the evidence, then the
    largest amount the landlord promised to refund.

    Args:
        events: All events.
        lease_text: The rental agreement, or None.

    Returns:
        The ledger.
    """
    lease_amount = deposit_from_lease(lease_text)
    paid = sum(e.amount or 0 for e in events if e.kind is EventKind.PAYMENT and "deposit" in e.quote.lower())
    promised = max((e.amount or 0 for e in events if e.kind is EventKind.REFUND_PROMISE), default=0)
    candidates = ((lease_amount, "rental agreement"), (paid, "payment evidence"), (promised, "landlord's message"))
    deposit, source = next(((amount, name) for amount, name in candidates if amount), (None, "not found"))
    return Ledger(deposit, source, _sum(events, EventKind.REFUND), _sum(events, EventKind.DEDUCTION_CLAIM))


def limitation_deadline(events: list[Event]) -> date | None:
    """Return a reminder date three years after move-out (or the first refund promise).

    Args:
        events: Chronologically sorted events.

    Returns:
        The date, or None if neither event is dated.
    """
    anchor = first_of(events, EventKind.MOVE_OUT) or first_of(events, EventKind.REFUND_PROMISE)
    return add_years(anchor.when, LIMITATION_YEARS) if anchor and anchor.when else None


def checklist(files: list[EvidenceFile], events: list[Event], ledger: Ledger) -> list[str]:
    """List evidence gaps a lawyer or court would notice.

    Args:
        files: All evidence files.
        events: All events.
        ledger: The deposit ledger.

    Returns:
        Plain-language gaps; empty when nothing obvious is missing.
    """
    kinds = {e.kind for e in events}
    gaps = [
        (ledger.deposit is None, "Add proof of the deposit amount: the rental agreement or a payment receipt."),
        (EventKind.MOVE_OUT not in kinds, "Add proof of move-out, such as a handover message or key receipt."),
        (EventKind.DEMAND not in kinds, "Send a written refund request and keep a copy; none was found."),
        (any(e.when is None for e in events), "Some events have no date. Add the date before filing."),
        (any(f.kind is EvidenceKind.IMAGE for f in files), "Images are hashed but not read. Describe each one."),
        (any(f.hash_matches is False for f in files), "A file changed during upload. Upload it again."),
    ]
    return [message for missing, message in gaps if missing]
