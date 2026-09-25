"""Tests for leaseguard/segment.py."""

import pytest

from leaseguard.sample import SAMPLE_LEASE
from leaseguard.segment import heading_of, segment_clauses

FILLER = " The parties agree to the terms set out in this clause in full." * 3


@pytest.mark.parametrize(
    "markers",
    [
        ["1.", "2.", "3."],
        ["1)", "2)", "3)"],
        ["I.", "II.", "III."],
        ["Clause 1", "Clause 2", "Clause 3"],
        ["Deposit:", "Rent:", "Entry:"],
    ],
)
def test_heading_styles(markers: list[str]) -> None:
    clauses = segment_clauses("\n".join(f"{m} Heading{FILLER}" for m in markers))
    assert [c.index for c in clauses] == [0, 1, 2]


def test_paragraph_fallback_without_headings() -> None:
    text = "\n\n".join(f"paragraph {i}{FILLER}" for i in range(4))
    assert len(segment_clauses(text)) == 4


def test_wrapped_lines_join_their_clause() -> None:
    deposit = next(c for c in segment_clauses(SAMPLE_LEASE) if "Deposit" in c.heading)
    assert deposit.heading == "3. Security Deposit"
    assert "refunded" in deposit.text


def test_short_fragments_are_skipped() -> None:
    assert segment_clauses("1. a\n2. b\n3. c") == []


def test_heading_of_edge_cases() -> None:
    assert heading_of("IV. Termination: text") == "IV. Termination"
    assert heading_of(":") == "Clause"
