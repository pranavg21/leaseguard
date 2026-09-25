"""Tests for leaseguard/classifier.py."""

import pytest

from leaseguard.classifier import classify_all, classify_offline
from leaseguard.models import Category
from tests.conftest import make_clause


@pytest.mark.parametrize(
    ("heading", "text", "expected"),
    [
        ("Security Deposit", "The tenant pays a deposit", Category.DEPOSIT),
        ("Entry", "The landlord may enter to inspect", Category.ENTRY),
        ("Disputes", "Disputes go to arbitration", Category.JURISDICTION),
        ("Rent Escalation", "Rent will increase yearly", Category.ESCALATION),
        ("Use", "Residential use only", Category.OTHER),
    ],
)
def test_classify_offline(heading: str, text: str, expected: Category) -> None:
    assert classify_offline(make_clause(text, heading)) is expected


def test_heading_outweighs_body_mentions() -> None:
    clause = make_clause("Repairs to be done; damage is not covered by the deposit.", "Maintenance")
    assert classify_offline(clause) is Category.MAINTENANCE


def test_classify_all_maps_every_index() -> None:
    clauses = [make_clause("deposit", index=0), make_clause("residential use", index=1)]
    assert classify_all(clauses) == {0: Category.DEPOSIT, 1: Category.OTHER}
