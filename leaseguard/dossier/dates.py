"""Deterministic date parsing. Dates are never produced by a language model."""

import re
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from leaseguard.constants import TWO_DIGIT_YEAR_BASE, TWO_DIGIT_YEAR_LIMIT

INDIA_TZ = ZoneInfo("Asia/Kolkata")

_MONTHS = {
    name: number
    for number, names in enumerate(
        (
            ("jan", "january"),
            ("feb", "february"),
            ("mar", "march"),
            ("apr", "april"),
            ("may",),
            ("jun", "june"),
            ("jul", "july"),
            ("aug", "august"),
            ("sep", "sept", "september"),
            ("oct", "october"),
            ("nov", "november"),
            ("dec", "december"),
        ),
        start=1,
    )
    for name in names
}
_NUMERIC = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DAY_MONTH = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
_MONTH_DAY = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")


def make_date(year: int, month: int, day: int) -> date | None:
    """Build a date, expanding two-digit years and rejecting impossible dates.

    Args:
        year: Year (two or four digits).
        month: Month number.
        day: Day of month.

    Returns:
        The date, or None if it does not exist.
    """
    full_year = year + TWO_DIGIT_YEAR_BASE if year < TWO_DIGIT_YEAR_LIMIT else year
    try:
        return date(full_year, month, day)
    except ValueError:
        return None


def _named(day: str, month_name: str, year: str) -> date | None:
    month = _MONTHS.get(month_name.lower())
    return make_date(int(year), month, int(day)) if month else None


def find_date(text: str) -> date | None:
    """Return the first date written in the text, reading numeric dates day-first (Indian style).

    Args:
        text: Any text.

    Returns:
        The date, or None if none is found.
    """
    candidates: list[tuple[int, date | None]] = []
    if match := _ISO.search(text):
        candidates.append((match.start(), make_date(int(match[1]), int(match[2]), int(match[3]))))
    if match := _NUMERIC.search(text):
        candidates.append((match.start(), make_date(int(match[3]), int(match[2]), int(match[1]))))
    if match := _DAY_MONTH.search(text):
        candidates.append((match.start(), _named(match[1], match[2], match[3])))
    if match := _MONTH_DAY.search(text):
        candidates.append((match.start(), _named(match[2], match[1], match[3])))
    found = [(position, value) for position, value in candidates if value is not None]
    return min(found, key=lambda pair: pair[0])[1] if found else None


def add_years(start: date, years: int) -> date:
    """Add whole years, moving 29 February to 28 February when needed.

    Args:
        start: The starting date.
        years: Years to add.

    Returns:
        The later date.
    """
    try:
        return start.replace(year=start.year + years)
    except ValueError:
        return start.replace(year=start.year + years, day=28)


def today_ist(now: datetime | None = None) -> date:
    """Return the calendar date in Indian Standard Time (UTC+05:30).

    On Cloud Run, servers run in UTC. A notice generated between midnight and
    05:30 IST would print yesterday's date if date.today() were used.

    Args:
        now: Optional datetime (defaults to current UTC time).

    Returns:
        Current calendar date in India.
    """
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(INDIA_TZ).date()
