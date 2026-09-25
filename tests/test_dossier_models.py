"""Tests for leaseguard/dossier/__init__.py and leaseguard/dossier/models.py."""

import leaseguard.dossier
from leaseguard.dossier.models import EVENT_TITLES, EventKind, EvidenceFile, EvidenceKind, Ledger


def test_package_documents_purpose() -> None:
    assert "dossier" in (leaseguard.dossier.__doc__ or "")


def test_every_event_kind_has_a_title() -> None:
    assert set(EVENT_TITLES) == set(EventKind)


def test_hash_match_states() -> None:
    base = EvidenceFile("A-1", "f", EvidenceKind.TEXT, "ab" * 32, 1, None, "")
    assert base.hash_matches is None
    assert EvidenceFile("A-1", "f", EvidenceKind.TEXT, "ab" * 32, 1, "AB" * 32, "").hash_matches is True
    assert EvidenceFile("A-1", "f", EvidenceKind.TEXT, "ab" * 32, 1, "cd" * 32, "").hash_matches is False


def test_ledger_outstanding() -> None:
    assert Ledger(50_000, "x", 10_000, 20_000).outstanding == 40_000
    assert Ledger(10_000, "x", 20_000, 0).outstanding == 0
    assert Ledger(None, "x", 0, 0).outstanding is None
