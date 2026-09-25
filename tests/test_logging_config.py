"""Tests for leaseguard/logging_config.py."""

import json
import logging

import pytest

from leaseguard.logging_config import CloudJsonFormatter, configure_logging


def _record(**extra: object) -> logging.LogRecord:
    record = logging.makeLogRecord({"name": "t", "levelname": "WARNING", "msg": "hello %s", "args": ("x",)})
    record.__dict__.update(extra)
    return record


def test_formatter_emits_cloud_logging_fields() -> None:
    payload = json.loads(CloudJsonFormatter().format(_record(path="/api")))
    assert payload["severity"] == "WARNING"
    assert payload["message"] == "hello x"
    assert payload["path"] == "/api"
    assert "time" in payload


def test_formatter_records_exception_type_without_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = _record(exc_info=sys.exc_info())
    payload = json.loads(CloudJsonFormatter().format(record))
    assert payload["error_type"] == "ValueError"
    assert "Traceback" not in json.dumps(payload)


def test_configure_logging_writes_json_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    logging.getLogger("leaseguard.test").info("ready", extra={"k": 1})
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert json.loads(line)["k"] == 1
