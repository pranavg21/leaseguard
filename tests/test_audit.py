"""Tests for scripts/audit.py: the structural audit must pass on this repository."""

from pathlib import Path

import pytest

from scripts import audit


def test_repository_passes_structural_audit() -> None:
    assert audit.run_audit() == []


def test_main_reports_success(capsys: pytest.CaptureFixture[str]) -> None:
    assert audit.main() == 0
    assert "Audit passed" in capsys.readouterr().err


def test_detects_long_function_print_and_missing_docstrings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    bad = tmp_path / "bad.py"
    bad.write_text("def public():\n" + "    print(1)\n" * 31 + "# type: ignore\n", encoding="utf-8")
    problems = " ".join(audit.check_python(bad))
    for expected in ("module docstring", "public() is 32 lines", "no docstring", "print()", "type-ignore"):
        assert expected in problems


def test_detects_unsafe_web_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    script = tmp_path / "a.js"
    script.write_text("el.innerHTML = x; // TODO", encoding="utf-8")
    page = tmp_path / "a.html"
    page.write_text('<html><body onload="x()"><h1>a</h1><h1>b</h1></body></html>', encoding="utf-8")
    assert len(audit.check_web(script)) == 2
    problems = " ".join(audit.check_web(page))
    assert "exactly one <h1>" in problems
    assert "skip-link" in problems
    assert "event handler" in problems


def test_detects_oversized_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * (audit.MAX_FILE_LINES + 1), encoding="utf-8")
    assert audit.check_sizes([big]) == [f"big.py: {audit.MAX_FILE_LINES + 1} lines > {audit.MAX_FILE_LINES}"]


def test_main_reports_failures(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(audit, "run_audit", lambda: ["x.py: problem"])
    assert audit.main() == 1
    assert "AUDIT: x.py: problem" in capsys.readouterr().err
