"""Integration tests for every endpoint in leaseguard/api/routes.py."""

import base64

import pytest
from fastapi.testclient import TestClient

import leaseguard.api
from leaseguard.api.routes import router
from leaseguard.api.schemas import DocumentIn
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED
from tests.conftest import MemoryRecorder

JSON = dict[str, object]


def test_router_exposes_every_endpoint() -> None:
    assert leaseguard.api.__doc__
    paths = {getattr(route, "path", "") for route in router.routes}
    assert paths == {f"/api/{name}" for name in ("health", "meta", "sample", "analyze", "ask", "compare", "packet")}


def test_health_meta_sample(api: TestClient) -> None:
    assert api.get("/api/health").json()["status"] == "ok"
    meta = api.get("/api/meta").json()
    assert meta["roles"] == ["tenant", "landlord"]
    assert "Maharashtra" in meta["states"]
    assert meta["ai_mode"] == "offline"
    assert api.get("/api/sample").json()["revised"] == SAMPLE_LEASE_REVISED


def test_analyze_records_anonymous_metrics(api: TestClient, sample_body: JSON, recorder: MemoryRecorder) -> None:
    body = api.post("/api/analyze", json=sample_body).json()
    assert body["counts"]["HIGH"] == 5
    assert body["coverage_complete"]
    assert len(recorder.events) == 1
    assert "Tenant" not in str(recorder.events[0])


def test_analyze_accepts_base64_file(api: TestClient) -> None:
    encoded = base64.b64encode(SAMPLE_LEASE.encode()).decode()
    assert api.post("/api/analyze", json={"document": {"file_base64": encoded}}).status_code == 200


def test_ask(api: TestClient, sample_body: JSON) -> None:
    answer = api.post("/api/ask", json={**sample_body, "question": "Can the landlord enter?"}).json()
    assert answer["grounded"]
    assert answer["heading"] == "6. Entry"


def test_compare(api: TestClient) -> None:
    body = {"original": {"text": SAMPLE_LEASE}, "revised": {"text": SAMPLE_LEASE_REVISED}}
    changes = api.post("/api/compare", json=body).json()["changes"]
    assert {c["direction"] for c in changes} == {"better", "same"}


def test_packet(api: TestClient, sample_body: JSON) -> None:
    response = api.post("/api/packet", json=sample_body)
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_document_errors_are_structured(api: TestClient) -> None:
    response = api.post("/api/analyze", json={"document": {"text": "too short"}})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_document"


def test_validation_errors_do_not_echo_input(api: TestClient) -> None:
    response = api.post("/api/analyze", json={"document": {"text": "<script>alert(1)</script>", "file_base64": "x"}})
    assert response.status_code == 422
    assert "script" not in response.text


def test_analyze_returns_key_terms_and_next_steps(api: TestClient, sample_body: JSON) -> None:
    body = api.post("/api/analyze", json=sample_body).json()
    assert body["key_terms"][0] == {
        "label": "Monthly rent",
        "value": "Rs. 25,000",
        "quote": "2. Rent: The Tenant shall pay a monthly rent of Rs. 25,000 on or before the 5th of every month.",
    }
    assert body["next_steps"][-1]["title"] == "Get free legal help if you are eligible"


def test_follow_ups_by_report_id_skip_the_document(
    api: TestClient, sample_body: JSON, recorder: MemoryRecorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_id = api.post("/api/analyze", json=sample_body).json()["report_id"]
    assert isinstance(report_id, str)
    assert len(report_id) == 64

    def never_parse(_: DocumentIn) -> str:
        raise AssertionError("the document must not be decoded again")

    monkeypatch.setattr(DocumentIn, "resolve", never_parse)
    answer = api.post("/api/ask", json={"report_id": report_id, "question": "Can the landlord enter?"}).json()
    assert answer["heading"] == "6. Entry"
    assert api.post("/api/packet", json={"report_id": report_id}).content.startswith(b"%PDF-")
    assert len(recorder.events) == 1


def test_unknown_or_invalid_report_ids(api: TestClient, sample_body: JSON) -> None:
    expired = api.post("/api/packet", json={"report_id": "a" * 64})
    assert expired.status_code == 404
    assert expired.json()["error"]["code"] == "expired"
    assert api.post("/api/ask", json={"report_id": "A" * 64, "question": "q"}).status_code == 422
    assert api.post("/api/packet", json={**sample_body, "report_id": "a" * 64}).status_code == 422
