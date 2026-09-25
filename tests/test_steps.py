"""Tests for leaseguard/steps.py."""

from leaseguard.ai import OfflineClient
from leaseguard.engine import analyse
from leaseguard.models import AnalysisReport, Category, CoverageGap, Role, UserContext
from leaseguard.sample import SAMPLE_LEASE
from leaseguard.steps import FREE_LEGAL_AID, MAX_LISTED, gap_step, negotiation_step, review_steps


def report_for(role: Role = Role.TENANT, state: str = "Maharashtra") -> AnalysisReport:
    return analyse(SAMPLE_LEASE, UserContext(role=role, state=state, monthly_rent=25_000), OfflineClient())


def test_tenant_plan_is_ordered_and_ends_with_free_legal_aid() -> None:
    steps = review_steps(report_for())
    titles = [s.title for s in steps]
    assert titles[0] == "Negotiate before you sign"
    assert "Complete stamp duty and registration" in titles
    assert titles[-2] == "Take the consultation packet to a lawyer"
    assert steps[-1] is FREE_LEGAL_AID
    assert "15100" in FREE_LEGAL_AID.detail
    assert "section 12" in FREE_LEGAL_AID.detail


def test_negotiation_lists_worst_first_and_truncates() -> None:
    step = negotiation_step(report_for())
    assert step is not None
    assert step.detail.startswith("Ask for the fair baseline on: 3. Security Deposit")
    assert "and 2 more" in step.detail
    assert MAX_LISTED == 4


def test_landlord_wording_differs() -> None:
    step = negotiation_step(report_for(role=Role.LANDLORD))
    assert step is not None
    assert step.title == "Revise one-sided clauses"


def test_no_flags_no_gaps_no_formalities() -> None:
    clean = AnalysisReport([], [], True, UserContext(state="Kerala"))
    assert negotiation_step(clean) is None
    assert gap_step(clean) is None
    assert [s.title for s in review_steps(clean)] == ["Take the consultation packet to a lawyer", FREE_LEGAL_AID.title]


def test_gap_step_names_missing_protections() -> None:
    report = AnalysisReport([], [CoverageGap(Category.ENTRY, "x")], True, UserContext())
    step = gap_step(report)
    assert step is not None
    assert "privacy and entry" in step.detail
