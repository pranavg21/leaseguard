"""HTTP security: headers, rate limiting, content-type and body-size checks."""

import threading
import time
from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from leaseguard.constants import (
    HSTS_MAX_AGE_SECONDS,
    MAX_REQUEST_BYTES,
    RATE_LIMIT_MAX_CLIENTS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)

Handler = Callable[[Request], Awaitable[Response]]

CSP_META_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
    "font-src 'self'; manifest-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'none'; "
    "form-action 'self'"
)
CONTENT_SECURITY_POLICY = f"{CSP_META_POLICY}; frame-ancestors 'none'"
SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "Strict-Transport-Security": f"max-age={HSTS_MAX_AGE_SECONDS}; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    """Build the single structured error format used by every endpoint.

    Args:
        status: HTTP status code.
        code: Stable machine-readable error code.
        message: Safe, human-readable message (never a stack trace).

    Returns:
        A JSON response of the form ``{"error": {"code": ..., "message": ...}}``.
    """
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def client_id(request: Request) -> str:
    """Identify the caller for rate limiting (first X-Forwarded-For hop on Cloud Run).

    Args:
        request: The incoming request.

    Returns:
        The client IP address, or "unknown".
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Sliding-window limiter: at most ``limit`` requests per ``window`` seconds per client.

    Clients are kept in least-recently-seen order, so idle clients are removed from the
    front in amortised O(1) per request, and memory never exceeds ``max_clients`` entries.
    """

    def __init__(
        self,
        limit: int = RATE_LIMIT_REQUESTS,
        window: float = RATE_LIMIT_WINDOW_SECONDS,
        max_clients: int = RATE_LIMIT_MAX_CLIENTS,
    ) -> None:
        """Create a limiter.

        Args:
            limit: Requests allowed per window.
            window: Window length in seconds.
            max_clients: Most clients tracked at once; beyond it the least recently seen is dropped.
        """
        self._limit = limit
        self._window = window
        self._max_clients = max_clients
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        """Record a request and report whether it is within the limit.

        Args:
            key: Client identifier.
            now: Current monotonic time (injectable for tests).

        Returns:
            True if the request may proceed.
        """
        current = time.monotonic() if now is None else now
        with self._lock:
            hits = self._track(key, current)
            while hits and current - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return False
            hits.append(current)
            return True

    def _track(self, key: str, now: float) -> deque[float]:
        hits = self._hits.get(key)
        if hits is not None:
            self._hits.move_to_end(key)
            return hits
        self._drop_idle(now)
        if len(self._hits) >= self._max_clients:
            self._hits.popitem(last=False)
        hits = self._hits[key] = deque()
        return hits

    def _drop_idle(self, now: float) -> None:
        while self._hits:
            oldest = next(iter(self._hits.values()))
            if oldest and now - oldest[-1] < self._window:
                return
            self._hits.popitem(last=False)

    def tracked_clients(self) -> int:
        """Return how many clients are currently tracked (for monitoring and tests)."""
        return len(self._hits)


def reject_unsafe_request(request: Request, limiter: RateLimiter) -> Response | None:
    """Apply API guards to state-changing requests.

    Args:
        request: The incoming request.
        limiter: The shared rate limiter.

    Returns:
        An error response, or None if the request may proceed.
    """
    if request.method != "POST" or not request.url.path.startswith("/api/"):
        return None
    if not request.headers.get("content-type", "").startswith("application/json"):
        return error_response(415, "unsupported_media_type", "Requests must be sent as application/json.")
    declared = request.headers.get("content-length", "")
    if not declared.isdigit() or int(declared) > MAX_REQUEST_BYTES:
        return error_response(413, "payload_too_large", "The request is too large or has no length.")
    if not limiter.allow(client_id(request)):
        return error_response(429, "rate_limited", "Too many requests. Please wait a minute and try again.")
    return None


def build_security_middleware(limiter: RateLimiter) -> Callable[[Request, Handler], Awaitable[Response]]:
    """Create middleware that guards API requests and adds security headers.

    Args:
        limiter: The rate limiter to use.

    Returns:
        An HTTP middleware function.
    """

    async def middleware(request: Request, call_next: Handler) -> Response:
        """Reject unsafe requests, otherwise continue; always add security headers."""
        response = reject_unsafe_request(request, limiter) or await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    return middleware
