"""Shared evidence fixtures for dossier tests."""

from datetime import date

from leaseguard.dossier.models import Event, EventKind, EvidenceFile, EvidenceKind, Parties

CHAT = (
    b"10/03/2026, 11:00 - Priya: I have vacated the flat and handed over the keys today.\n"
    b"12/03/2026, 10:15 - Ravi: Keys received. I will return your full deposit of Rs. 50,000 within 7 days.\n"
    b"[20/03/26, 6:40:11 PM] Ravi: I am deducting Rs. 20,000 for painting charges\n"
    b"and cleaning.\n"
    b"25/03/2026, 09:00 - Priya: Please refund the deposit as promised.\n"
)
RECEIPT = b"UPI Payment Receipt\nDate: 01/10/2025\nPaid Rs. 50,000 to Ravi towards security deposit\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
PARTIES = Parties("Priya", "Ravi", "Flat 4, Pune")


def evidence(text: str, kind: EvidenceKind = EvidenceKind.TEXT, annexure: str = "A-1") -> EvidenceFile:
    """Build an evidence file directly from text."""
    return EvidenceFile(annexure, "f.txt", kind, "0" * 64, len(text), None, text)


def event(kind: EventKind, when: date | None = None, actor: str = "Ravi", amount: int | None = None) -> Event:
    """Build an event for timeline and ledger tests."""
    return Event(when, kind, actor, f"{kind.value} message", "A-1", amount)
