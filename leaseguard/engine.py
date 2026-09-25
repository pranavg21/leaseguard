"""The analysis pipeline: scrub, segment, classify, rate, ground, audit coverage."""

import logging

from leaseguard.ai import LLMClient
from leaseguard.cache import LRUCache, content_key
from leaseguard.constants import CACHE_SIZE
from leaseguard.context_rules import context_notes, frame_for_role
from leaseguard.errors import ExpiredError, describe_error
from leaseguard.grounding import NormalisedText, best_sentence, verify_grounding
from leaseguard.knowledge import BASELINE, CATEGORY_TITLES, EXPECTED_CATEGORIES, LAWYER_QUESTIONS
from leaseguard.models import AnalysisReport, Category, Clause, CoverageGap, Finding, UserContext
from leaseguard.privacy import scrub_pii
from leaseguard.rules import assess
from leaseguard.segment import segment_clauses
from leaseguard.steps import review_steps
from leaseguard.summary import key_terms

logger = logging.getLogger(__name__)

REPORT_CACHE: LRUCache[AnalysisReport] = LRUCache(CACHE_SIZE)


def report_key(clean_text: str, ctx: UserContext) -> str:
    """Return the cache key for a scrubbed document and every context field that affects it.

    Args:
        clean_text: PII-scrubbed document text.
        ctx: The user's context.

    Returns:
        A content hash.
    """
    return content_key(ctx.role.value, ctx.state, str(ctx.monthly_rent), ctx.language.value, clean_text)


def build_finding(clause: Clause, category: Category, ctx: UserContext, source: NormalisedText) -> Finding:
    """Rate one clause and attach a verified quote.

    Args:
        clause: The clause to rate.
        category: Its category.
        ctx: The user's context.
        source: The full scrubbed document, normalised once, used to verify the quote.

    Returns:
        The finding.
    """
    rule = assess(clause, category, ctx)
    quote = best_sentence(clause.text, rule.keywords)
    return Finding(
        clause=clause,
        category=category,
        risk=rule.risk,
        reason=frame_for_role(rule.reason, rule.risk, ctx.role),
        quote=quote,
        quote_verified=verify_grounding(quote, source),
        question_for_lawyer=LAWYER_QUESTIONS[category],
        rule_id=rule.rule_id,
    )


def coverage_gaps(findings: list[Finding]) -> list[CoverageGap]:
    """Report expected protections that no clause covers.

    Args:
        findings: All findings for the document.

    Returns:
        One gap per expected category that is absent.
    """
    present = {finding.category for finding in findings}
    return [
        CoverageGap(cat, f"No clause about {CATEGORY_TITLES[cat].lower()} was found. Baseline: {BASELINE[cat]}")
        for cat in EXPECTED_CATEGORIES
        if cat not in present
    ]


def _rate_all(
    clauses: list[Clause], client: LLMClient, ctx: UserContext, source: NormalisedText
) -> tuple[list[Finding], list[int]]:
    categories = client.classify(clauses)
    findings: list[Finding] = []
    failed: list[int] = []
    for clause in clauses:
        try:
            findings.append(build_finding(clause, Category(categories[clause.index]), ctx, source))
        except (KeyError, ValueError) as error:
            logger.warning("clause_failed", extra={"clause": clause.index, "error": describe_error(error)})
            failed.append(clause.index)
    return findings, failed


def _explain(findings: list[Finding], client: LLMClient, ctx: UserContext) -> None:
    flagged = [(f.clause.index, f.clause.text, f.reason) for f in findings if f.risk.rank > 0]
    explanations = client.explain(flagged, ctx.language)
    for finding in findings:
        finding.reason = explanations.get(finding.clause.index, finding.reason)


def _build_report(clean: str, ctx: UserContext, client: LLMClient) -> AnalysisReport:
    findings, failed = _rate_all(segment_clauses(clean), client, ctx, NormalisedText(clean))
    _explain(findings, client, ctx)
    report = AnalysisReport(
        findings=findings,
        gaps=[] if failed else coverage_gaps(findings),
        coverage_complete=not failed,
        context=ctx,
        failed_clauses=failed,
        context_notes=context_notes(clean, ctx),
    )
    report.key_terms = key_terms(report)
    report.next_steps = review_steps(report)
    return report


def analyse(text: str, ctx: UserContext, client: LLMClient) -> AnalysisReport:
    """Analyse an agreement and return findings, coverage gaps and context notes.

    PII is scrubbed before anything reaches the AI client. Results are cached
    by content hash; a run in which any clause failed is never cached, so a
    transient failure cannot become a permanent wrong answer. A cached report
    carries its key as ``report_id`` so later requests can refer to it instead
    of uploading the document again.

    Args:
        text: Agreement text.
        ctx: The user's context.
        client: AI client used for classification and explanations.

    Returns:
        The analysis report.
    """
    clean = scrub_pii(text)
    key = report_key(clean, ctx)
    cached = REPORT_CACHE.get(key)
    if cached is not None:
        return cached
    report = _build_report(clean, ctx, client)
    if report.coverage_complete:
        report.report_id = key
        REPORT_CACHE.put(key, report)
    return report


def cached_report(report_id: str) -> AnalysisReport:
    """Return a report analysed earlier, without the document being sent again.

    Args:
        report_id: The ``report_id`` returned with the report.

    Returns:
        The cached report.

    Raises:
        ExpiredError: If the report is no longer cached on this server.
    """
    report = REPORT_CACHE.get(report_id)
    if report is None:
        raise ExpiredError("This review has expired. Sending the agreement again.")
    return report
