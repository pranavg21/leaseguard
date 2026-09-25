"""Extract rupee amounts, month counts and percentages from clause text."""

import re

from leaseguard.constants import MONTH_WINDOW_CHARS

_NUMBER = r"(\d+(?:\.\d+)?)"
_MONTHS = re.compile(_NUMBER + r"\s*(?:\(\d+\)\s*)?months?")
_PERCENT = re.compile(_NUMBER + r"\s*(?:%|per\s*cent|percent)", re.IGNORECASE)
_RUPEES = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+)", re.IGNORECASE)
_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "eighteen": 18,
    "twenty-four": 24,
}
_WORD_PATTERN = re.compile(r"\b(" + "|".join(_WORD_NUMBERS) + r")\b")


def words_to_digits(text: str) -> str:
    """Lower-case text and replace number words ("six") with digits ("6").

    Args:
        text: Clause text.

    Returns:
        Lower-case text with number words converted.
    """
    return _WORD_PATTERN.sub(lambda m: str(_WORD_NUMBERS[m.group(1)]), text.lower())


def parse_amount(text: str) -> int | None:
    """Return the first rupee amount (₹, Rs. or INR), ignoring Indian digit grouping.

    Args:
        text: Clause text.

    Returns:
        The amount in rupees, or None if there is none.
    """
    match = _RUPEES.search(text)
    digits = match.group(1).replace(",", "") if match else ""
    return int(digits) if digits.isdigit() else None


def parse_months(text: str, *anchors: str) -> float | None:
    """Return the month count that closely follows the first matching anchor phrase.

    Only a short window after each anchor is searched, so a heading such as
    "Lock-in and Notice:" does not capture a number that belongs to a later
    sentence.

    Args:
        text: Clause text.
        *anchors: Phrases to try in order, such as "notice period".

    Returns:
        The number of months, or None.
    """
    lowered = words_to_digits(text)
    for anchor in anchors:
        start = lowered.find(anchor)
        while start != -1:
            end = start + len(anchor)
            found = _MONTHS.search(lowered[end : end + MONTH_WINDOW_CHARS])
            if found:
                return float(found.group(1))
            start = lowered.find(anchor, end)
    return None


def parse_percent(text: str) -> float | None:
    """Return the first percentage in the text.

    Args:
        text: Clause text.

    Returns:
        The percentage, or None.
    """
    match = _PERCENT.search(text)
    return float(match.group(1)) if match else None
