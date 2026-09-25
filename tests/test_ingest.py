"""Tests for leaseguard/ingest.py."""

import io

import pytest
from pypdf import PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from leaseguard.constants import MAX_PDF_PAGES, MAX_UPLOAD_BYTES
from leaseguard.errors import IngestError
from leaseguard.ingest import extract_text, validate_text
from leaseguard.sample import SAMPLE_LEASE


def make_pdf(lines: list[str], pages: int = 1) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    for _ in range(pages):
        for offset, line in enumerate(lines):
            pdf.drawString(40, 800 - 14 * offset, line)
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def sample_lines() -> list[str]:
    return [line[:95] for line in SAMPLE_LEASE.splitlines() if line][:12]


def test_plain_text_is_accepted() -> None:
    assert "Security Deposit" in extract_text(SAMPLE_LEASE.encode())


def test_pdf_text_is_extracted() -> None:
    assert "Security Deposit" in extract_text(make_pdf(sample_lines()))


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "empty"),
        (b"a" * (MAX_UPLOAD_BYTES + 1), "5 MB"),
        (b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 4, "Only PDF"),
        (b"%PDF-1.4 this is not really a pdf", "could not be read"),
    ],
    ids=["empty", "too_large", "png", "corrupt_pdf"],
)
def test_bad_uploads_are_rejected(data: bytes, message: str) -> None:
    with pytest.raises(IngestError, match=message):
        extract_text(data)


def test_scanned_pdf_without_text_asks_for_ocr() -> None:
    with pytest.raises(IngestError, match="OCR"):
        extract_text(make_pdf([]))


def test_too_many_pages_rejected() -> None:
    with pytest.raises(IngestError, match="pages"):
        extract_text(make_pdf(["x"], pages=MAX_PDF_PAGES + 1))


def test_encrypted_pdf_rejected() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(IngestError, match="Password"):
        extract_text(buffer.getvalue())


def test_validate_text_strips_nulls_and_truncates() -> None:
    assert "\x00" not in validate_text("a\x00" * 600)
    with pytest.raises(IngestError, match="500 characters"):
        validate_text("too short")
