"""Grounded question answering: every answer must cite a verified quote."""

from leaseguard.ai import LLMClient
from leaseguard.grounding import NormalisedText, verify_grounding
from leaseguard.models import Answer, Clause, Language
from leaseguard.privacy import scrub_pii

NOT_FOUND = "Not stated in your agreement. Consider asking the other party or a lawyer."
_NO_ANSWER = Answer(NOT_FOUND, None, None, grounded=False)


def heading_for(quote: str, clauses: list[Clause], claimed_index: int) -> str | None:
    """Find the heading of the clause a quote came from.

    Args:
        quote: A verified quote.
        clauses: All clauses.
        claimed_index: The clause index the model claimed, or -1.

    Returns:
        The heading of the claimed clause if it contains the quote, else of the
        first clause that does, else None.
    """
    containing = [c for c in clauses if verify_grounding(quote, c.text)]
    claimed = [c for c in containing if c.index == claimed_index]
    chosen = claimed or containing
    return chosen[0].heading if chosen else None


def ask(question: str, clauses: list[Clause], client: LLMClient, language: Language) -> Answer:
    """Answer a question, refusing if the supporting quote cannot be verified.

    Args:
        question: The user's question (PII is scrubbed before use).
        clauses: Clauses of the scrubbed agreement.
        client: AI client that proposes an answer and quote.
        language: Output language.

    Returns:
        A grounded answer, or the "not stated" answer.
    """
    cleaned = scrub_pii(question.strip())
    if not cleaned or not clauses:
        return _NO_ANSWER
    raw = client.answer(cleaned, clauses, language)
    source = NormalisedText("\n".join(clause.text for clause in clauses))
    if not verify_grounding(raw.quote, source):
        return _NO_ANSWER
    text = raw.answer.strip() or "See the quoted clause."
    return Answer(text, raw.quote.strip(), heading_for(raw.quote, clauses, raw.clause_index), grounded=True)
