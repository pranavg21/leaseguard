"""Tests for leaseguard/dossier/evidence.py."""

import hashlib

import pytest

from leaseguard.constants import MAX_UPLOAD_BYTES
from leaseguard.dossier.evidence import detect_kind, load_evidence, read_text, safe_name, sha256_hex
from leaseguard.dossier.models import EvidenceKind
from leaseguard.errors import IngestError
from tests.dossier_fixtures import CHAT, PNG, RECEIPT
from tests.test_ingest import make_pdf


def test_sha256_matches_hashlib() -> None:
    assert sha256_hex(CHAT) == hashlib.sha256(CHAT).hexdigest()


@pytest.mark.parametrize(
    ("data", "kind"),
    [
        (CHAT, EvidenceKind.WHATSAPP),
        (RECEIPT, EvidenceKind.TEXT),
        (PNG, EvidenceKind.IMAGE),
        (b"\xff\xd8\xff\xe0jpeg", EvidenceKind.IMAGE),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", EvidenceKind.IMAGE),
        (make_pdf(["Paid Rs. 500"]), EvidenceKind.PDF),
    ],
)
def test_detect_kind_by_content(data: bytes, kind: EvidenceKind) -> None:
    assert detect_kind(data) is kind


@pytest.mark.parametrize(
    "data", [b"", b"a" * (MAX_UPLOAD_BYTES + 1), b"\x00\xff\xfe binary", b"RIFF\x00\x00\x00\x00WAVE\xff\xfe"]
)
def test_detect_kind_rejects_bad_files(data: bytes) -> None:
    with pytest.raises(IngestError):
        detect_kind(data)


def test_read_text_scrubs_pii_and_skips_images() -> None:
    assert "[PAN]" in read_text(b"PAN ABCDE1234F", EvidenceKind.TEXT)
    assert read_text(PNG, EvidenceKind.IMAGE) == ""
    assert "Paid" in read_text(make_pdf(["Paid Rs. 500"]), EvidenceKind.PDF)


def test_safe_name_strips_paths() -> None:
    assert safe_name("C:\\Users\\me\\chat<1>.txt") == "chat_1_.txt"
    assert safe_name("../../etc/passwd") == "passwd"
    assert safe_name("") == "file"


def test_load_evidence_labels_and_compares_hashes() -> None:
    item = load_evidence(2, "chat.txt", CHAT, sha256_hex(CHAT))
    assert item.annexure == "A-3"
    assert item.kind is EvidenceKind.WHATSAPP
    assert item.hash_matches is True
    assert item.size_bytes == len(CHAT)
