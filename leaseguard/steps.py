"""Personalised next steps: an ordered action plan built from the findings and the user's context."""

from dataclasses import dataclass

from leaseguard.knowledge import CATEGORY_TITLES
from leaseguard.models import AnalysisReport, RiskLevel, Role

MAX_LISTED = 4


@dataclass(frozen=True)
class Step:
    """One action the user can take, in plain language."""

    title: str
    detail: str


FREE_LEGAL_AID = Step(
    "Get free legal help if you are eligible",
    "Call the NALSA legal services helpline on 15100, or visit your District Legal Services Authority. Under "
    "section 12 of the Legal Services Authorities Act, 1987, free legal services are available to, among others, "
    "women, children, members of Scheduled Castes and Scheduled Tribes, persons with disabilities, industrial "
    "workers and anyone whose income is below the limit set by their state.",
)


def _names(report: AnalysisReport, risk: RiskLevel) -> list[str]:
    return [f.clause.heading for f in report.findings if f.risk is risk]


def _listing(items: list[str]) -> str:
    shown = ", ".join(items[:MAX_LISTED])
    return shown + (f" and {len(items) - MAX_LISTED} more" if len(items) > MAX_LISTED else "")


def negotiation_step(report: AnalysisReport) -> Step | None:
    """Ask to change the flagged clauses, worst first; wording depends on the user's side.

    Args:
        report: The analysis report.

    Returns:
        The step, or None when nothing is flagged.
    """
    flagged = _names(report, RiskLevel.HIGH) + _names(report, RiskLevel.MEDIUM)
    if not flagged:
        return None
    if report.context.role is Role.LANDLORD:
        return Step("Revise one-sided clauses", f"Bring these closer to the fair baseline: {_listing(flagged)}.")
    return Step(
        "Negotiate before you sign", f"Ask for the fair baseline on: {_listing(flagged)}. Get changes in writing."
    )


def gap_step(report: AnalysisReport) -> Step | None:
    """Ask for protections the agreement is missing.

    Args:
        report: The analysis report.

    Returns:
        The step, or None when nothing is missing.
    """
    missing = [CATEGORY_TITLES[g.category].lower() for g in report.gaps]
    return Step("Add missing protections", f"Ask for a clause on: {_listing(missing)}.") if missing else None


def formality_step(report: AnalysisReport) -> Step | None:
    """Turn registration and stamp-duty notes into an action.

    Args:
        report: The analysis report.

    Returns:
        The step, or None when no formality applies.
    """
    notes = [n for n in report.context_notes if "regist" in n.lower() or "stamp" in n.lower()]
    return Step("Complete stamp duty and registration", " ".join(notes)) if notes else None


def review_steps(report: AnalysisReport) -> list[Step]:
    """Build the ordered action plan for an agreement review.

    Args:
        report: The analysis report.

    Returns:
        Steps in the order to take them, always ending with lawyer review and free legal aid.
    """
    steps = [s for s in (negotiation_step(report), gap_step(report), formality_step(report)) if s]
    steps.append(
        Step(
            "Take the consultation packet to a lawyer",
            "Download the PDF: it lists each flagged clause with a verified quote and the question to ask.",
        )
    )
    return [*steps, FREE_LEGAL_AID]
