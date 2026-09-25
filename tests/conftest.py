"""Shared fixtures. Every test runs offline with a fresh cache."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from leaseguard.ai import OfflineClient
from leaseguard.api.app import create_app
from leaseguard.engine import REPORT_CACHE
from leaseguard.models import Clause, Role, UserContext
from leaseguard.sample import SAMPLE_LEASE


class MemoryRecorder:
    """Recorder that keeps events in memory for assertions."""

    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(self, event: dict[str, object]) -> None:
        self.events.append(event)


@pytest.fixture(autouse=True)
def _fresh_cache(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "FIRESTORE_COLLECTION", "GEMINI_MODEL"):
        monkeypatch.delenv(name, raising=False)
    REPORT_CACHE.clear()
    yield
    REPORT_CACHE.clear()


@pytest.fixture
def client() -> OfflineClient:
    return OfflineClient()


@pytest.fixture
def tenant_ctx() -> UserContext:
    return UserContext(role=Role.TENANT, state="Maharashtra", monthly_rent=25_000)


@pytest.fixture
def recorder() -> MemoryRecorder:
    return MemoryRecorder()


@pytest.fixture
def api(recorder: MemoryRecorder) -> TestClient:
    return TestClient(create_app(client=OfflineClient(), recorder=recorder))


@pytest.fixture
def sample_body() -> dict[str, object]:
    return {
        "document": {"text": SAMPLE_LEASE},
        "context": {"role": "tenant", "state": "Maharashtra", "monthly_rent": 25000, "language": "English"},
    }


def make_clause(text: str, heading: str = "Clause", index: int = 0) -> Clause:
    """Build a clause for rule tests."""
    return Clause(index=index, heading=heading, text=text)
