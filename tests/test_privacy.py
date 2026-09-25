"""Tests for leaseguard/privacy.py."""

import pytest

from leaseguard.privacy import scrub_pii


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Aadhaar 2345 6789 0123 given", "Aadhaar [AADHAAR] given"),
        ("Aadhaar 2345-6789-0123", "Aadhaar [AADHAAR]"),
        ("PAN ABCDE1234F", "PAN [PAN]"),
        ("call +91 98765 43210", "call [PHONE]"),
        ("call 9876543210 now", "call [PHONE] now"),
        ("mail owner.name@example.co.in", "mail [EMAIL]"),
    ],
)
def test_identifiers_are_replaced(raw: str, expected: str) -> None:
    assert scrub_pii(raw) == expected


def test_rupee_amounts_and_dates_are_kept() -> None:
    text = "rent of Rs. 25,000 and ₹2,50,000 from 1 October 2026"
    assert scrub_pii(text) == text
