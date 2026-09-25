"""Tests for leaseguard/config.py."""

import pytest

from leaseguard.config import DEFAULT_MODEL, get_settings


def test_defaults_without_environment() -> None:
    settings = get_settings()
    assert settings.gemini_api_key is None
    assert not settings.llm_enabled
    assert settings.gemini_model == DEFAULT_MODEL
    assert settings.firestore_collection is None


def test_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "  key  ")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-x")
    monkeypatch.setenv("FIRESTORE_COLLECTION", "metrics")
    settings = get_settings()
    assert settings.gemini_api_key == "key"
    assert settings.llm_enabled
    assert settings.gemini_model == "gemini-x"
    assert settings.firestore_collection == "metrics"


def test_blank_values_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    assert get_settings().gemini_api_key is None
