"""Split evidence text into verbatim, dated messages."""

from leaseguard.dossier.dates import find_date, make_date
from leaseguard.dossier.evidence import WHATSAPP_LINE
from leaseguard.dossier.models import EvidenceFile, EvidenceKind, Message


def chat_messages(evidence: EvidenceFile) -> list[Message]:
    """Parse a WhatsApp export (Android or iOS format, day-first dates).

    Lines that do not start a new message are appended to the previous one,
    so multi-line messages stay whole.

    Args:
        evidence: A WhatsApp export.

    Returns:
        One message per chat entry, in order.
    """
    messages: list[Message] = []
    for raw in evidence.text.splitlines():
        line = raw.strip()
        match = WHATSAPP_LINE.match(line)
        if match:
            when = make_date(int(match[3]), int(match[2]), int(match[1]))
            messages.append(Message(evidence.annexure, when, match[7].strip(), match[8].strip()))
        elif line and messages:
            last = messages[-1]
            messages[-1] = Message(last.annexure, last.when, last.sender, f"{last.text} {line}")
    return messages


def document_messages(evidence: EvidenceFile) -> list[Message]:
    """Treat each non-empty line of an email, receipt or PDF as a message.

    A line without its own date inherits the most recent date above it, which
    matches how receipts and emails are laid out.

    Args:
        evidence: A text or PDF file.

    Returns:
        One message per line.
    """
    messages: list[Message] = []
    current = None
    for raw in evidence.text.splitlines():
        line = " ".join(raw.split())
        if line:
            current = find_date(line) or current
            messages.append(Message(evidence.annexure, current, "", line))
    return messages


def messages_for(evidence: EvidenceFile) -> list[Message]:
    """Return the messages of any evidence file.

    Args:
        evidence: The file.

    Returns:
        Its messages; images have none.
    """
    if evidence.kind is EvidenceKind.WHATSAPP:
        return chat_messages(evidence)
    return [] if evidence.kind is EvidenceKind.IMAGE else document_messages(evidence)
