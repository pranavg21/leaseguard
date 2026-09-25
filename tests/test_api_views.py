"""Tests for leaseguard/api/views.py."""

from leaseguard.ai import OfflineClient
from leaseguard.api.views import answer_view, change_view, report_view
from leaseguard.compare import compare_reports
from leaseguard.engine import analyse
from leaseguard.models import Answer, UserContext
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED


def test_report_view_orders_worst_first(client: OfflineClient, tenant_ctx: UserContext) -> None:
    view = report_view(analyse(SAMPLE_LEASE, tenant_ctx, client))
    findings = view["findings"]
    assert isinstance(findings, list)
    assert findings[0]["risk"] == "HIGH"
    assert view["counts"] == {"FAIR": 4, "MEDIUM": 1, "HIGH": 5}
    assert {"baseline", "question_for_lawyer", "quote_verified", "rule_id"} <= set(findings[0])


def test_answer_and_change_views(client: OfflineClient, tenant_ctx: UserContext) -> None:
    assert answer_view(Answer("a", "q", "h", True)) == {"answer": "a", "quote": "q", "heading": "h", "grounded": True}
    changes = compare_reports(
        analyse(SAMPLE_LEASE, tenant_ctx, client), analyse(SAMPLE_LEASE_REVISED, tenant_ctx, client)
    )
    row = change_view(changes[0])
    assert row["direction"] == "better"
    assert row["before"] == "HIGH"
    assert row["after"] == "FAIR"
