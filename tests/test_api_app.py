"""Tests for leaseguard/api/app.py: pages, PWA files and error handling."""

import pytest
from fastapi.testclient import TestClient

from leaseguard.ai import OfflineClient
from leaseguard.api.app import ROOT_FILES, create_app
from tests.conftest import MemoryRecorder


class ExplodingRecorder(MemoryRecorder):
    def record(self, event: dict[str, object]) -> None:
        raise RuntimeError("unexpected")


@pytest.mark.parametrize("path", ["/", *(f"/{name}" for name in ROOT_FILES), "/static/js/main.js"])
def test_pages_and_pwa_files_are_served(api: TestClient, path: str) -> None:
    assert api.get(path).status_code == 200


def test_manifest_media_type(api: TestClient) -> None:
    assert api.get("/manifest.webmanifest").headers["content-type"].startswith("application/manifest+json")


def test_query_strings_cannot_select_files(api: TestClient) -> None:
    assert api.get("/sw.js?name=../README.md").text.startswith("/**\n * @module sw")


def test_unknown_route_is_structured_404(api: TestClient) -> None:
    response = api.get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Not found."


def test_unexpected_errors_hide_details(sample_body: dict[str, object]) -> None:
    app = create_app(client=OfflineClient(), recorder=ExplodingRecorder())
    response = TestClient(app, raise_server_exceptions=False).post("/api/analyze", json=sample_body)
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Something went wrong. Please try again."}
    }


def test_api_docs_are_disabled(api: TestClient) -> None:
    assert api.get("/docs").status_code == 404


def test_responses_are_compressed_and_static_assets_cached(api: TestClient) -> None:
    script = api.get("/static/js/main.js", headers={"Accept-Encoding": "gzip"})
    assert script.headers["content-encoding"] == "gzip"
    assert script.headers["cache-control"] == "public, max-age=86400"
    assert "script-src 'self'" in script.headers["content-security-policy"]
    page = api.get("/", headers={"Accept-Encoding": "gzip"})
    assert page.headers["cache-control"] == "no-cache"
    assert api.get("/static/missing.js").headers.get("cache-control") != "public, max-age=86400"


def test_dossier_pdf_reuses_the_dossier_without_a_second_ai_call() -> None:
    import base64

    from tests.test_dossier_service import CountingLabeller

    client = CountingLabeller()
    app = TestClient(create_app(client=client, recorder=MemoryRecorder()))
    files = [
        {
            "name": "chat.txt",
            "content_base64": base64.b64encode(b"12/03/2026, 10:15 - Ravi: I will return your full deposit").decode(),
        }
    ]
    assert app.post("/api/dossier", json={"files": files}).status_code == 200
    assert app.post("/api/dossier/pdf", json={"files": files}).status_code == 200
    assert client.calls == 1
