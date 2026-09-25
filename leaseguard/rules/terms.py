"""Rules for tenure terms: lock-in, notice and landlord entry."""

import re

from leaseguard.constants import LOCK_IN_FAIR_MONTHS, LOCK_IN_HIGH_MONTHS, NOTICE_MAX_MONTHS
from leaseguard.models import RiskLevel, RuleResult, UserContext
from leaseguard.parsing import parse_months
from leaseguard.rules.bands import Band, first_phrase, grade

_LOCK_IN_WORDS = ("lock-in", "lock in", "notice", "months", "forfeit")
_ENTRY_WORDS = ("enter", "entry", "inspect", "notice", "any time")
_NO_NOTICE = ("without notice", "without prior notice", "at any time")

LOCK_IN_BANDS = (
    Band(
        LOCK_IN_HIGH_MONTHS, RiskLevel.HIGH, "lock_in_above_12_months", "A {value}-month lock-in is far above 6 months."
    ),
    Band(
        LOCK_IN_FAIR_MONTHS,
        RiskLevel.MEDIUM,
        "lock_in_above_6_months",
        "A {value}-month lock-in is longer than 6 months.",
    ),
)
NOTICE_BANDS = (
    Band(
        NOTICE_MAX_MONTHS,
        RiskLevel.MEDIUM,
        "notice_above_2_months",
        "A {value}-month notice period exceeds 1-2 months.",
    ),
)

FORFEITURE = RuleResult(
    RiskLevel.HIGH, "Leaving early forfeits the deposit or other money.", "lock_in_forfeiture", ("forfeit",)
)
LOCK_IN_FAIR = RuleResult(RiskLevel.FAIR, "Lock-in and notice are within the baseline.", "lock_in_fair", _LOCK_IN_WORDS)
ENTRY_WITHOUT_NOTICE = RuleResult(
    RiskLevel.HIGH, "The landlord may enter without notice.", "entry_without_notice", _NO_NOTICE
)
ENTRY_NO_PERIOD = RuleResult(RiskLevel.MEDIUM, "No notice period for entry is stated.", "entry_no_period", _ENTRY_WORDS)
ENTRY_FAIR = RuleResult(RiskLevel.FAIR, "Entry requires notice, in line with the baseline.", "entry_fair", _ENTRY_WORDS)


def rule_lock_in(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate a lock-in and notice clause: forfeiture, lock-in length, then notice length.

    Args:
        raw: Original clause text.
        lowered: Lower-case clause text.
        ctx: The user's context (unused; kept for a uniform rule signature).

    Returns:
        The rule outcome.
    """
    del ctx
    lock = parse_months(raw, "lock-in period", "lock in period", "lock-in", "lock in")
    notice = parse_months(raw, "notice period", "notice of", "notice")
    return (
        first_phrase(lowered, ("forfeit",), FORFEITURE)
        or grade(lock, LOCK_IN_BANDS, _LOCK_IN_WORDS)
        or grade(notice, NOTICE_BANDS, _LOCK_IN_WORDS)
        or LOCK_IN_FAIR
    )


def rule_entry(raw: str, lowered: str, ctx: UserContext) -> RuleResult:
    """Rate a landlord-entry clause: entry without notice, no stated period, or fair.

    Args:
        raw: Original clause text (unused; kept for a uniform rule signature).
        lowered: Lower-case clause text.
        ctx: The user's context (unused).

    Returns:
        The rule outcome.
    """
    del raw, ctx
    has_period = re.search(r"\d+\s*hours|notice", lowered) is not None
    return first_phrase(lowered, _NO_NOTICE, ENTRY_WITHOUT_NOTICE) or (ENTRY_FAIR if has_period else ENTRY_NO_PERIOD)
