"""Tests for leaseguard/ai/gemini.py using a fake SDK: offline and deterministic."""

import json
from types import SimpleNamespace

from google.genai import errors

from leaseguard.ai.gemini import GeminiClient
from leaseguard.dossier.models import EventKind, Message
from leaseguard.models import Category, Clause, Language

CLAUSES = [
    Clause(0, "3. Security Deposit", "The Tenant shall pay a security deposit of Rs. 50,000."),
    Clause(1, "9. Use", "The premises shall be used for residential purposes only."),
]


class FakeModels:
    def __init__(self, payload: object = None, error: Exception | None = None) -> None:
        self.payload, self.error, self.calls = payload, error, []

    def generate_content(self, model: str, contents: str, config: object) -> SimpleNamespace:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.error:
            raise self.error
        return SimpleNamespace(text=json.dumps(self.payload))


def make(payload: object = None, error: Exception | None = None) -> tuple[GeminiClient, FakeModels]:
    models = FakeModels(payload, error)
    sdk = SimpleNamespace(models=models)
    return GeminiClient("key", "gemini-test", sdk=sdk), models  # type: ignore[arg-type]


def test_classify_uses_schema_and_ignores_unknown_indexes() -> None:
    client, models = make([{"index": 1, "category": "maintenance"}, {"index": 9, "category": "deposit"}])
    assert client.classify(CLAUSES) == {0: Category.DEPOSIT, 1: Category.MAINTENANCE}
    config = models.calls[0]["config"]
    assert config.temperature == 0
    assert config.response_json_schema["type"] == "array"
    assert "<document>" in models.calls[0]["contents"]


def test_invalid_output_falls_back() -> None:
    client, _ = make([{"index": 0, "category": "made_up"}])
    assert client.classify(CLAUSES)[0] is Category.DEPOSIT


def test_api_error_falls_back() -> None:
    client, _ = make(error=errors.APIError(503, {"error": {"message": "unavailable"}}))
    assert client.classify(CLAUSES)[1] is Category.OTHER
    assert client.explain([(0, "t", "reason")], Language.ENGLISH) == {0: "reason"}
    assert client.answer("How much is the deposit?", CLAUSES, Language.ENGLISH).clause_index == 0


def test_explain_merges_translations() -> None:
    client, models = make([{"index": 0, "explanation": "  सरल भाषा  "}, {"index": 5, "explanation": "x"}])
    assert client.explain([(0, "t", "reason"), (1, "t", "other")], Language.HINDI) == {0: "सरल भाषा", 1: "other"}
    assert client.explain([], Language.HINDI) == {}
    assert len(models.calls) == 1


def test_answer_returns_model_answer() -> None:
    client, _ = make({"answer": "Rs. 50,000", "quote": "security deposit of Rs. 50,000", "clause_index": 0})
    assert client.answer("deposit?", CLAUSES, Language.ENGLISH).answer == "Rs. 50,000"


MESSAGES = [
    Message("A-1", None, "Ravi", "I will return your full deposit"),
    Message("A-1", None, "Priya", "Keys are with the guard"),
    Message("A-1", None, "Ravi", "Paint is peeling"),
]


def test_label_events_merges_model_labels() -> None:
    payload = [
        {"index": 0, "kind": None},
        {"index": 1, "kind": "move_out", "summary": " Tenant handed over keys "},
        {"index": 9, "kind": "refund"},
    ]
    client, models = make(payload)
    labels = client.label_events(MESSAGES, Language.ENGLISH)
    assert labels == {1: (EventKind.MOVE_OUT, "Tenant handed over keys")}
    assert "<document>" in models.calls[0]["contents"]


def test_label_events_falls_back_and_skips_empty_input() -> None:
    client, models = make(error=errors.APIError(500, {"error": {"message": "down"}}))
    assert client.label_events(MESSAGES, Language.ENGLISH) == {0: (EventKind.REFUND_PROMISE, "")}
    assert client.label_events([], Language.ENGLISH) == {}
    assert len(models.calls) == 1
