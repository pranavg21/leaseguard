"""Tests for leaseguard/export.py."""

import io

from pypdf import PdfReader

from leaseguard.ai import OfflineClient
from leaseguard.engine import analyse
from leaseguard.export import build_packet
from leaseguard.models import AnalysisReport, UserContext
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED


def pdf_text(data: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(data)).pages)


def test_packet_lists_flagged_clauses_and_notes(client: OfflineClient, tenant_ctx: UserContext) -> None:
    data = build_packet(analyse(SAMPLE_LEASE, tenant_ctx, client))
    text = pdf_text(data)
    assert data.startswith(b"%PDF-")
    assert "HIGH RISK" in text
    assert "Question for your lawyer" in text
    assert "Maharashtra" in text
    meta = PdfReader(io.BytesIO(data)).metadata
    assert meta is not None and meta.title == "LeaseGuard consultation packet"


def test_packet_without_flags_and_with_skipped_audit(client: OfflineClient, tenant_ctx: UserContext) -> None:
    report = analyse(SAMPLE_LEASE_REVISED, tenant_ctx, client)
    fair_only = AnalysisReport([f for f in report.findings if f.risk.rank == 0], [], False, tenant_ctx)
    text = pdf_text(build_packet(fair_only))
    assert "No clauses were flagged" in text
    assert "Coverage audit skipped" in text
