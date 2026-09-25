"""Tests for leaseguard/dossier/service.py and leaseguard/sample_evidence.py."""

import pytest

from leaseguard.ai import OfflineClient
from leaseguard.constants import MAX_EVIDENCE_FILES, MAX_EVIDENCE_TOTAL_BYTES
from leaseguard.dossier import evidence as evidence_module
from leaseguard.dossier import service as service_module
from leaseguard.dossier.evidence import sha256_hex
from leaseguard.dossier.models import EventKind, Message
from leaseguard.dossier.service import Upload, build_dossier, cached_dossier, extract_events, load_files
from leaseguard.errors import ExpiredError, IngestError
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


class CountingLabeller(OfflineClient):
    """Counts AI labelling calls."""

    def __init__(self) -> None:
        self.calls = 0

    def label_events(self, messages: list[Message], language: Language) -> dict[int, tuple[EventKind, str]]:
        self.calls += 1
        return super().label_events(messages, language)


def test_identical_inputs_reuse_the_cached_dossier() -> None:
    from leaseguard.dossier.service import dossier_key

    client = CountingLabeller()
    uploads = [Upload("chat.txt", CHAT, None)]
    first = build_dossier(uploads, None, PARTIES, client, Language.ENGLISH)
    second = build_dossier(uploads, None, PARTIES, client, Language.ENGLISH)
    assert first is second
    assert client.calls == 1
    changed = [Upload("chat.txt", CHAT + b"\n", None)]
    assert dossier_key(changed, None, PARTIES, Language.ENGLISH) != dossier_key(
        uploads, None, PARTIES, Language.ENGLISH
    )
    build_dossier(uploads, None, PARTIES, client, Language.HINDI)
    assert client.calls == 2


def test_each_file_is_hashed_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    hashed: list[bytes] = []

    def counting(data: bytes) -> str:
        hashed.append(data)
        return sha256_hex(data)

    monkeypatch.setattr(service_module, "sha256_hex", counting)
    monkeypatch.setattr(evidence_module, "sha256_hex", counting)
    uploads = [Upload("chat.txt", CHAT, None), Upload("receipt.txt", RECEIPT, None)]
    dossier = build_dossier(uploads, None, PARTIES, OfflineClient(), Language.ENGLISH)
    assert sorted(hashed) == sorted([CHAT, RECEIPT])
    assert dossier.files[0].sha256 == sha256_hex(CHAT)


def test_total_evidence_size_is_limited() -> None:
    half = MAX_EVIDENCE_TOTAL_BYTES // 2 + 1
    with pytest.raises(IngestError, match="5 MB in total"):
        load_files([Upload("a.txt", b"a" * half, None), Upload("b.txt", b"b" * half, None)])


def test_cached_dossier_by_id_and_stored_steps() -> None:
    dossier = build_dossier([Upload("chat.txt", CHAT, None)], None, PARTIES, OfflineClient(), Language.ENGLISH)
    assert cached_dossier(dossier.dossier_id) is dossier
    assert dossier.next_steps[-1].title == "Get free legal help if you are eligible"
    with pytest.raises(ExpiredError):
        cached_dossier("c" * 64)
