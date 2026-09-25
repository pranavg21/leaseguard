"""Fingerprint and read evidence files. Hashes are computed on the original bytes."""

import hashlib
import re

from leaseguard.constants import MAX_UPLOAD_BYTES
from leaseguard.dossier.models import EvidenceFile, EvidenceKind
from leaseguard.errors import IngestError
from leaseguard.ingest import PDF_MAGIC, pdf_text
from leaseguard.privacy import scrub_pii

IMAGE_MAGIC = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")
WEBP_TAG = slice(8, 12)
WHATSAPP_LINE = re.compile(
    r"^\[?(\d{1,2})/(\d{1,2})/(\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::\d{2})?\s*([ap]\.?\s?m\.?)?\]?\s*(?:-\s*)?"
    r"([^:\n]{1,40}):\s(.+)$",
    re.IGNORECASE,
)
_SAFE_NAME = re.compile(r"[^\w .()-]")
_MIN_CHAT_LINES = 2


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 digest of the bytes as lower-case hex.

    Args:
        data: File bytes.

    Returns:
        A 64-character hex string.
    """
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    """Strip path components and unusual characters from a file name for display.

    Args:
        name: The name the browser supplied.

    Returns:
        A short, printable file name.
    """
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return _SAFE_NAME.sub("_", base)[:80] or "file"


def detect_kind(data: bytes) -> EvidenceKind:
    """Identify a file by its content signature, never by its extension.

    Args:
        data: File bytes.

    Returns:
        The evidence kind.

    Raises:
        IngestError: If the file is empty, too large or of an unsupported type.
    """
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise IngestError("Each evidence file must be between 1 byte and 5 MB.")
    if data.startswith(PDF_MAGIC):
        return EvidenceKind.PDF
    if data.startswith(IMAGE_MAGIC) or (data.startswith(b"RIFF") and data[WEBP_TAG] == b"WEBP"):
        return EvidenceKind.IMAGE
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise IngestError("Evidence must be a PDF, an image, or a UTF-8 text/chat export.") from error
    chat_lines = sum(1 for line in text.splitlines() if WHATSAPP_LINE.match(line.strip()))
    return EvidenceKind.WHATSAPP if chat_lines >= _MIN_CHAT_LINES else EvidenceKind.TEXT


def read_text(data: bytes, kind: EvidenceKind) -> str:
    """Return the PII-scrubbed text of a file; images carry no text.

    Args:
        data: File bytes.
        kind: The detected kind.

    Returns:
        Scrubbed text, or an empty string for images.
    """
    if kind is EvidenceKind.IMAGE:
        return ""
    raw = pdf_text(data) if kind is EvidenceKind.PDF else data.decode("utf-8-sig")
    return scrub_pii(raw.replace("‎", "").replace(" ", " "))


def load_evidence(index: int, name: str, data: bytes, client_sha256: str | None) -> EvidenceFile:
    """Fingerprint and read one evidence file.

    Args:
        index: Zero-based position, used for the annexure label (A-1, A-2, ...).
        name: The file name supplied by the browser.
        data: File bytes.
        client_sha256: Hash the browser computed before upload, if any.

    Returns:
        The evidence file record.
    """
    kind = detect_kind(data)
    return EvidenceFile(
        annexure=f"A-{index + 1}",
        name=safe_name(name),
        kind=kind,
        sha256=sha256_hex(data),
        size_bytes=len(data),
        client_sha256=client_sha256,
        text=read_text(data, kind),
    )
