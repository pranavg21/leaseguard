"""Tests for leaseguard/dossier/dates.py."""

from datetime import UTC, date, datetime

import pytest

from leaseguard.dossier.dates import add_years, find_date, make_date, today_ist


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("paid on 05/10/2025", date(2025, 10, 5)),
        ("05-10-25 receipt", date(2025, 10, 5)),
        ("2026-03-31 statement", date(2026, 3, 31)),
        ("12th March 2026", date(2026, 3, 12)),
        ("March 12, 2026", date(2026, 3, 12)),
        ("1 Sept 2026", date(2026, 9, 1)),
        ("on 31/02/2026", None),
        ("in Blorch 2026", None),
        ("no date here", None),
    ],
)
def test_find_date(text: str, expected: date | None) -> None:
    assert find_date(text) == expected


def test_first_date_in_text_wins() -> None:
    assert find_date("12 March 2026 then 01/01/2027") == date(2026, 3, 12)


def test_make_date_and_add_years() -> None:
    assert make_date(26, 1, 2) == date(2026, 1, 2)
    assert make_date(2026, 13, 1) is None
    assert add_years(date(2026, 3, 10), 3) == date(2029, 3, 10)
    assert add_years(date(2028, 2, 29), 3) == date(2031, 2, 28)


def test_today_ist_handles_midnight_window() -> None:
    # 19:00 UTC on 24 Sept is 00:30 IST on 25 Sept (midnight to 05:30 window)
    utc_night = datetime(2026, 9, 24, 19, 0, 0, tzinfo=UTC)
    assert today_ist(utc_night) == date(2026, 9, 25)
    # Naive datetime is treated as UTC
    naive_night = datetime(2026, 9, 24, 19, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    assert today_ist(naive_night) == date(2026, 9, 25)
    # Default without args returns today's date in IST
    assert isinstance(today_ist(), date)


def test_timezone_data_ships_with_the_app() -> None:
    """India's zone must resolve even on slim images without OS tz files (tzdata is a pinned dependency)."""
    import tzdata

    assert tzdata.IANA_VERSION
