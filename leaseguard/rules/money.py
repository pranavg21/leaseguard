"""Rules for money terms: security deposit and rent escalation."""

import re

from leaseguard.constants import DEPOSIT_CAP_MONTHS, DEPOSIT_HIGH_MONTHS, ESCALATION_FAIR_PCT, ESCALATION_HIGH_PCT
from leaseguard.models import RiskLevel, RuleResult, UserContext
from leaseguard.parsing import parse_amount, parse_months, parse_percent
from leaseguard.rules.bands import Band, first_phrase, grade

_REFUND_DEADLINE = re.compile(r"\d+\s*days|within")

_DEPOSIT_WORDS = ("deposit", "refund", "months", "₹", "rs")
_ESCALATION_WORDS = ("increase", "escalat", "%", "per cent", "percent")
_MTA = "the 2-month benchmark in the Model Tenancy Act, 2021"

DEPOSIT_BANDS = (
    Band(
        DEPOSIT_HIGH_MONTHS,
        RiskLevel.HIGH,
        "deposit_above_6_months",
        f"About {{value}} months' rent, far above {_MTA}.",
    ),
    Band(
        DEPOSIT_CAP_MONTHS, RiskLevel.MEDIUM, "deposit_above_2_months", f"About {{value}} months' rent, above {_MTA}."
    ),
)
ESCALATION_BANDS = (
    Band(
        ESCALATION_HIGH_PCT, RiskLevel.HIGH, "escalation_above_15", "A {value}% increase is far above the 5-10% norm."
    ),
    Band(ESCALATION_FAIR_PCT, RiskLevel.MEDIUM, "escalation_above_10", "A {value}% increase is above the 5-10% norm."),
)

NON_REFUNDABLE = RuleResult(
    RiskLevel.HIGH, "The deposit, or part of it, is non-refundable.", "deposit_non_refundable", ("non-refundable",)
)
NO_DEADLINE = RuleResult(RiskLevel.MEDIUM, "No deadline is given for refunding the deposit.", "deposit_no_deadline", ())
DEPOSIT_FAIR = RuleResult(RiskLevel.FAIR, "The deposit terms are within the baseline.", "deposit_fair", _DEPOSIT_WORDS)
DISCRETIONARY = RuleResult(
    RiskLevel.HIGH, "Rent can be raised at the landlord's discretion with no limit.", "escalation_discretionary", ()
)
UNSPECIFIED = RuleResult(
    RiskLevel.MEDIUM, "The escalation rate is not stated as a fixed figure.", "escalation_unspecified", ()
)
ESCALATION_FAIR = RuleResult(
    RiskLevel.FAIR, "The escalation is within the 5-10% baseline.", "escalation_fair", _ESCALATION_WORDS
)


def deposit_months(raw: str, ctx: UserContext) -> float | None:
    """Return the deposit in months of rent, from a stated count or rupees divided by rent.

    Args:
        raw: Original clause text.
        ctx: The user's context.

    Returns:
        Months of rent, rounded to one decimal place, or None if unknown.
    """
    months = parse_months(raw, "deposit")
    amount = parse_amount(raw)
    if months is None and amount and ctx.monthly_rent:
        months = round(amount / ctx.monthly_rent, 1)
    return months


def rule_deposit(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate a deposit clause: refundability, size in months of rent, then refund deadline.

    Args:
        raw: Original clause text.
        lowered: Lower-case clause text.
        ctx: The user's context (supplies monthly rent).

    Returns:
        The rule outcome.
    """
    no_deadline = "refund" in lowered and not _REFUND_DEADLINE.search(lowered)
    return (
        first_phrase(lowered, ("non-refundable", "non refundable"), NON_REFUNDABLE)
        or grade(deposit_months(raw, ctx), DEPOSIT_BANDS, _DEPOSIT_WORDS)
        or (NO_DEADLINE if no_deadline else DEPOSIT_FAIR)
    )


def rule_escalation(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate an escalation clause: discretionary, unspecified, then percentage bands.

    Args:
        raw: Original clause text.
        lowered: Lower-case clause text.
        ctx: The user's context (unused; kept for a uniform rule signature).

    Returns:
        The rule outcome.
    """
    del ctx
    pct = parse_percent(raw)
    return (
        first_phrase(lowered, ("discretion", "as decided by the landlord"), DISCRETIONARY)
        or (UNSPECIFIED if pct is None else None)
        or grade(pct, ESCALATION_BANDS, _ESCALATION_WORDS)
        or ESCALATION_FAIR
    )
