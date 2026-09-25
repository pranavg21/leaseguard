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


def test_csp_meta_and_server_policies_in_sync() -> None:
    import re
    from pathlib import Path

    from leaseguard.api.security import CONTENT_SECURITY_POLICY, CSP_META_POLICY

    expected_server_csp = f"{CSP_META_POLICY}; frame-ancestors 'none'"
    assert expected_server_csp == CONTENT_SECURITY_POLICY
    static_dir = Path(__file__).resolve().parents[1] / "static"
    pattern = re.compile(r'<meta http-equiv="Content-Security-Policy"\s+content="([^"]+)"')
    html_files = list(static_dir.glob("*.html"))
    assert html_files, "Expected static HTML files"
    for html_file in html_files:
        match = pattern.search(html_file.read_text(encoding="utf-8"))
        assert match is not None, f"Missing CSP meta tag in {html_file.name}"
        assert match.group(1) == CSP_META_POLICY, f"Mismatch in {html_file.name}"


def test_rate_limiter_memory_is_bounded() -> None:
    limiter = RateLimiter(limit=5, window=10, max_clients=3)
    for i in range(3):
        limiter.allow(f"client-{i}", now=0)
    assert limiter.tracked_clients() == 3
    limiter.allow("client-new", now=20)  # others idle for a full window: dropped from the front
    assert limiter.tracked_clients() == 1
    limiter.allow("a", now=21)
    limiter.allow("b", now=21)
    limiter.allow("client-new", now=21)  # seen again: now the most recent
    limiter.allow("c", now=22)  # full and all active: the least recently seen ("a") is dropped
    assert limiter.tracked_clients() == 3
    for _ in range(4):
        limiter.allow("client-new", now=23)
    assert not limiter.allow("client-new", now=23)  # a tracked client keeps its window
    assert limiter.allow("a", now=23)  # "a" was dropped, so it starts a fresh window


def test_rate_limiter_drops_only_idle_clients_from_the_front() -> None:
    limiter = RateLimiter(limit=5, window=10, max_clients=100)
    for i in range(50):
        limiter.allow(f"old-{i}", now=0)
    limiter.allow("recent", now=5)
    limiter.allow("newcomer", now=12)
    assert limiter.tracked_clients() == 2
