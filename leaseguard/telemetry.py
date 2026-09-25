"""Optional anonymous usage metrics stored in Google Cloud Firestore.

Only counts and categories are recorded: never document text, quotes,
questions or anything that could identify a person. Recording is enabled by
setting ``FIRESTORE_COLLECTION``; otherwise a no-op recorder is used.
"""

import logging
from datetime import UTC, datetime
from typing import Protocol

from leaseguard.config import get_settings
from leaseguard.errors import describe_error
from leaseguard.models import AnalysisReport, RiskLevel

logger = logging.getLogger(__name__)


class _Collection(Protocol):
    def add(self, document_data: dict[str, object]) -> object:
        """Add a document to the collection."""
        ...


class _Client(Protocol):
    def collection(self, collection_path: str) -> _Collection:
        """Return a collection reference."""
        ...


class Recorder(Protocol):
    """Destination for anonymous metrics."""

    def record(self, event: dict[str, object]) -> None:
        """Store one event."""
        ...


class NullRecorder:
    """Recorder that discards events (used when Firestore is not configured)."""

    def record(self, event: dict[str, object]) -> None:
        """Discard an event.

        Args:
            event: The event to discard.
        """
        del event


class FirestoreRecorder:
    """Recorder that writes events to a Firestore collection."""

    def __init__(self, collection: str, client: _Client | None = None) -> None:
        """Create a recorder.

        Args:
            collection: Firestore collection name.
            client: Optional pre-built Firestore client (used in tests).
        """
        if client is None:
            from google.cloud import firestore  # noqa: PLC0415 - optional dependency, loaded on demand

            client = firestore.Client()
        self._collection = client.collection(collection)

    def record(self, event: dict[str, object]) -> None:
        """Write an event; failures are logged and never break a request.

        Args:
            event: The event to store.
        """
        try:
            self._collection.add(event)
        except Exception as error:  # noqa: BLE001 - metrics must never break the user's request
            logger.warning("telemetry_failed", extra={"error": describe_error(error)})


def analysis_event(report: AnalysisReport, ai_mode: str) -> dict[str, object]:
    """Build an anonymous event describing an analysis.

    Args:
        report: The analysis report.
        ai_mode: Name of the AI client used.

    Returns:
        Counts per risk level, flagged categories and coarse context only.
    """
    counts = report.counts()
    return {
        "time": datetime.now(tz=UTC).isoformat(),
        "ai_mode": ai_mode,
        "role": report.context.role.value,
        "state": report.context.state,
        "counts": {level.value: counts[level] for level in RiskLevel},
        "flagged": sorted({f.category.value for f in report.findings if f.risk is not RiskLevel.FAIR}),
        "gaps": len(report.gaps),
    }


def get_recorder() -> Recorder:
    """Return a Firestore recorder if configured, otherwise a no-op recorder.

    Returns:
        A recorder.
    """
    collection = get_settings().firestore_collection
    return FirestoreRecorder(collection) if collection else NullRecorder()
