"""Tests for leaseguard/dossier/messages.py."""

from datetime import date

from leaseguard.dossier.messages import chat_messages, document_messages, messages_for
from leaseguard.dossier.models import EvidenceKind
from tests.dossier_fixtures import CHAT, RECEIPT, evidence


def test_chat_messages_handle_android_ios_and_continuations() -> None:
    messages = chat_messages(evidence(CHAT.decode(), EvidenceKind.WHATSAPP))
    assert [m.sender for m in messages] == ["Priya", "Ravi", "Ravi", "Priya"]
    assert messages[2].when == date(2026, 3, 20)
    assert messages[2].text == "I am deducting Rs. 20,000 for painting charges and cleaning."


def test_orphan_line_before_first_message_is_ignored() -> None:
    text = "Messages are end-to-end encrypted\n" + CHAT.decode()
    assert len(chat_messages(evidence(text, EvidenceKind.WHATSAPP))) == 4


def test_document_lines_inherit_the_latest_date() -> None:
    messages = document_messages(evidence(RECEIPT.decode()))
    assert messages[0].when is None
    assert messages[2].when == date(2025, 10, 1)
    assert messages[2].sender == ""


def test_messages_for_each_kind() -> None:
    assert messages_for(evidence("", EvidenceKind.IMAGE)) == []
    assert len(messages_for(evidence(CHAT.decode(), EvidenceKind.WHATSAPP))) == 4
    assert len(messages_for(evidence("a\n\nb", EvidenceKind.PDF))) == 2
