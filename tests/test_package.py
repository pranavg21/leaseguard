"""Tests for leaseguard/__init__.py, constants.py, knowledge.py and sample.py."""

import leaseguard
from leaseguard import constants
from leaseguard.knowledge import (
    BASELINE,
    CATEGORY_KEYWORDS,
    CATEGORY_TITLES,
    EXPECTED_CATEGORIES,
    LAWYER_QUESTIONS,
    STATES,
)
from leaseguard.models import Category
from leaseguard.sample import SAMPLE_LEASE, SAMPLE_LEASE_REVISED


def test_version_is_semantic() -> None:
    assert leaseguard.__version__.count(".") == 2


def test_thresholds_are_ordered() -> None:
    assert constants.DEPOSIT_CAP_MONTHS < constants.DEPOSIT_HIGH_MONTHS
    assert constants.LOCK_IN_FAIR_MONTHS < constants.LOCK_IN_HIGH_MONTHS
    assert constants.ESCALATION_FAIR_PCT < constants.ESCALATION_HIGH_PCT
    assert constants.MAX_UPLOAD_BYTES < constants.MAX_REQUEST_BYTES
    assert constants.MIN_TEXT_CHARS < constants.MAX_TEXT_CHARS


def test_every_category_has_title_baseline_and_question() -> None:
    for category in Category:
        assert CATEGORY_TITLES[category]
        assert BASELINE[category]
        assert LAWYER_QUESTIONS[category].endswith("?")


def test_keywords_cover_every_expected_category() -> None:
    assert set(EXPECTED_CATEGORIES) <= set(CATEGORY_KEYWORDS)
    assert Category.OTHER not in CATEGORY_KEYWORDS


def test_states_include_fallback() -> None:
    assert "Maharashtra" in STATES
    assert STATES[-1] == "Other"


def test_samples_are_long_enough_to_analyse() -> None:
    assert len(SAMPLE_LEASE) > constants.MIN_TEXT_CHARS
    assert len(SAMPLE_LEASE_REVISED) > constants.MIN_TEXT_CHARS
