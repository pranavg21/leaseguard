"""Key terms at a glance: the agreement's main numbers, each with its verbatim source."""

from collections import defaultdict

from leaseguard.formatting import indian_rupees
from leaseguard.grounding import best_sentence, sentence_with
from leaseguard.models import AnalysisReport, Category, Finding, KeyTerm
from leaseguard.parsing import parse_amount, parse_months, parse_percent
from leaseguard.rules.money import deposit_months

NOT_STATED = "Not stated"
TERM_ANCHORS = ("for a period of", "term of")
LOCK_ANCHORS = ("lock-in period", "lock in period", "lock-in")
NOTICE_ANCHORS = ("notice period", "notice of")

__all__ = ["NOT_STATED", "KeyTerm", "key_terms"]


def _texts_by_category(findings: list[Finding]) -> dict[Category, str]:
    grouped: defaultdict[Category, list[str]] = defaultdict(list)
    for finding in findings:
        grouped[finding.category].append(finding.clause.text)
    return {category: " ".join(texts) for category, texts in grouped.items()}


def _clause_with(findings: list[Finding], anchors: tuple[str, ...]) -> str:
    return next((f.clause.text for f in findings if any(a in f.clause.text.lower() for a in anchors)), "")


def _rent_sentence(findings: list[Finding]) -> str:
    for finding in findings:
        text = finding.clause.text
        lowered = text.lower()
        if "rent" in lowered and parse_amount(text) and not any(w in lowered for w in ("deposit", "increase")):
            return best_sentence(text, ("rent", "rs", "₹"))
    return ""


def _term(label: str, value: str | None, text: str, anchors: tuple[str, ...]) -> KeyTerm:
    if value is None:
        return KeyTerm(label, NOT_STATED, "")
    return KeyTerm(label, value, sentence_with(text, anchors))


def _months(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:g} month" if value == 1 else f"{value:g} months"


def _deposit(report: AnalysisReport, text: str) -> KeyTerm:
    amount = parse_amount(text)
    months = deposit_months(text, report.context) if text else None
    parts = [indian_rupees(amount)] if amount else []
    parts += [f"about {months:g} months' rent"] if months else []
    return _term("Security deposit", ", ".join(parts) or None, text, ("deposit",))


def key_terms(report: AnalysisReport) -> list[KeyTerm]:
    """Extract the headline terms deterministically from the analysed clauses.

    Findings are grouped by category in one pass, so each term reads only its own clauses.

    Args:
        report: The analysis report.

    Returns:
        Rent, deposit, term, lock-in, notice and escalation, in that order.
    """
    findings = report.findings
    texts = _texts_by_category(findings)
    term = _clause_with(findings, TERM_ANCHORS)
    lock = texts.get(Category.LOCK_IN, "")
    escalation = texts.get(Category.ESCALATION, "")
    rent_quote = _rent_sentence(findings)
    rent = parse_amount(rent_quote)
    pct = parse_percent(escalation)
    return [
        KeyTerm("Monthly rent", indian_rupees(rent), rent_quote) if rent else KeyTerm("Monthly rent", NOT_STATED, ""),
        _deposit(report, texts.get(Category.DEPOSIT, "")),
        _term("Agreement term", _months(parse_months(term, *TERM_ANCHORS)), term, TERM_ANCHORS),
        _term("Lock-in", _months(parse_months(lock, *LOCK_ANCHORS)), lock, LOCK_ANCHORS),
        _term("Notice period", _months(parse_months(lock, *NOTICE_ANCHORS)), lock, NOTICE_ANCHORS),
        _term("Rent increase", None if pct is None else f"{pct:g}%", escalation, ("%", "per cent", "percent")),
    ]
