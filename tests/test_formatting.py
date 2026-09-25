"""Tests for leaseguard/formatting.py."""

import pytest

from leaseguard.formatting import indian_rupees


@pytest.mark.parametrize(
    ("amount", "text"),
    [(0, "Rs. 0"), (999, "Rs. 999"), (1000, "Rs. 1,000"), (150_000, "Rs. 1,50,000"), (12_345_678, "Rs. 1,23,45,678")],
)
def test_indian_grouping(amount: int, text: str) -> None:
    assert indian_rupees(amount) == text
