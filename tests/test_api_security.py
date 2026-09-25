"""Tests for leaseguard/api/security.py."""

from fastapi.testclient import TestClient
from starlette.requests import Request

from leaseguard.api.security import SECURITY_HEADERS, RateLimiter, client_id, error_response
from leaseguard.constants import MAX_REQUEST_BYTES


def make_request(headers: dict[str, str], client: tuple[str, int] | None = ("1.2.3.4", 1)) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": raw, "client": client})


def test_rate_limiter_sliding_window() -> None:
    limiter = RateLimiter(limit=2, window=10)
    assert limiter.allow("a", now=0)
    assert limiter.allow("a", now=1)
    assert not limiter.allow("a", now=2)
    assert limiter.allow("b", now=2)
    assert limiter.allow("a", now=11)


def test_client_id_prefers_forwarded_header() -> None:
    assert client_id(make_request({"X-Forwarded-For": "9.9.9.9, 10.0.0.1"})) == "9.9.9.9"
    assert client_id(make_request({})) == "1.2.3.4"
    assert client_id(make_request({}, client=None)) == "unknown"


def test_error_response_shape() -> None:
    response = error_response(418, "teapot", "No coffee.")
    assert response.status_code == 418
    assert response.body == b'{"error":{"code":"teapot","message":"No coffee."}}'


def test_headers_on_every_response(api: TestClient) -> None:
    for path in ("/", "/api/health", "/does-not-exist"):
        response = api.get(path)
        for name, value in SECURITY_HEADERS.items():
            assert response.headers[name] == value
    assert "script-src 'self'" in SECURITY_HEADERS["Content-Security-Policy"]
    assert "unsafe-inline" not in SECURITY_HEADERS["Content-Security-Policy"]


def test_rejects_wrong_content_type(api: TestClient) -> None:
    response = api.post("/api/analyze", content="{}", headers={"Content-Type": "text/plain"})
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_rejects_oversized_body(api: TestClient) -> None:
    headers = {"Content-Type": "application/json", "Content-Length": str(MAX_REQUEST_BYTES + 1)}
    response = api.post("/api/analyze", content="{}", headers=headers)
    assert response.status_code == 413


def test_rate_limit_returns_429(api: TestClient) -> None:
    statuses = {api.post("/api/analyze", json={}).status_code for _ in range(35)}
    assert statuses == {422, 429}
