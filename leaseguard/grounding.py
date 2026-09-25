"""Verify that every quote shown to the user exists verbatim in the source."""

import re
import unicodedata

from leaseguard.constants import MAX_QUOTE_CHARS, MIN_QUOTE_CHARS

_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-"})
# Split after a sentence-ending letter so "Rs. 2,50,000" is never split.
_SENTENCE_END = re.compile(r"(?<=[a-z)\]][.;])\s+(?=[A-Z(])")


def normalise(text: str) -> str:
    """Normalise unicode, smart quotes, dashes, case and whitespace.

    Args:
        text: Any text.

    Returns:
        A comparison-friendly form of the text.
    """
    text = unicodedata.normalize("NFKC", text).translate(_QUOTES)
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_grounding(quote: str, source: str) -> bool:
    """Check that a quote is a normalised substring of the source.

    Paraphrases, corrected typos and invented text all fail, as do quotes
    too short to prove anything.

    Args:
        quote: Text claimed to come from the source.
        source: The original document text.

    Returns:
        True only if the quote appears in the source.
    """
    candidate = normalise(quote).strip(" \"'.")
    return len(candidate) >= MIN_QUOTE_CHARS and candidate in normalise(source)


def appears_in(quote: str, source: str) -> bool:
    """Check that a non-empty quote occurs in the source after normalisation, with no minimum length.

    Used for evidence messages, which are copied verbatim by the parser and may be short.

    Args:
        quote: Text claimed to come from the source.
        source: The original text.

    Returns:
        True only if the normalised quote is non-empty and found in the source.
    """
    candidate = normalise(quote)
    return bool(candidate) and candidate in normalise(source)


def best_sentence(text: str, keywords: tuple[str, ...]) -> str:
    """Pick the sentence that mentions the most keywords, copied verbatim.

    Ties go to the later sentence, so a first sentence that only carries the
    heading does not win by default.

    Args:
        text: Clause text.
        keywords: Lower-case words that signal relevance.

    Returns:
        One sentence from ``text``, truncated to the maximum quote length.
    """
    sentences = [s.strip() for s in _SENTENCE_END.split(text) if s.strip()] or [text]
    best = max(reversed(sentences), key=lambda s: sum(k in s.lower() for k in keywords))
    return best[:MAX_QUOTE_CHARS]
