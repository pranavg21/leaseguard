"""Tests for leaseguard/ai/offline.py."""

from leaseguard.ai.offline import OfflineClient, question_keywords
from leaseguard.models import Category, Clause, Language

CLAUSES = [
    Clause(0, "3. Security Deposit", "The Tenant shall pay a security deposit of Rs. 50,000."),
    Clause(1, "4. Notice", "Either party may terminate with a notice period of one month."),
]


def test_question_keywords_drop_stop_words() -> None:
    assert question_keywords("How much notice must I give before leaving?") == ("notice", "leaving")


def test_classify_and_explain_are_deterministic() -> None:
    client = OfflineClient()
    assert client.classify(CLAUSES)[0] is Category.DEPOSIT
    assert client.explain([(0, "t", "reason")], Language.HINDI) == {0: "reason"}


def test_answer_quotes_best_clause() -> None:
    answer = OfflineClient().answer("What notice do I need?", CLAUSES, Language.ENGLISH)
    assert answer.clause_index == 1
    assert "notice period" in answer.quote


def test_answer_empty_when_nothing_matches() -> None:
    client = OfflineClient()
    assert client.answer("pets?", CLAUSES, Language.ENGLISH).clause_index == -1
    assert client.answer("swimming pool access", CLAUSES, Language.ENGLISH).quote == ""


def test_label_events_offline() -> None:
    from leaseguard.dossier.models import EventKind, Message

    messages = [Message("A-1", None, "Ravi", "I will return your full deposit"), Message("A-1", None, "P", "Hi")]
    assert OfflineClient().label_events(messages, Language.HINDI) == {0: (EventKind.REFUND_PROMISE, "")}
