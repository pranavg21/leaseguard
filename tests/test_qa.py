"""Tests for leaseguard/qa.py."""

from leaseguard.ai import OfflineClient, RawAnswer
from leaseguard.models import Clause, Language
from leaseguard.qa import NOT_FOUND, ask, heading_for

CLAUSES = [
    Clause(0, "3. Security Deposit", "The Tenant shall pay a security deposit of Rs. 50,000."),
    Clause(1, "6. Entry", "The Landlord may enter the premises with 24 hours written notice."),
]


class ScriptedClient(OfflineClient):
    def __init__(self, raw: RawAnswer) -> None:
        self.raw = raw
        self.questions: list[str] = []

    def answer(self, question: str, clauses: list[Clause], language: Language) -> RawAnswer:
        self.questions.append(question)
        return self.raw


def test_grounded_answer(client: OfflineClient) -> None:
    answer = ask("Can the landlord enter?", CLAUSES, client, Language.ENGLISH)
    assert answer.grounded
    assert answer.clause_heading == "6. Entry"


def test_hallucinated_quote_is_refused() -> None:
    fake = ScriptedClient(RawAnswer(answer="Pets allowed.", quote="Pets are allowed in the flat", clause_index=0))
    answer = ask("Are pets allowed?", CLAUSES, fake, Language.ENGLISH)
    assert not answer.grounded
    assert answer.text == NOT_FOUND


def test_question_pii_is_scrubbed_and_blank_answer_gets_default() -> None:
    fake = ScriptedClient(RawAnswer(answer="", quote="security deposit of Rs. 50,000", clause_index=7))
    answer = ask("My PAN is ABCDE1234F, what is the deposit?", CLAUSES, fake, Language.ENGLISH)
    assert "ABCDE1234F" not in fake.questions[0]
    assert answer.text == "See the quoted clause."
    assert answer.clause_heading == "3. Security Deposit"


def test_empty_inputs(client: OfflineClient) -> None:
    assert ask("   ", CLAUSES, client, Language.ENGLISH).text == NOT_FOUND
    assert ask("deposit?", [], client, Language.ENGLISH).text == NOT_FOUND


def test_heading_for_prefers_claimed_clause() -> None:
    assert heading_for("security deposit of Rs. 50,000", CLAUSES, 0) == "3. Security Deposit"
    assert heading_for("not in any clause at all", CLAUSES, 0) is None
