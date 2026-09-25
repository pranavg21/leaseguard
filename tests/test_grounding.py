"""Tests for leaseguard/grounding.py."""

import pytest

from leaseguard.constants import MAX_QUOTE_CHARS
from leaseguard.grounding import best_sentence, normalise, verify_grounding

SOURCE = "The Tenant shall pay a security deposit of Rs. 2,50,000 which shall be refunded."


@pytest.mark.parametrize(
    "quote",
    ["security deposit of Rs. 2,50,000", "SECURITY   deposit\nof Rs. 2,50,000", "“The Tenant shall pay”"],
)
def test_verbatim_quotes_pass(quote: str) -> None:
    assert verify_grounding(quote, SOURCE)


@pytest.mark.parametrize(
    "quote",
    ["tenant must pay a deposit of 2.5 lakh", "security deposit of Rs. 3,50,000", "Tenant", ""],
)
def test_paraphrases_near_misses_and_short_quotes_fail(quote: str) -> None:
    assert not verify_grounding(quote, SOURCE)


def test_normalise() -> None:
    assert normalise("  A\t\n“B” – c ") == 'a "b" - c'


def test_best_sentence_prefers_keywords_and_keeps_rupee_abbreviation() -> None:
    text = "Rent is due monthly. The deposit of Rs. 2,50,000 is refunded in 30 days."
    assert best_sentence(text, ("deposit",)) == "The deposit of Rs. 2,50,000 is refunded in 30 days."


def test_best_sentence_is_truncated() -> None:
    assert len(best_sentence("word " * 500, ())) == MAX_QUOTE_CHARS


def test_normalised_text_is_reusable_and_equivalent() -> None:
    from leaseguard.grounding import NormalisedText, appears_in

    source = NormalisedText(SOURCE)
    assert source.text == normalise(SOURCE)
    assert verify_grounding("security deposit of Rs. 2,50,000", source)
    assert appears_in("Tenant", source)
    assert not appears_in("landlord", source)
