"""Structured JSON logging compatible with Google Cloud Logging.

Cloud Run forwards stdout to Cloud Logging, which reads the ``severity`` and
``message`` fields of each JSON line. Nothing in LeaseGuard uses ``print``.
"""

import json
import logging
import sys
from datetime import UTC, datetime

_RESERVED = frozenset(vars(logging.makeLogRecord({})))


class CloudJsonFormatter(logging.Formatter):
    """Format log records as single-line JSON with Cloud Logging field names."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise a record, including any ``extra`` fields.

        Args:
            record: The log record to format.

        Returns:
            A JSON string.
        """
        payload: dict[str, object] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
        }
        payload.update({k: v for k, v in vars(record).items() if k not in _RESERVED})
        if record.exc_info and record.exc_info[1] is not None:
            payload["error_type"] = type(record.exc_info[1]).__name__
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Route all logging to stdout as JSON. Safe to call more than once.

    Args:
        level: Minimum level to emit.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudJsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
