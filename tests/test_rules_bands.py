"""Tests for leaseguard/rules/bands.py."""

from leaseguard.models import RiskLevel, RuleResult
from leaseguard.rules.bands import Band, first_phrase, grade

BANDS = (Band(10, RiskLevel.HIGH, "high", "{value} is high"), Band(5, RiskLevel.MEDIUM, "medium", "{value} is medium"))
RESULT = RuleResult(RiskLevel.HIGH, "r", "id", ())


def test_grade_picks_highest_band_first() -> None:
    high = grade(12.5, BANDS, ("k",))
    assert high is not None
    assert high.rule_id == "high"
    assert high.reason == "12.5 is high"
    medium = grade(6, BANDS, ())
    assert medium is not None
    assert medium.risk is RiskLevel.MEDIUM


def test_grade_returns_none_within_limits_or_unknown() -> None:
    assert grade(5, BANDS, ()) is None
    assert grade(None, BANDS, ()) is None


def test_first_phrase() -> None:
    assert first_phrase("at any time", ("any time",), RESULT) is RESULT
    assert first_phrase("with notice", ("any time",), RESULT) is None
