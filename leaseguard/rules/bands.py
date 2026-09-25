"""Threshold bands shared by numeric rules, so each limit is declared once as data."""

from dataclasses import dataclass

from leaseguard.models import RiskLevel, RuleResult


@dataclass(frozen=True)
class Band:
    """A risk band: values strictly above ``above`` get this rating.

    Attributes:
        above: Exclusive lower bound.
        risk: Rating for values in the band.
        rule_id: Stable rule identifier.
        template: Explanation; ``{value}`` is replaced with the measured value.
    """

    above: float
    risk: RiskLevel
    rule_id: str
    template: str


def grade(value: float | None, bands: tuple[Band, ...], keywords: tuple[str, ...]) -> RuleResult | None:
    """Return the first band (highest first) that the value falls into.

    Args:
        value: The measured value, or None if it could not be found.
        bands: Bands ordered from the highest threshold down.
        keywords: Words used to pick the quoted sentence.

    Returns:
        The matching result, or None if the value is missing or within every limit.
    """
    if value is None:
        return None
    for band in bands:
        if value > band.above:
            return RuleResult(band.risk, band.template.format(value=f"{value:g}"), band.rule_id, keywords)
    return None


def first_phrase(lowered: str, phrases: tuple[str, ...], result: RuleResult) -> RuleResult | None:
    """Return ``result`` if any phrase occurs in the text.

    Args:
        lowered: Lower-case clause text.
        phrases: Phrases that trigger the result.
        result: The result to return on a match.

    Returns:
        The result, or None when no phrase is present.
    """
    return result if any(phrase in lowered for phrase in phrases) else None
