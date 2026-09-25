"""Build a deposit-recovery dossier from uploaded evidence."""

from dataclasses import dataclass

from leaseguard.ai import LLMClient
from leaseguard.constants import MAX_EVIDENCE_FILES
from leaseguard.dossier.events import to_event
from leaseguard.dossier.evidence import load_evidence
from leaseguard.dossier.ledger import build_ledger, checklist, limitation_deadline
from leaseguard.dossier.messages import messages_for
from leaseguard.dossier.models import Dossier, Event, EvidenceFile, Message, Parties
from leaseguard.dossier.timeline import find_contradictions, sort_events
from leaseguard.errors import IngestError
from leaseguard.grounding import appears_in
from leaseguard.models import Language


@dataclass(frozen=True)
class Upload:
    """A raw uploaded file and the hash the browser computed for it."""

    name: str
    data: bytes
    client_sha256: str | None


def load_files(uploads: list[Upload]) -> list[EvidenceFile]:
    """Fingerprint and read every upload in order.

    Args:
        uploads: The uploaded files.

    Returns:
        Evidence files labelled A-1, A-2, ...

    Raises:
        IngestError: If there are no files or too many.
    """
    if not uploads or len(uploads) > MAX_EVIDENCE_FILES:
        raise IngestError(f"Upload between 1 and {MAX_EVIDENCE_FILES} evidence files.")
    return [load_evidence(i, u.name, u.data, u.client_sha256) for i, u in enumerate(uploads)]


def extract_events(files: list[EvidenceFile], client: LLMClient, language: Language) -> list[Event]:
    """Label messages and keep only events whose quote appears verbatim in its source file.

    Args:
        files: The evidence files.
        client: AI client that labels messages.
        language: Language for event summaries.

    Returns:
        Verified events in chronological order.
    """
    messages: list[Message] = [m for f in files for m in messages_for(f)]
    labels = client.label_events(messages, language)
    sources = {f.annexure: f.text for f in files}
    labelled = sorted((i, label) for i, label in labels.items() if 0 <= i < len(messages))
    events = [to_event(messages[i], kind, summary) for i, (kind, summary) in labelled]
    return sort_events([e for e in events if appears_in(e.quote, sources[e.annexure])])


def build_dossier(
    uploads: list[Upload], lease_text: str | None, parties: Parties, client: LLMClient, language: Language
) -> Dossier:
    """Build the full dossier.

    Args:
        uploads: Evidence files.
        lease_text: The rental agreement, if the user provided it.
        parties: Names for the certificate and notice.
        client: AI client.
        language: Language for event summaries.

    Returns:
        The dossier.
    """
    files = load_files(uploads)
    events = extract_events(files, client, language)
    ledger = build_ledger(events, lease_text)
    return Dossier(
        parties=parties,
        files=files,
        events=events,
        contradictions=find_contradictions(events),
        ledger=ledger,
        limitation_deadline=limitation_deadline(events),
        checklist=checklist(files, events, ledger),
    )
