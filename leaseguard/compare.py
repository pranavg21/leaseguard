"""Compare two drafts of an agreement, category by category."""

from dataclasses import dataclass
from enum import StrEnum

from leaseguard.models import AnalysisReport, Category, Finding, RiskLevel


class Direction(StrEnum):
    """How a category changed between drafts, in display-priority order."""

    WORSE = "worse"
    REMOVED = "removed"
    ADDED = "added"
    BETTER = "better"
    SAME = "same"


_PRIORITY = {direction: position for position, direction in enumerate(Direction)}


@dataclass(frozen=True)
class CategoryChange:
    """The worst-rated clause of one category in each draft."""

    category: Category
    before: Finding | None
    after: Finding | None
    direction: Direction


def worst_finding(findings: list[Finding], category: Category) -> Finding | None:
    """Return the highest-risk finding in a category.

    Args:
        findings: All findings for a draft.
        category: The category to look at.

    Returns:
        The worst finding, or None if the category is absent.
    """
    matches = [finding for finding in findings if finding.category is category]
    return max(matches, key=lambda finding: finding.risk.rank, default=None)


def direction_of(before: RiskLevel | None, after: RiskLevel | None) -> Direction:
    """Classify the change between two risk levels.

    Args:
        before: Risk in the original draft, or None if absent.
        after: Risk in the revised draft, or None if absent.

    Returns:
        The direction of change.
    """
    if before is None:
        return Direction.ADDED
    if after is None:
        return Direction.REMOVED
    if after.rank == before.rank:
        return Direction.SAME
    return Direction.BETTER if after.rank < before.rank else Direction.WORSE


def compare_reports(original: AnalysisReport, revised: AnalysisReport) -> list[CategoryChange]:
    """Compare two drafts, listing categories that got worse first.

    Args:
        original: Report for the original draft.
        revised: Report for the revised draft.

    Returns:
        One change per category present in either draft.
    """
    changes = []
    for category in Category:
        before = worst_finding(original.findings, category)
        after = worst_finding(revised.findings, category)
        if before or after:
            direction = direction_of(before.risk if before else None, after.risk if after else None)
            changes.append(CategoryChange(category, before, after, direction))
    return sorted(changes, key=lambda change: _PRIORITY[change.direction])
