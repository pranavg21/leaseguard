"""Rules for duties and remedies: maintenance, disputes and other terms."""

import re

from leaseguard.models import RiskLevel, RuleResult, UserContext
from leaseguard.rules.bands import first_phrase

_MAINTENANCE_WORDS = ("repair", "structural", "maintenance", "wear")
_JURISDICTION_WORDS = ("arbitrat", "court", "jurisdiction", "dispute")
_UNILATERAL_ARBITRATOR = ("appointed by the landlord", "appointed solely by", "nominated by the landlord")
_OTHER_FLAGS = ("penalty", "forfeit", "waive")

STRUCTURAL_ON_TENANT = RuleResult(
    RiskLevel.HIGH,
    "The tenant is made responsible for structural repairs.",
    "maintenance_structural_on_tenant",
    ("structural",),
)
ALL_REPAIRS = RuleResult(
    RiskLevel.MEDIUM,
    "All repairs fall on one party, with no minor/major split.",
    "maintenance_all_repairs",
    ("all repairs", "all maintenance"),
)
MAINTENANCE_FAIR = RuleResult(
    RiskLevel.FAIR, "Repair duties are split in line with the baseline.", "maintenance_fair", _MAINTENANCE_WORDS
)
UNILATERAL_ARBITRATOR = RuleResult(
    RiskLevel.HIGH,
    "The arbitrator is chosen by one party alone.",
    "jurisdiction_unilateral_arbitrator",
    ("appointed", "nominated"),
)
JURISDICTION_FAIR = RuleResult(
    RiskLevel.FAIR, "Dispute resolution is within the baseline.", "jurisdiction_fair", _JURISDICTION_WORDS
)
OTHER_FAIR = RuleResult(RiskLevel.FAIR, "No unusual terms detected.", "other_fair", ())


def rule_maintenance(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate a repairs clause: structural repairs on the tenant, all repairs on one party, or fair.

    Args:
        raw: Original clause text (unused; kept for a uniform rule signature).
        lowered: Lower-case clause text.
        ctx: The user's context (unused).

    Returns:
        The rule outcome.
    """
    del raw, ctx
    if "structural" in lowered and "tenant" in lowered and "landlord shall" not in lowered:
        return STRUCTURAL_ON_TENANT
    if re.search(r"all (?:repairs|maintenance)", lowered) and "minor" not in lowered:
        return ALL_REPAIRS
    return MAINTENANCE_FAIR


def rule_jurisdiction(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate a dispute clause: HIGH if one party alone chooses the arbitrator.

    Args:
        raw: Original clause text (unused; kept for a uniform rule signature).
        lowered: Lower-case clause text.
        ctx: The user's context (unused).

    Returns:
        The rule outcome.
    """
    del raw, ctx
    return first_phrase(lowered, _UNILATERAL_ARBITRATOR, UNILATERAL_ARBITRATOR) or JURISDICTION_FAIR


def rule_other(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate any other clause: MEDIUM if it mentions a penalty, forfeiture or waiver.

    Args:
        raw: Original clause text (unused; kept for a uniform rule signature).
        lowered: Lower-case clause text.
        ctx: The user's context (unused).

    Returns:
        The rule outcome.
    """
    del raw, ctx
    flag = next((flag for flag in _OTHER_FLAGS if flag in lowered), None)
    if flag is None:
        return OTHER_FAIR
    return RuleResult(
        RiskLevel.MEDIUM, f"Contains a '{flag}' term; check it is proportionate.", f"other_{flag}", (flag,)
    )
