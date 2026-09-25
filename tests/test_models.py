"""Tests for leaseguard/models.py."""

from leaseguard.models import AnalysisReport, Category, Finding, RiskLevel, UserContext
from tests.conftest import make_clause


def test_risk_rank_and_label() -> None:
    assert [r.rank for r in (RiskLevel.FAIR, RiskLevel.MEDIUM, RiskLevel.HIGH)] == [0, 1, 2]
    assert RiskLevel.HIGH.label == "High risk"


def test_report_counts_every_level() -> None:
    finding = Finding(make_clause("x"), Category.OTHER, RiskLevel.HIGH, "r", "q", True, "?", "id")
    report = AnalysisReport([finding, finding], [], True, UserContext())
    assert report.counts() == {RiskLevel.FAIR: 0, RiskLevel.MEDIUM: 0, RiskLevel.HIGH: 2}
