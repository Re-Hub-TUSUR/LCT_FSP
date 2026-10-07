"""Age and work-experience arithmetic for the resume (ТЗ: under 14 is refused, 14–17 is marked
«до 18»)."""

from collections.abc import Iterable
from datetime import date

MIN_AGE = 14
ADULT_AGE = 18


def age_on(birth: date, today: date | None = None) -> int:
    today = today or date.today()
    before_birthday = (today.month, today.day) < (birth.month, birth.day)
    return today.year - birth.year - int(before_birthday)


def _month_index(value: str) -> int:
    year, month = value.split("-")
    return int(year) * 12 + int(month) - 1


def experience_years(periods: Iterable[tuple[str, str | None]], today: date | None = None) -> int:
    """Whole years worked; overlapping jobs count once. Months are "YYYY-MM", None = now."""
    today = today or date.today()
    now = today.year * 12 + today.month - 1
    spans = sorted(
        (_month_index(start), min(_month_index(end) if end else now, now) + 1)
        for start, end in periods
    )
    months = 0
    current_start, current_end = None, None
    for start, end in spans:
        if current_end is None or start > current_end:
            if current_start is not None and current_end is not None:
                months += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_start is not None and current_end is not None:
        months += max(current_end - current_start, 0)
    return months // 12
