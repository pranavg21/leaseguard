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
