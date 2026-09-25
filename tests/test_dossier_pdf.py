"""Tests for leaseguard/dossier/pdf.py."""

import io
from datetime import date

from pypdf import PdfReader

from leaseguard.ai import OfflineClient
from leaseguard.dossier.pdf import annexures, build_dossier_pdf
from leaseguard.dossier.service import Upload, build_dossier
from leaseguard.models import Language
from tests.dossier_fixtures import CHAT, PARTIES, PNG


def test_pdf_contains_every_section() -> None:
    dossier = build_dossier(
        [Upload("chat.txt", CHAT, None), Upload("p.png", PNG, None)], None, PARTIES, OfflineClient(), Language.ENGLISH
    )
    data = build_dossier_pdf(dossier, date(2026, 9, 24))
    reader = PdfReader(io.BytesIO(data))
    text = " ".join(page.extract_text() for page in reader.pages)
    for expected in (
        "Index of annexures",
        "List of dates",
        "Contradiction",
        "three years",
        "63(4)(c)",
        "Demand notice",
        "To do:",
    ):
        assert expected in text
    assert reader.metadata is not None
    assert reader.metadata.title == "LeaseGuard deposit-recovery dossier"
    assert annexures(dossier.contradictions[0]) == "A-1"


def test_pdf_with_undated_event_marks_date_needed() -> None:
    dossier = build_dossier(
        [Upload("n.txt", b"I have vacated the flat.", None)], None, PARTIES, OfflineClient(), Language.ENGLISH
    )
    text = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(build_dossier_pdf(dossier, date(2026, 1, 1)))).pages)
    assert "DATE NEEDED" in " ".join(text.split())
