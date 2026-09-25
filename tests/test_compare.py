"""Tests for leaseguard/compare.py."""

import pytest

from leaseguard.ai import OfflineClient
from leaseguard.compare import Direction, compare_reports, direction_of, worst_finding
from leaseguard.engine import analyse
from leaseguard.models import Category, RiskLevel, UserContext
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (None, RiskLevel.FAIR, Direction.ADDED),
        (RiskLevel.FAIR, None, Direction.REMOVED),
        (RiskLevel.HIGH, RiskLevel.FAIR, Direction.BETTER),
        (RiskLevel.FAIR, RiskLevel.MEDIUM, Direction.WORSE),
        (RiskLevel.MEDIUM, RiskLevel.MEDIUM, Direction.SAME),
    ],
)
def test_direction_of(before: RiskLevel | None, after: RiskLevel | None, expected: Direction) -> None:
    assert direction_of(before, after) is expected


def test_compare_samples(client: OfflineClient, tenant_ctx: UserContext) -> None:
    original = analyse(SAMPLE_LEASE, tenant_ctx, client)
    revised = analyse(SAMPLE_LEASE_REVISED, tenant_ctx, client)
    forward = {c.category: c.direction for c in compare_reports(original, revised)}
    assert forward[Category.DEPOSIT] is Direction.BETTER
    assert forward[Category.ESCALATION] is Direction.SAME
    backward = compare_reports(revised, original)
    assert backward[0].direction is Direction.WORSE
    assert worst_finding(original.findings, Category.DEPOSIT) is not None


def test_categories_absent_from_both_drafts_are_skipped(client: OfflineClient, tenant_ctx: UserContext) -> None:
    text = "\n".join(
        f"{i}. Use: The premises are for residential purposes only, clause {i} applies." for i in range(1, 8)
    )
    report = analyse(text, tenant_ctx, client)
    changes = compare_reports(report, report)
    assert [change.category for change in changes] == [Category.OTHER]
