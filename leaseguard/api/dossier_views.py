"""JSON views for the deposit-recovery dossier."""

from leaseguard.api.views import JsonDict, steps_view
from leaseguard.dossier.certificate import build_certificate
from leaseguard.dossier.models import EVENT_TITLES, Dossier, Event, EvidenceFile


def file_view(evidence: EvidenceFile) -> JsonDict:
    """Serialise one evidence file (its text is never returned).

    Args:
        evidence: The file.

    Returns:
        A JSON-ready dictionary.
    """
    return {
        "annexure": evidence.annexure,
        "name": evidence.name,
        "kind": evidence.kind.value,
        "size_bytes": evidence.size_bytes,
        "sha256": evidence.sha256,
        "hash_matches": evidence.hash_matches,
    }


def event_view(event: Event) -> JsonDict:
    """Serialise one event.

    Args:
        event: The event.

    Returns:
        A JSON-ready dictionary; ``date`` is ISO format or null.
    """
    return {
        "date": event.when.isoformat() if event.when else None,
        "kind": event.kind.value,
        "title": EVENT_TITLES[event.kind],
        "actor": event.actor,
        "quote": event.quote,
        "summary": event.summary,
        "annexure": event.annexure,
        "amount": event.amount,
    }


def dossier_view(dossier: Dossier) -> JsonDict:
    """Serialise the dossier for the interface.

    Args:
        dossier: The dossier.

    Returns:
        A JSON-ready dictionary.
    """
    ledger = dossier.ledger
    certificate = build_certificate(dossier.parties, dossier.files)
    return {
        "files": [file_view(f) for f in dossier.files],
        "events": [event_view(e) for e in dossier.events],
        "contradictions": [c.message for c in dossier.contradictions],
        "ledger": {
            "deposit": ledger.deposit,
            "deposit_source": ledger.deposit_source,
            "refunded": ledger.refunded,
            "deductions_claimed": ledger.deductions_claimed,
            "outstanding": ledger.outstanding,
        },
        "limitation_deadline": dossier.limitation_deadline.isoformat() if dossier.limitation_deadline else None,
        "checklist": dossier.checklist,
        "certificate_title": certificate.title,
        "next_steps": steps_view(dossier.next_steps),
        "dossier_id": dossier.dossier_id or None,
    }
