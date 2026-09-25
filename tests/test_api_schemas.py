"""Tests for leaseguard/api/schemas.py."""

import base64

import pytest
from pydantic import ValidationError

from leaseguard.api.schemas import AnalyzeRequest, AskRequest, ContextIn, DocumentIn
from leaseguard.errors import IngestError
from leaseguard.models import Language, Role
from leaseguard.sample import SAMPLE_LEASE


def test_context_defaults_and_conversion() -> None:
    ctx = ContextIn(role=Role.LANDLORD, state="Kerala", monthly_rent=15000, language=Language.MARATHI).to_context()
    assert ctx.role is Role.LANDLORD
    assert ctx.monthly_rent == 15000
    assert ContextIn().to_context().state == "Other"


@pytest.mark.parametrize(
    "payload",
    [{"state": "Atlantis"}, {"monthly_rent": 0}, {"role": "agent"}, {"language": "French"}, {"extra": 1}],
)
def test_context_rejects_invalid_values(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ContextIn.model_validate(payload)


def test_document_requires_exactly_one_source() -> None:
    with pytest.raises(ValidationError):
        DocumentIn()
    with pytest.raises(ValidationError):
        DocumentIn(text="a", file_base64="YQ==")


def test_document_resolves_text_and_base64() -> None:
    assert "Security Deposit" in DocumentIn(text=SAMPLE_LEASE).resolve()
    encoded = base64.b64encode(SAMPLE_LEASE.encode()).decode()
    assert "Security Deposit" in DocumentIn(file_base64=encoded).resolve()
    with pytest.raises(IngestError, match="decoded"):
        DocumentIn(file_base64="not base64!").resolve()


def test_request_models() -> None:
    body = {"document": {"text": "x"}, "question": "q"}
    assert AskRequest.model_validate(body).question == "q"
    with pytest.raises(ValidationError):
        AskRequest.model_validate({**body, "question": ""})
    assert AnalyzeRequest.model_validate({"document": {"text": "x"}}).context.role is Role.TENANT
