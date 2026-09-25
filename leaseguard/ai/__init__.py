"""Language-model access behind a small interface, with a deterministic fallback.

The model does three things only: classify clauses (one batched call), write
plain-language explanations (one batched call, optionally translated) and
answer questions. Ratings, grounding, PII scrubbing and the coverage audit
are deterministic code.
"""

import logging
from typing import Protocol

from leaseguard.ai.offline import OfflineClient
from leaseguard.ai.schemas import RawAnswer
from leaseguard.config import get_settings
from leaseguard.dossier.models import EventKind, Message
from leaseguard.models import Category, Clause, Language

logger = logging.getLogger(__name__)

Explainable = tuple[int, str, str]


class LLMClient(Protocol):
    """Operations the pipeline needs from a language model."""

    name: str

    def classify(self, clauses: list[Clause]) -> dict[int, Category]:
        """Map each clause index to a category."""
        ...

    def explain(self, items: list[Explainable], language: Language) -> dict[int, str]:
        """Map each (index, clause text, reason) item to a plain-language explanation."""
        ...

    def answer(self, question: str, clauses: list[Clause], language: Language) -> RawAnswer:
        """Answer a question from the clauses, with a claimed supporting quote."""
        ...

    def label_events(self, messages: list[Message], language: Language) -> dict[int, tuple[EventKind, str]]:
        """Map relevant evidence-message indexes to an event kind and a short summary."""
        ...


def get_client() -> LLMClient:
    """Return a Gemini client when a key is configured, otherwise the offline client.

    Returns:
        A client implementing :class:`LLMClient`.
    """
    settings = get_settings()
    if settings.gemini_api_key:
        from leaseguard.ai.gemini import GeminiClient  # noqa: PLC0415 - optional dependency, loaded on demand

        return GeminiClient(settings.gemini_api_key, settings.gemini_model)
    logger.info("ai_mode_offline")
    return OfflineClient()


__all__ = ["Explainable", "LLMClient", "OfflineClient", "RawAnswer", "get_client"]
