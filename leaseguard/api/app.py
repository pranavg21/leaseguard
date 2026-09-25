"""FastAPI application factory. Run with ``uvicorn leaseguard.api.app:app``."""

import logging
import mimetypes
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from leaseguard import __version__
from leaseguard.ai import LLMClient, get_client
from leaseguard.api import dossier_routes, routes
from leaseguard.api.security import Handler, RateLimiter, build_security_middleware, error_response
from leaseguard.constants import GZIP_MIN_BYTES, STATIC_MAX_AGE_SECONDS
from leaseguard.errors import LeaseGuardError, describe_error
from leaseguard.logging_config import configure_logging
from leaseguard.telemetry import Recorder, get_recorder

logger = logging.getLogger(__name__)

mimetypes.add_type("application/manifest+json", ".webmanifest")

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
ROOT_FILES = ("sw.js", "manifest.webmanifest", "offline.html", "icon.svg")
_MS_PER_SECOND = 1000
HTTP_OK = 200


async def _log_requests(request: Request, call_next: Handler) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    latency = round((time.perf_counter() - started) * _MS_PER_SECOND, 1)
    extra = {"method": request.method, "path": request.url.path, "status": response.status_code, "latency_ms": latency}
    logger.info("request", extra=extra)
    return response


async def _cache_static(request: Request, call_next: Handler) -> Response:
    response = await call_next(request)
    if request.url.path.startswith("/static/") and response.status_code == HTTP_OK:
        response.headers["Cache-Control"] = f"public, max-age={STATIC_MAX_AGE_SECONDS}"
    return response


def _register_errors(app: FastAPI) -> None:
    async def on_domain_error(_: Request, error: Exception) -> Response:
        """Return 400 with the domain error's safe message."""
        code = error.code if isinstance(error, LeaseGuardError) else "bad_request"
        return error_response(400, code, str(error))

    async def on_validation_error(_: Request, error: Exception) -> Response:
        """Return 422 without echoing the invalid input."""
        del error  # never echo user input back
        return error_response(422, "invalid_request", "The request body is missing fields or has invalid values.")

    async def on_http_error(_: Request, error: Exception) -> Response:
        """Return routing errors such as 404 in the structured format."""
        status = error.status_code if isinstance(error, HTTPException) else 500
        return error_response(status, "http_error", "Not found." if status == 404 else "Request failed.")

    async def on_unexpected(_: Request, error: Exception) -> Response:
        """Log the error type and return a generic 500 with no details."""
        logger.error("unhandled_error", extra={"error": describe_error(error)})
        return error_response(500, "internal_error", "Something went wrong. Please try again.")

    app.add_exception_handler(LeaseGuardError, on_domain_error)
    app.add_exception_handler(RequestValidationError, on_validation_error)
    app.add_exception_handler(HTTPException, on_http_error)
    app.add_exception_handler(Exception, on_unexpected)


def _page_handler(name: str) -> Handler:
    path = STATIC_DIR / name

    async def handler(_: Request) -> Response:
        """Serve the fixed file; the request cannot choose the path."""
        return FileResponse(path, headers={"Cache-Control": "no-cache"})

    return handler


def _register_pages(app: FastAPI) -> None:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.add_route("/", _page_handler("index.html"), methods=["GET"], include_in_schema=False)
    for name in ROOT_FILES:
        app.add_route(f"/{name}", _page_handler(name), methods=["GET"], include_in_schema=False)


def create_app(client: LLMClient | None = None, recorder: Recorder | None = None) -> FastAPI:
    """Build the application.

    Args:
        client: AI client; defaults to Gemini if configured, else offline.
        recorder: Metrics recorder; defaults to Firestore if configured, else no-op.

    Returns:
        The configured FastAPI app.
    """
    configure_logging()
    app = FastAPI(title="LeaseGuard", version=__version__, docs_url=None, redoc_url=None)
    app.state.llm_client = client or get_client()
    app.state.recorder = recorder or get_recorder()
    app.middleware("http")(build_security_middleware(RateLimiter()))
    app.middleware("http")(_cache_static)
    app.middleware("http")(_log_requests)
    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MIN_BYTES)
    _register_errors(app)
    app.include_router(routes.router)
    app.include_router(dossier_routes.router)
    _register_pages(app)
    return app


app = create_app()
