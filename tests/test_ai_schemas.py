"""Tests for leaseguard/ai/schemas.py."""

import pytest
from pydantic import ValidationError

from leaseguard.ai.schemas import NO_ANSWER, ClassifiedClause, Explanation, RawAnswer
from leaseguard.models import Category


def test_classified_clause_validates_category() -> None:
    assert ClassifiedClause.model_validate({"index": 1, "category": "deposit"}).category is Category.DEPOSIT
    with pytest.raises(ValidationError):
        ClassifiedClause.model_validate({"index": 1, "category": "made_up"})
    with pytest.raises(ValidationError):
        ClassifiedClause.model_validate({"index": -1, "category": "deposit"})


def test_explanation_requires_text() -> None:
    with pytest.raises(ValidationError):
        Explanation.model_validate({"index": 0, "explanation": ""})


def test_raw_answer_defaults_and_ignores_extra_fields() -> None:
    assert RawAnswer() == NO_ANSWER
    assert RawAnswer.model_validate({"answer": "a", "unexpected": 1}).clause_index == -1


def test_inline_schema_removes_references() -> None:
    from pydantic import TypeAdapter

    from leaseguard.ai.schemas import inline_schema

    schema = inline_schema(TypeAdapter(list[ClassifiedClause]).json_schema())
    assert "$ref" not in str(schema)
    assert "$defs" not in str(schema)
    assert "deposit" in str(schema)
    assert inline_schema({"type": "string"}) == {"type": "string"}
    assert inline_schema({"$defs": [], "type": "object"}) == {"type": "object"}


def test_event_label_accepts_null_kind() -> None:
    from leaseguard.ai.schemas import EventLabel

    assert EventLabel.model_validate({"index": 0, "kind": None}).kind is None
    with pytest.raises(ValidationError):
        EventLabel.model_validate({"index": 0, "kind": "bribe"})


def test_all_schemas_use_shared_base_class() -> None:
    from leaseguard.ai.schemas import ClassifiedClause, EventLabel, Explanation, RawAnswer, _IgnoreExtra

    for schema_cls in (ClassifiedClause, Explanation, RawAnswer, EventLabel):
        assert issubclass(schema_cls, _IgnoreExtra)
        assert schema_cls.model_config.get("extra") == "ignore"
