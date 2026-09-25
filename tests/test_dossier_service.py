"""Tests for leaseguard/dossier/service.py and leaseguard/sample_evidence.py."""

import pytest

from leaseguard.ai import OfflineClient
from leaseguard.constants import MAX_EVIDENCE_FILES
from leaseguard.dossier.evidence import sha256_hex
from leaseguard.dossier.models import EventKind, Message
from leaseguard.dossier.service import Upload, build_dossier, extract_events, load_files
from leaseguard.errors import IngestError
from leaseguard.models import Language
from leaseguard.sample import SAMPLE_LEASE
from leaseguard.sample_evidence import SAMPLE_EVIDENCE
from tests.dossier_fixtures import CHAT, PARTIES, PNG, RECEIPT


class InventingClient(OfflineClient):
    """Pretends the model labelled a message whose text is not in the evidence."""

    def label_events(self, messages: list[Message], language: Language) -> dict[int, tuple[EventKind, str]]:
        return {0: (EventKind.REFUND, "invented")}


def test_load_files_limits() -> None:
    with pytest.raises(IngestError):
        load_files([])
    with pytest.raises(IngestError):
        load_files([Upload("a.txt", b"a", None)] * (MAX_EVIDENCE_FILES + 1))


def test_full_dossier_from_chat_receipt_and_image() -> None:
    uploads = [Upload("chat.txt", CHAT, sha256_hex(CHAT)), Upload("r.txt", RECEIPT, None), Upload("p.png", PNG, None)]
    dossier = build_dossier(uploads, SAMPLE_LEASE, PARTIES, OfflineClient(), Language.ENGLISH)
    kinds = [e.kind for e in dossier.events]
    assert kinds[0] is EventKind.PAYMENT
    assert EventKind.DEDUCTION_CLAIM in kinds
    assert dossier.ledger.deposit == 250_000
    assert len(dossier.contradictions) == 1
    assert dossier.limitation_deadline is not None
    assert any("Images" in item for item in dossier.checklist)


def test_out_of_range_labels_are_ignored() -> None:
    files = load_files([Upload("note.txt", b"nothing relevant", None)])

    class FarClient(OfflineClient):
        def label_events(self, messages: list[Message], language: Language) -> dict[int, tuple[EventKind, str]]:
            return {99: (EventKind.REFUND, ""), -1: (EventKind.REFUND, "")}

    assert extract_events(files, FarClient(), Language.ENGLISH) == []


def test_events_not_found_verbatim_are_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    files = load_files([Upload("chat.txt", CHAT, None)])
    forged = [Message("A-1", None, "Ravi", "I have refunded everything")]
    monkeypatch.setattr("leaseguard.dossier.service.messages_for", lambda _: forged)
    assert extract_events(files, InventingClient(), Language.ENGLISH) == []


def test_sample_evidence_produces_a_complete_timeline() -> None:
    uploads = [Upload(name, text.encode(), None) for name, text in SAMPLE_EVIDENCE.items()]
    dossier = build_dossier(uploads, SAMPLE_LEASE, PARTIES, OfflineClient(), Language.ENGLISH)
    assert dossier.checklist == []
    assert {e.kind for e in dossier.events} == set(EventKind) - {EventKind.REFUND}
