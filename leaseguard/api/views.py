"""Convert domain objects into JSON-ready response dictionaries."""

from leaseguard.compare import CategoryChange
from leaseguard.knowledge import BASELINE, CATEGORY_TITLES
from leaseguard.models import AnalysisReport, Answer, Finding, RiskLevel, Step

JsonDict = dict[str, object]


def finding_view(finding: Finding) -> JsonDict:
    """Serialise one finding.

    Args:
        finding: The finding.

    Returns:
        A JSON-ready dictionary.
    """
    return {
        "index": finding.clause.index,
        "heading": finding.clause.heading,
        "category": finding.category.value,
        "category_title": CATEGORY_TITLES[finding.category],
        "risk": finding.risk.value,
        "risk_label": finding.risk.label,
        "reason": finding.reason,
        "quote": finding.quote,
        "quote_verified": finding.quote_verified,
        "baseline": BASELINE[finding.category],
        "question_for_lawyer": finding.question_for_lawyer,
        "rule_id": finding.rule_id,
    }


def report_view(report: AnalysisReport) -> JsonDict:
    """Serialise a report, worst findings first.

    Args:
        report: The analysis report.

    Returns:
        A JSON-ready dictionary.
    """
    ordered = sorted(report.findings, key=lambda f: (-f.risk.rank, f.clause.index))
    counts = report.counts()
    return {
        "counts": {level.value: counts[level] for level in RiskLevel},
        "findings": [finding_view(f) for f in ordered],
        "gaps": [{"category": g.category.value, "message": g.message} for g in report.gaps],
        "coverage_complete": report.coverage_complete,
        "context_notes": report.context_notes,
        "key_terms": [{"label": t.label, "value": t.value, "quote": t.quote} for t in report.key_terms],
        "next_steps": steps_view(report.next_steps),
        "report_id": report.report_id or None,
    }


def steps_view(steps: list[Step]) -> list[JsonDict]:
    """Serialise an ordered action plan.

    Args:
        steps: The steps.

    Returns:
        JSON-ready dictionaries with a title and detail.
    """
    return [{"title": step.title, "detail": step.detail} for step in steps]


def answer_view(answer: Answer) -> JsonDict:
    """Serialise a grounded answer.

    Args:
        answer: The answer.

    Returns:
        A JSON-ready dictionary.
    """
    return {"answer": answer.text, "quote": answer.quote, "heading": answer.clause_heading, "grounded": answer.grounded}


def change_view(change: CategoryChange) -> JsonDict:
    """Serialise one draft-comparison row.

    Args:
        change: The category change.

    Returns:
        A JSON-ready dictionary.
    """
    return {
        "category": change.category.value,
        "category_title": CATEGORY_TITLES[change.category],
        "direction": change.direction.value,
        "before": change.before.risk.value if change.before else None,
        "after": change.after.risk.value if change.after else None,
        "before_quote": change.before.quote if change.before else None,
        "after_quote": change.after.quote if change.after else None,
    }
