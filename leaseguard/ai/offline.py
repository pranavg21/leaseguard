"""Deterministic, network-free client used without an API key and as a fallback."""

import re

from leaseguard.ai.schemas import NO_ANSWER, RawAnswer
from leaseguard.classifier import classify_all
from leaseguard.constants import MIN_KEYWORD_CHARS
from leaseguard.dossier.events import classify_message
from leaseguard.dossier.models import EventKind, Message
from leaseguard.grounding import best_sentence
from leaseguard.models import Category, Clause, Language

_STOP_WORDS = frozenset(
    [
        "what",
        "when",
        "does",
        "much",
        "have",
        "will",
        "with",
        "this",
        "that",
        "there",
        "lease",
        "agreement",
        "clause",
        "about",
        "which",
        "should",
        "could",
        "would",
        "they",
        "must",
        "give",
        "before",
        "after",
        "shall",
        "need",
        "many",
        "long",
        "from",
        "your",
        "mine",
        "landlord",
        "tenant",
        "flat",
        "premises",
        "property",
    ]
)


def question_keywords(question: str) -> tuple[str, ...]:
    """Return the meaningful words of a question.

    Args:
        question: The user's question.

    Returns:
        Lower-case words of at least four letters that are not stop words.
    """
    words = re.findall(rf"[a-z]{{{MIN_KEYWORD_CHARS},}}", question.lower())
    return tuple(w for w in words if w not in _STOP_WORDS)


class OfflineClient:
    """Keyword-based implementation of :class:`leaseguard.ai.LLMClient`."""

    name = "offline"

    def classify(self, clauses: list[Clause]) -> dict[int, Category]:
        """Classify clauses with the keyword classifier.

        Args:
            clauses: Clauses to classify.

        Returns:
            A mapping from clause index to category.
        """
        return classify_all(clauses)

    def explain(self, items: list[tuple[int, str, str]], language: Language) -> dict[int, str]:
        """Return each rule explanation unchanged (translation needs Gemini).

        Args:
            items: (index, clause text, reason) tuples.
            language: Requested language (unused offline).

        Returns:
            A mapping from index to the original reason.
        """
        del language
        return {index: reason for index, _text, reason in items}

    def answer(self, question: str, clauses: list[Clause], language: Language) -> RawAnswer:
        """Find the clause that best matches the question and quote it.

        Args:
            question: The user's question.
            clauses: Clauses to search.
            language: Requested language (unused offline).

        Returns:
            A candidate answer, or an empty answer if nothing matches.
        """
        del language
        words = question_keywords(question)
        scored = [(sum(c.text.lower().count(w) for w in words), c) for c in clauses]
        score, best = max(scored, key=lambda pair: pair[0], default=(0, None))
        if best is None or score == 0:
            return NO_ANSWER
        return RawAnswer(
            answer=f"Your agreement addresses this in '{best.heading}'.",
            quote=best_sentence(best.text, words),
            clause_index=best.index,
        )

    def label_events(self, messages: list[Message], language: Language) -> dict[int, tuple[EventKind, str]]:
        """Label evidence messages with the keyword rules (no summaries offline).

        Args:
            messages: Evidence messages in order.
            language: Summary language (unused offline).

        Returns:
            A mapping from message index to (event kind, summary) for relevant messages.
        """
        del language
        return {i: (kind, "") for i, m in enumerate(messages) if (kind := classify_message(m.text)) is not None}
