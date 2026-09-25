"""Deterministic baseline rules. Ratings never depend on a language model.

Each rule takes the clause text (original and lower-case) and the user
context, and returns a :class:`~leaseguard.models.RuleResult` with a stable
rule ID so every rating can be traced and reproduced.
"""

from collections.abc import Callable, Mapping
from types import MappingProxyType

from leaseguard.models import Category, Clause, RiskLevel, RuleResult, UserContext
from leaseguard.rules.duties import rule_jurisdiction, rule_maintenance, rule_other
from leaseguard.rules.money import rule_deposit, rule_escalation
from leaseguard.rules.terms import rule_entry, rule_lock_in

Rule = Callable[[str, str, UserContext], RuleResult]

RULES: Mapping[Category, Rule] = MappingProxyType(
    {
        Category.DEPOSIT: rule_deposit,
        Category.LOCK_IN: rule_lock_in,
        Category.ESCALATION: rule_escalation,
        Category.ENTRY: rule_entry,
        Category.MAINTENANCE: rule_maintenance,
        Category.JURISDICTION: rule_jurisdiction,
        Category.OTHER: rule_other,
    }
)

ONE_SIDED_PHRASES = (
    "sole discretion",
    "absolute discretion",
    "without assigning any reason",
    "without any reason",
)


def assess(clause: Clause, category: Category, ctx: UserContext) -> RuleResult:
    """Apply the baseline rule for a category, then check for one-sided wording.

    Args:
        clause: The clause to rate.
        category: The clause's category.
        ctx: The user's context.

    Returns:
        The rule outcome.
    """
    lowered = clause.text.lower()
    result = RULES[category](clause.text, lowered, ctx)
    if result.risk is RiskLevel.FAIR and any(p in lowered for p in ONE_SIDED_PHRASES):
        return RuleResult(
            RiskLevel.MEDIUM,
            "Gives one party a unilateral right ('sole discretion' or 'without reason').",
            "one_sided",
            ONE_SIDED_PHRASES,
        )
    return result
