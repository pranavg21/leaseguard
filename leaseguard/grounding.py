"""Verify that every quote shown to the user exists verbatim in the source."""

import re
import unicodedata

from leaseguard.constants import MAX_QUOTE_CHARS, MIN_QUOTE_CHARS

_WHITESPACE = re.compile(r"\s+")

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
    return _WHITESPACE.sub(" ", text).strip().lower()


class NormalisedText:
    """A source text normalised once, so many quotes can be checked against it cheaply.

    Normalising a whole document is linear in its length; doing it once per
    analysis instead of once per quote keeps grounding linear overall.
    """

    __slots__ = ("text",)

    def __init__(self, raw: str) -> None:
        """Normalise the source.

        Args:
            raw: The original text.
        """
        self.text = normalise(raw)


def _normalised(source: "str | NormalisedText") -> str:
    return source.text if isinstance(source, NormalisedText) else normalise(source)


def verify_grounding(quote: str, source: "str | NormalisedText") -> bool:
    """Check that a quote is a normalised substring of the source.

    Paraphrases, corrected typos and invented text all fail, as do quotes
    too short to prove anything.

    Args:
        quote: Text claimed to come from the source.
        source: The original document text, or a pre-normalised copy.

    Returns:
        True only if the quote appears in the source.
    """
    candidate = normalise(quote).strip(" \"'.")
    return len(candidate) >= MIN_QUOTE_CHARS and candidate in _normalised(source)


def appears_in(quote: str, source: "str | NormalisedText") -> bool:
    """Check that a non-empty quote occurs in the source after normalisation, with no minimum length.

    Used for evidence messages, which are copied verbatim by the parser and may be short.

    Args:
        quote: Text claimed to come from the source.
        source: The original text, or a pre-normalised copy.

    Returns:
        True only if the normalised quote is non-empty and found in the source.
    """
    candidate = normalise(quote)
    return bool(candidate) and candidate in _normalised(source)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences without breaking abbreviations such as "Rs. 2,50,000".

    Args:
        text: Any text.

    Returns:
        Stripped, non-empty sentences in order.
    """
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


def sentence_with(text: str, phrases: tuple[str, ...]) -> str:
    """Return the first sentence that contains any of the phrases, verbatim.

    Args:
        text: Any text.
        phrases: Lower-case phrases to look for.

    Returns:
        The sentence, or an empty string if none matches.
    """
    return next((s for s in split_sentences(text) if any(p in s.lower() for p in phrases)), "")


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
    sentences = split_sentences(text) or [text]
    best = max(reversed(sentences), key=lambda s: sum(k in s.lower() for k in keywords))
    return best[:MAX_QUOTE_CHARS]
