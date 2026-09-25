"""Tests for leaseguard/rules/__init__.py (dispatch and one-sided wording)."""

from leaseguard.models import Category, RiskLevel, UserContext
from leaseguard.rules import RULES, assess
from tests.conftest import make_clause


def test_every_category_has_a_rule() -> None:
    assert set(RULES) == set(Category)


def test_one_sided_wording_raises_fair_clause_to_medium() -> None:
    clause = make_clause("The landlord may terminate at his sole discretion with 1 month notice.")
    result = assess(clause, Category.LOCK_IN, UserContext())
    assert result.risk is RiskLevel.MEDIUM
    assert result.rule_id == "one_sided"


def test_one_sided_wording_does_not_lower_high_risk() -> None:
    clause = make_clause("At his sole discretion the landlord may enter at any time.")
    assert assess(clause, Category.ENTRY, UserContext()).risk is RiskLevel.HIGH
