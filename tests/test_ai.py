"""Tests for leaseguard/ai/__init__.py (client selection)."""

import pytest

from leaseguard.ai import OfflineClient, get_client
from leaseguard.ai.gemini import GeminiClient


def test_offline_without_key() -> None:
    assert isinstance(get_client(), OfflineClient)


def test_gemini_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    client = get_client()
    assert isinstance(client, GeminiClient)
    assert client.name == "gemini"
