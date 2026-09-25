"""Tests for leaseguard/rules/duties.py."""

import pytest

from leaseguard.models import UserContext
from leaseguard.rules.duties import rule_jurisdiction, rule_maintenance, rule_other


@pytest.mark.parametrize(
    ("text", "rule_id"),
    [
        ("the tenant bears structural repairs", "maintenance_structural_on_tenant"),
        ("the tenant shall do all repairs", "maintenance_all_repairs"),
        ("tenant does minor repairs; the landlord shall do structural repairs", "maintenance_fair"),
    ],
)
def test_maintenance_rules(text: str, rule_id: str) -> None:
    assert rule_maintenance(text, text.lower(), UserContext()).rule_id == rule_id


def test_jurisdiction_rules() -> None:
    bad = "a sole arbitrator appointed by the landlord"
    good = "subject to the courts at pune"
    assert rule_jurisdiction(bad, bad, UserContext()).rule_id == "jurisdiction_unilateral_arbitrator"
    assert rule_jurisdiction(good, good, UserContext()).rule_id == "jurisdiction_fair"


@pytest.mark.parametrize(
    ("text", "rule_id"),
    [
        ("a penalty of rs. 500 per day", "other_penalty"),
        ("tenant waives all claims", "other_waive"),
        ("residential use only", "other_fair"),
    ],
)
def test_other_rules(text: str, rule_id: str) -> None:
    assert rule_other(text, text, UserContext()).rule_id == rule_id
