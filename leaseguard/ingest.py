"""Safe document ingestion: signature checks, size limits and text extraction."""

import io
import logging

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from leaseguard.constants import MAX_PDF_PAGES, MAX_TEXT_CHARS, MAX_UPLOAD_BYTES, MIN_TEXT_CHARS, PRINTABLE_RATIO
from leaseguard.errors import IngestError

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"


def extract_text(data: bytes) -> str:
    """Validate an upload by its content (never its extension) and return its text.

    Args:
        data: Raw file bytes.

    Returns:
        Normalised document text.

    Raises:
        IngestError: If the file is empty, too large, unsupported, encrypted,
            damaged, a scan without a text layer, or too short.
    """
    if not data:
        raise IngestError("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise IngestError("The file is larger than 5 MB. Please upload a smaller file.")
    if data.startswith(PDF_MAGIC):
        return validate_text(pdf_text(data))
    if _is_text(data):
        return validate_text(data.decode("utf-8"))
    logger.info("upload_rejected", extra={"reason": "unsupported_signature"})
    raise IngestError("Only PDF or plain-text files are supported.")


def validate_text(text: str) -> str:
    """Normalise pasted or extracted text and enforce length limits.

    Args:
        text: Candidate document text.

    Returns:
        The stripped text, truncated to the maximum supported length.

    Raises:
        IngestError: If the text is too short to be an agreement.
    """
    cleaned = text.replace("\x00", "").strip()
    if len(cleaned) < MIN_TEXT_CHARS:
        raise IngestError(
            "Very little text was found (under 500 characters). If this is a scanned "
            "stamp-paper copy, run OCR first or paste the text instead."
        )
    return cleaned[:MAX_TEXT_CHARS]


def _is_text(data: bytes) -> bool:
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    printable = sum(ch.isprintable() or ch in "\n\r\t" for ch in decoded)
    return printable / len(decoded) > PRINTABLE_RATIO


def pdf_text(data: bytes) -> str:
    """Extract the text layer of a PDF after encryption and page-count checks.

    Args:
        data: PDF bytes.

    Returns:
        The text of every page, joined by newlines.

    Raises:
        IngestError: If the PDF is encrypted, too long or damaged.
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise IngestError("Password-protected PDFs are not supported.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise IngestError(f"PDFs are limited to {MAX_PDF_PAGES} pages.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as exc:
        raise IngestError("The PDF could not be read. It may be damaged.") from exc
