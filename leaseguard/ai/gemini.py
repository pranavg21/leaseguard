"""Google Gemini client using the google-genai SDK with schema-constrained JSON output."""

import logging
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import TypeAdapter, ValidationError

from leaseguard.ai.offline import OfflineClient
from leaseguard.ai.prompts import SYSTEM_INSTRUCTION, answer_prompt, classify_prompt, events_prompt, explain_prompt
from leaseguard.ai.schemas import ClassifiedClause, EventLabel, Explanation, RawAnswer, inline_schema
from leaseguard.constants import LLM_TEMPERATURE
from leaseguard.dossier.models import EventKind, Message
from leaseguard.errors import describe_error
from leaseguard.models import Category, Clause, Language

logger = logging.getLogger(__name__)

T = TypeVar("T")
_CLASSIFIED = TypeAdapter(list[ClassifiedClause])
_EXPLAINED = TypeAdapter(list[Explanation])
_ANSWER = TypeAdapter(RawAnswer)
_LABELS = TypeAdapter(list[EventLabel])


class GeminiClient:
    """Gemini implementation of :class:`leaseguard.ai.LLMClient`.

    Every call falls back to :class:`OfflineClient` if the API fails or its
    output does not match the schema, so the app never breaks on AI errors.
    """

    name = "gemini"

    def __init__(self, api_key: str, model: str, sdk: genai.Client | None = None) -> None:
        """Create a client.

        Args:
            api_key: Gemini API key.
            model: Model name, such as ``gemini-2.5-flash``.
            sdk: Optional pre-built SDK client (used in tests).
        """
        self._sdk = sdk or genai.Client(api_key=api_key)
        self._model = model
        self._fallback = OfflineClient()

    def _generate(self, prompt: str, adapter: TypeAdapter[T], operation: str) -> T | None:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=LLM_TEMPERATURE,
            response_mime_type="application/json",
            response_json_schema=inline_schema(adapter.json_schema()),
        )
        try:
            response = self._sdk.models.generate_content(model=self._model, contents=prompt, config=config)
            return adapter.validate_json(response.text or "null")
        except (errors.APIError, ValidationError, ValueError, OSError) as error:
            logger.warning("gemini_fallback", extra={"operation": operation, "error": describe_error(error)})
            return None

    def classify(self, clauses: list[Clause]) -> dict[int, Category]:
        """Classify all clauses in one call, keeping offline results for any gaps.

        Args:
            clauses: Clauses to classify.

        Returns:
            A mapping from clause index to category.
        """
        result = self._fallback.classify(clauses)
        for item in self._generate(classify_prompt(clauses), _CLASSIFIED, "classify") or []:
            if item.index in result:
                result[item.index] = item.category
        return result

    def explain(self, items: list[tuple[int, str, str]], language: Language) -> dict[int, str]:
        """Rewrite findings in plain language in one call.

        Args:
            items: (index, clause text, reason) tuples.
            language: Output language.

        Returns:
            A mapping from index to explanation; rule text is kept for any gaps.
        """
        result = self._fallback.explain(items, language)
        if items:
            for item in self._generate(explain_prompt(items, language), _EXPLAINED, "explain") or []:
                if item.index in result:
                    result[item.index] = item.explanation.strip()
        return result

    def answer(self, question: str, clauses: list[Clause], language: Language) -> RawAnswer:
        """Answer a question; the quote is verified later by the caller.

        Args:
            question: The user's question.
            clauses: Clauses that may contain the answer.
            language: Output language.

        Returns:
            The model's answer, or the offline answer if the call fails.
        """
        answer = self._generate(answer_prompt(question, clauses, language), _ANSWER, "answer")
        return answer or self._fallback.answer(question, clauses, language)

    def label_events(self, messages: list[Message], language: Language) -> dict[int, tuple[EventKind, str]]:
        """Label evidence messages in one call; keyword labels fill any gaps.

        The model only chooses the event kind and writes a summary. Quotes and
        dates always come from the deterministic parser.

        Args:
            messages: Evidence messages in order.
            language: Summary language.

        Returns:
            A mapping from message index to (event kind, summary) for relevant messages.
        """
        result = self._fallback.label_events(messages, language)
        labels = self._generate(events_prompt(messages, language), _LABELS, "label_events") if messages else None
        for label in labels or []:
            if label.index >= len(messages):
                continue
            if label.kind is None:
                result.pop(label.index, None)
            else:
                result[label.index] = (label.kind, label.summary.strip())
        return result
