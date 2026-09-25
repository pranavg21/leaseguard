"""Tests for leaseguard/summary.py."""

from leaseguard.ai import OfflineClient
from leaseguard.engine import analyse
from leaseguard.grounding import verify_grounding
from leaseguard.models import UserContext
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED
from leaseguard.summary import NOT_STATED, key_terms

FILLER = " The parties agree to these terms in full." * 20


def terms(text: str, rent: int | None = 25_000) -> dict[str, tuple[str, str]]:
    report = analyse(text, UserContext(monthly_rent=rent), OfflineClient())
    return {t.label: (t.value, t.quote) for t in key_terms(report)}


def test_sample_key_terms_are_exact() -> None:
    found = terms(SAMPLE_LEASE)
    assert found["Monthly rent"][0] == "Rs. 25,000"
    assert found["Security deposit"][0] == "Rs. 2,50,000, about 10 months' rent"
    assert found["Agreement term"][0] == "11 months"
    assert found["Lock-in"][0] == "11 months"
    assert found["Notice period"][0] == "3 months"
    assert found["Rent increase"][0] == "15%"


def test_every_quote_is_verbatim_from_the_agreement() -> None:
    for text in (SAMPLE_LEASE, SAMPLE_LEASE_REVISED):
        for value, quote in terms(text).values():
            assert value == NOT_STATED or verify_grounding(quote, text)


def test_singular_month_and_months_only_deposit() -> None:
    found = terms(SAMPLE_LEASE_REVISED)
    assert found["Notice period"][0] == "1 month"
    assert found["Security deposit"][0] == "about 2 months' rent"


def test_missing_terms_are_marked_not_stated() -> None:
    text = "1. Use: The flat is for residential use only." + FILLER + "\n2. Pets: No pets." + FILLER
    found = terms(text, rent=None)
    assert all(value == NOT_STATED and quote == "" for value, quote in found.values())
