"""Pydantic schemas for model output. Every response is validated before use."""

from pydantic import BaseModel, ConfigDict, Field

from leaseguard.constants import LLM_EXPLANATION_MAX_CHARS, LLM_SUMMARY_MAX_CHARS, MAX_QUOTE_CHARS
from leaseguard.dossier.models import EventKind
from leaseguard.models import Category


class _IgnoreExtra(BaseModel):
    """Base model that silently drops fields the schema does not declare."""

    model_config = ConfigDict(extra="ignore")


class ClassifiedClause(_IgnoreExtra):
    """One clause classification returned by the model."""

    index: int = Field(ge=0)
    category: Category


class Explanation(_IgnoreExtra):
    """One plain-language explanation returned by the model."""

    index: int = Field(ge=0)
    explanation: str = Field(min_length=1, max_length=LLM_EXPLANATION_MAX_CHARS)


class RawAnswer(_IgnoreExtra):
    """An unverified answer; the quote is checked by :mod:`leaseguard.qa`."""

    answer: str = ""
    quote: str = Field(default="", max_length=MAX_QUOTE_CHARS)
    clause_index: int = -1


NO_ANSWER = RawAnswer()


class EventLabel(_IgnoreExtra):
    """The model's reading of one evidence message. The quote and date never come from here."""

    index: int = Field(ge=0)
    kind: EventKind | None
    summary: str = Field(default="", max_length=LLM_SUMMARY_MAX_CHARS)



def _resolve(node: object, definitions: dict[str, object]) -> object:
    if isinstance(node, list):
        return [_resolve(item, definitions) for item in node]
    if not isinstance(node, dict):
        return node
    reference = node.get("$ref")
    if isinstance(reference, str):
        return _resolve(definitions[reference.rsplit("/", 1)[-1]], definitions)
    return {key: _resolve(value, definitions) for key, value in node.items() if key != "$defs"}


def inline_schema(schema: dict[str, object]) -> dict[str, object]:
    """Replace every ``$ref`` with its definition so the schema is self-contained.

    Gemini's structured output has limited support for references, so the
    schema sent with each request contains none.

    Args:
        schema: A JSON schema, possibly with ``$defs`` and ``$ref``.

    Returns:
        An equivalent schema without references.
    """
    definitions = schema.get("$defs", {})
    resolved = _resolve(schema, definitions if isinstance(definitions, dict) else {})
    return resolved if isinstance(resolved, dict) else {}
