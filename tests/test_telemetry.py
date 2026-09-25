"""Tests for leaseguard/telemetry.py."""

import json

import pytest

from leaseguard.ai import OfflineClient
from leaseguard.engine import analyse
from leaseguard.models import UserContext
from leaseguard.sample import SAMPLE_LEASE
from leaseguard.telemetry import FirestoreRecorder, NullRecorder, analysis_event, get_recorder


class FakeCollection:
    def __init__(self, fail: bool = False) -> None:
        self.docs: list[dict[str, object]] = []
        self.fail = fail

    def add(self, document_data: dict[str, object]) -> object:
        if self.fail:
            raise RuntimeError("firestore down")
        self.docs.append(document_data)
        return None


class FakeFirestore:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection_obj = collection
        self.names: list[str] = []

    def collection(self, collection_path: str) -> FakeCollection:
        self.names.append(collection_path)
        return self.collection_obj


def test_event_is_anonymous(client: OfflineClient, tenant_ctx: UserContext) -> None:
    event = analysis_event(analyse(SAMPLE_LEASE, tenant_ctx, client), "offline")
    serialised = json.dumps(event)
    assert event["counts"] == {"FAIR": 4, "MEDIUM": 1, "HIGH": 5}
    assert "Tenant shall" not in serialised
    assert "2,50,000" not in serialised


def test_firestore_recorder_writes_and_survives_failures() -> None:
    good = FakeCollection()
    FirestoreRecorder("metrics", FakeFirestore(good)).record({"a": 1})
    assert good.docs == [{"a": 1}]
    FirestoreRecorder("metrics", FakeFirestore(FakeCollection(fail=True))).record({"a": 1})


def test_recorder_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    assert isinstance(get_recorder(), NullRecorder)
    NullRecorder().record({"ignored": True})
    monkeypatch.setenv("FIRESTORE_COLLECTION", "metrics")
    monkeypatch.setattr("leaseguard.telemetry.FirestoreRecorder", lambda name: ("firestore", name))
    assert get_recorder() == ("firestore", "metrics")


def test_firestore_client_is_created_when_not_injected(monkeypatch: pytest.MonkeyPatch) -> None:
    from google.cloud import firestore

    fake = FakeFirestore(FakeCollection())
    monkeypatch.setattr(firestore, "Client", lambda: fake)
    FirestoreRecorder("metrics").record({"a": 1})
    assert fake.names == ["metrics"]
