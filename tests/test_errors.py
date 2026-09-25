"""Tests for leaseguard/errors.py."""

from leaseguard.errors import IngestError, LeaseGuardError, describe_error


def test_ingest_error_is_domain_error_with_code() -> None:
    error = IngestError("bad file")
    assert isinstance(error, LeaseGuardError)
    assert error.code == "invalid_document"


def test_describe_error_uses_first_line_only() -> None:
    assert describe_error(ValueError("first\nsecret second line")) == "ValueError: first"


def test_describe_error_without_message() -> None:
    assert describe_error(KeyError()) == "KeyError"
