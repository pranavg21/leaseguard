"""Integration tests for every endpoint in leaseguard/api/routes.py."""

import base64

from fastapi.testclient import TestClient

import leaseguard.api
from leaseguard.api.routes import router
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
