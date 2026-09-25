"""Local PII scrubbing applied before any text is sent to an AI service."""

import re

# Order matters: Aadhaar is replaced before phone numbers so a 12-digit
# Aadhaar number is never partly matched as a phone number.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("[PAN]", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    ("[AADHAAR]", re.compile(r"\b[2-9][0-9]{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b")),
    ("[PHONE]", re.compile(r"(?<![\w₹])(?:\+91[\s-]?|0)?[6-9][0-9]{4}[\s-]?[0-9]{5}\b")),
)


def scrub_pii(text: str) -> str:
    """Replace Aadhaar, PAN, Indian mobile numbers and emails with placeholders.

    Args:
        text: Text that may contain personal identifiers.

    Returns:
        The text with identifiers replaced by ``[EMAIL]``, ``[PAN]``,
        ``[AADHAAR]`` or ``[PHONE]``.
    """
    for placeholder, pattern in _PATTERNS:
        text = pattern.sub(placeholder, text)
    return text
