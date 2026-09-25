"""Tests for leaseguard/parsing.py."""

from leaseguard.parsing import parse_amount, parse_months, parse_percent, words_to_digits


def test_words_to_digits() -> None:
    assert words_to_digits("Six months and TWELVE days") == "6 months and 12 days"


def test_parse_amount() -> None:
    assert parse_amount("deposit of Rs. 2,50,000") == 250_000
    assert parse_amount("deposit of ₹60,000") == 60_000
    assert parse_amount("INR 5000") == 5000
    assert parse_amount("no amount") is None


def test_parse_months_uses_nearest_anchor() -> None:
    text = "Lock-in and Notice: a lock-in period of 6 months. Notice period of 2 (two) months."
    assert parse_months(text, "lock-in period") == 6
    assert parse_months(text, "notice period") == 2
    assert parse_months("nothing here", "notice") is None


def test_parse_months_tries_anchors_in_order() -> None:
    assert parse_months("term of eleven months", "missing", "term of") == 11


def test_parse_percent() -> None:
    assert parse_percent("increase of 7.5 per cent") == 7.5
    assert parse_percent("by 10%") == 10
    assert parse_percent("no figure") is None
