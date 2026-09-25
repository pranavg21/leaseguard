"""Tests for leaseguard/api/dossier_schemas.py, dossier_views.py and dossier_routes.py."""

import base64
import hashlib

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from leaseguard.api.dossier_routes import router
from leaseguard.api.dossier_schemas import DossierRequest, EvidenceIn, PartiesIn
from leaseguard.api.dossier_views import event_view, file_view
from leaseguard.dossier.models import EventKind
from leaseguard.errors import IngestError
from leaseguard.sample import SAMPLE_LEASE
from leaseguard.sample_evidence import SAMPLE_EVIDENCE
from tests.dossier_fixtures import CHAT, PNG, event, evidence


def encoded(data: bytes, with_hash: bool = True) -> dict[str, object]:
    item: dict[str, object] = {"name": "chat.txt", "content_base64": base64.b64encode(data).decode()}
    if with_hash:
        item["client_sha256"] = hashlib.sha256(data).hexdigest()
    return item


def test_schema_validation() -> None:
    assert EvidenceIn.model_validate(encoded(CHAT)).to_upload().data == CHAT
    with pytest.raises(ValidationError):
        EvidenceIn.model_validate({**encoded(CHAT), "client_sha256": "not-a-hash"})
    with pytest.raises(ValidationError):
        DossierRequest.model_validate({"files": []})
    with pytest.raises(IngestError):
        EvidenceIn(name="x", content_base64="@@@").to_upload()
    assert PartiesIn(tenant="A").to_parties().tenant == "A"


def test_views_hide_evidence_text() -> None:
    view = file_view(evidence("secret text"))
    assert "text" not in view
    assert view["hash_matches"] is None
    assert event_view(event(EventKind.MOVE_OUT))["date"] is None


def test_router_paths() -> None:
    assert {getattr(route, "path", "") for route in router.routes} == {"/api/dossier", "/api/dossier/pdf"}


def test_dossier_endpoint_with_sample_evidence(api: TestClient) -> None:
    files = [{"name": n, "content_base64": base64.b64encode(t.encode()).decode()} for n, t in SAMPLE_EVIDENCE.items()]
    body = {"files": files, "lease": {"text": SAMPLE_LEASE}, "parties": {"tenant": "Priya", "landlord": "Ravi Sharma"}}
    result = api.post("/api/dossier", json=body).json()
    assert result["ledger"]["outstanding"] == 250_000
    assert result["contradictions"] == ["Ravi Sharma promised a refund, then later claimed deductions."]
    assert result["checklist"] == []
    assert "63(4)(c)" in result["certificate_title"]


def test_hash_mismatch_is_reported(api: TestClient) -> None:
    item = {**encoded(CHAT), "client_sha256": "0" * 64}
    result = api.post("/api/dossier", json={"files": [item, encoded(PNG, with_hash=False)]}).json()
    assert result["files"][0]["hash_matches"] is False
    assert result["files"][1]["kind"] == "image"
    assert any("changed during upload" in item for item in result["checklist"])


def test_dossier_pdf_endpoint(api: TestClient) -> None:
    response = api.post("/api/dossier/pdf", json={"files": [encoded(CHAT)]})
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_bad_evidence_is_a_structured_error(api: TestClient) -> None:
    response = api.post("/api/dossier", json={"files": [{"name": "x.bin", "content_base64": "AP/+"}]})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_document"


def test_dossier_includes_next_steps(api: TestClient) -> None:
    result = api.post("/api/dossier", json={"files": [encoded(CHAT)]}).json()
    titles = [step["title"] for step in result["next_steps"]]
    assert "Try a free pre-litigation Lok Adalat" in titles
    assert titles[-1] == "Get free legal help if you are eligible"


def test_dossier_pdf_by_id_without_re_uploading(api: TestClient) -> None:
    dossier_id = api.post("/api/dossier", json={"files": [encoded(CHAT)]}).json()["dossier_id"]
    assert isinstance(dossier_id, str)
    assert len(dossier_id) == 64
    assert api.post("/api/dossier/pdf", json={"dossier_id": dossier_id}).content.startswith(b"%PDF-")
    expired = api.post("/api/dossier/pdf", json={"dossier_id": "b" * 64})
    assert (expired.status_code, expired.json()["error"]["code"]) == (404, "expired")
    assert api.post("/api/dossier/pdf", json={"dossier_id": "nope"}).status_code == 422
