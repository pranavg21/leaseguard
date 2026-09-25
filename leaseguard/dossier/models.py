"""Typed data structures for the deposit-recovery dossier."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class EvidenceKind(StrEnum):
    """What an evidence file contains, detected from its content."""

    WHATSAPP = "whatsapp"
    TEXT = "text"
    PDF = "pdf"
    IMAGE = "image"


class EventKind(StrEnum):
    """Legally relevant event types in a deposit dispute."""

    PAYMENT = "payment"
    MOVE_OUT = "move_out"
    REFUND_PROMISE = "refund_promise"
    REFUND = "refund"
    DEDUCTION_CLAIM = "deduction_claim"
    DEMAND = "demand"


EVENT_TITLES = {
    EventKind.PAYMENT: "Payment made",
    EventKind.MOVE_OUT: "Move-out / handover",
    EventKind.REFUND_PROMISE: "Refund promised",
    EventKind.REFUND: "Refund received",
    EventKind.DEDUCTION_CLAIM: "Deduction claimed",
    EventKind.DEMAND: "Refund demanded",
}


@dataclass(frozen=True)
class EvidenceFile:
    """One uploaded evidence file, fingerprinted on arrival."""

    annexure: str
    name: str
    kind: EvidenceKind
    sha256: str
    size_bytes: int
    client_sha256: str | None
    text: str

    @property
    def hash_matches(self) -> bool | None:
        """Whether the browser's hash equals the server's, or None if the browser sent none."""
        return None if self.client_sha256 is None else self.client_sha256.lower() == self.sha256


@dataclass(frozen=True)
class Message:
    """One line or chat message from an evidence file, kept verbatim."""

    annexure: str
    when: date | None
    sender: str
    text: str


@dataclass(frozen=True)
class Event:
    """A dated, sourced event. ``quote`` is verified against the evidence text."""

    when: date | None
    kind: EventKind
    actor: str
    quote: str
    annexure: str
    amount: int | None
    summary: str = ""


@dataclass(frozen=True)
class Contradiction:
    """A later statement by the same party that conflicts with an earlier one."""

    earlier: Event
    later: Event
    message: str


@dataclass(frozen=True)
class Ledger:
    """Deposit reconciliation in rupees. ``None`` means the figure is unknown."""

    deposit: int | None
    deposit_source: str
    refunded: int
    deductions_claimed: int

    @property
    def outstanding(self) -> int | None:
        """Deposit minus refunds received; disputed deductions are not subtracted."""
        return None if self.deposit is None else max(self.deposit - self.refunded, 0)


@dataclass(frozen=True)
class Parties:
    """Names used in the certificate and notice."""

    tenant: str
    landlord: str
    property_address: str


@dataclass
class Dossier:
    """The complete deposit-recovery dossier."""

    parties: Parties
    files: list[EvidenceFile]
    events: list[Event]
    contradictions: list[Contradiction]
    ledger: Ledger
    limitation_deadline: date | None
    checklist: list[str] = field(default_factory=list)
