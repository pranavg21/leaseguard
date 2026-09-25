"""Tests for leaseguard/rules/money.py."""

import pytest

from leaseguard.models import RiskLevel, UserContext
from leaseguard.rules import Rule
from leaseguard.rules.money import deposit_months, rule_deposit, rule_escalation

CTX = UserContext(monthly_rent=20_000)


def rate(rule: Rule, text: str, ctx: UserContext = CTX) -> str:
    return rule(text, text.lower(), ctx).rule_id


@pytest.mark.parametrize(
    ("text", "rule_id"),
    [
        ("security deposit of Rs. 40,000 refunded within 30 days", "deposit_fair"),
        ("security deposit of Rs. 1,00,000 refunded within 30 days", "deposit_above_2_months"),
        ("security deposit of Rs. 2,00,000 refunded within 30 days", "deposit_above_6_months"),
        ("a non-refundable deposit of one month", "deposit_non_refundable"),
        ("the deposit shall be refunded after deductions", "deposit_no_deadline"),
        ("deposit equal to ten months rent", "deposit_above_6_months"),
    ],
)
def test_deposit_rules(text: str, rule_id: str) -> None:
    assert rate(rule_deposit, text) == rule_id


def test_deposit_ratio_depends_on_rent() -> None:
    text = "deposit of Rs. 1,00,000 refunded within 30 days"
    assert rule_deposit(text, text, UserContext(monthly_rent=10_000)).risk is RiskLevel.HIGH
    assert rule_deposit(text, text, UserContext(monthly_rent=50_000)).risk is RiskLevel.FAIR
    assert deposit_months(text, UserContext()) is None


@pytest.mark.parametrize(
    ("text", "rule_id"),
    [
        ("rent increases by 5% every year", "escalation_fair"),
        ("rent increases by 12% every year", "escalation_above_10"),
        ("rent increases by 20 per cent every year", "escalation_above_15"),
        ("rent may be revised at the landlord's discretion", "escalation_discretionary"),
        ("rent will be revised on renewal", "escalation_unspecified"),
    ],
)
def test_escalation_rules(text: str, rule_id: str) -> None:
    assert rate(rule_escalation, text) == rule_id
