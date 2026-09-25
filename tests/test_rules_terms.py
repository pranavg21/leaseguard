"""Tests for leaseguard/rules/terms.py."""

import pytest

from leaseguard.models import UserContext
from leaseguard.rules.terms import rule_entry, rule_lock_in


@pytest.mark.parametrize(
    ("text", "rule_id"),
    [
        ("lock-in period of 6 months, notice of 1 month", "lock_in_fair"),
        ("lock-in period of 9 months for both parties", "lock_in_above_6_months"),
        ("lock-in period of 24 months", "lock_in_above_12_months"),
        ("the tenant shall forfeit the deposit if leaving", "lock_in_forfeiture"),
        ("Lock-in and Notice: lock-in period of 6 months. Notice period of three months.", "notice_above_2_months"),
    ],
)
def test_lock_in_rules(text: str, rule_id: str) -> None:
    assert rule_lock_in(text, text.lower(), UserContext()).rule_id == rule_id


@pytest.mark.parametrize(
    ("text", "rule_id"),
    [
        ("landlord may enter with 24 hours notice", "entry_fair"),
        ("landlord may enter at any time", "entry_without_notice"),
        ("landlord may enter without prior notice", "entry_without_notice"),
        ("landlord may inspect the flat", "entry_no_period"),
    ],
)
def test_entry_rules(text: str, rule_id: str) -> None:
    assert rule_entry(text, text.lower(), UserContext()).rule_id == rule_id
