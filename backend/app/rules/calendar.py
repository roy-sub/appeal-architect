"""US federal holidays and business-day arithmetic.

The build spec names ``workalendar``. It cannot be installed: its transitive
dependency ``pymeeus`` fails to build on Python 3.13. ``holidays`` is the
substitute, and it lives behind this one module so the source stays swappable.

The adapter is tested against a hardcoded table transcribed from 5 U.S.C. § 6103
in ``tests/test_calendar.py``, so the deadline tests do not depend on any
library being correct. If the library and the table ever disagree, the test
fails and a human decides which is right.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import holidays

#: Weekday numbers Monday=0 .. Sunday=6.
_WEEKEND = {5, 6}


@lru_cache(maxsize=32)
def _calendar(year: int) -> holidays.HolidayBase:
    """Federal holidays for one year, with observed-date shifting applied.

    ``observed=True`` matters: when 4 July falls on a Saturday the federal
    holiday is observed on the Friday, and that Friday is the day offices are
    shut. Business-day arithmetic has to agree with reality, not the statute's
    nominal date.
    """
    # `holidays` ships no stubs for its per-country classes, so mypy cannot see
    # UnitedStates. The adapter's behaviour is pinned by tests/test_calendar.py
    # against the statute, which is a stronger guarantee than a type stub.
    return holidays.country_holidays("US", years=year, observed=True)


def is_federal_holiday(day: date) -> bool:
    return day in _calendar(day.year)


def holiday_name(day: date) -> str | None:
    return _calendar(day.year).get(day)


def is_business_day(day: date) -> bool:
    """A weekday that is not an observed federal holiday."""
    return day.weekday() not in _WEEKEND and not is_federal_holiday(day)


def add_business_days(start: date, count: int) -> date:
    """``count`` business days after ``start``, not counting ``start`` itself.

    ``count`` of 0 returns ``start`` unchanged, even when ``start`` is a weekend
    -- rolling it forward would silently grant time the rule did not give.
    Use :func:`next_business_day` when a roll-forward is what the rule says.
    """
    if count < 0:
        raise ValueError("count must not be negative")
    day = start
    remaining = count
    while remaining > 0:
        day += timedelta(days=1)
        if is_business_day(day):
            remaining -= 1
    return day


def next_business_day(day: date) -> date:
    """``day`` itself if it is a business day, otherwise the next one.

    Used only where a rule explicitly says a deadline falling on a weekend or
    holiday rolls forward. It is never applied by default: assuming a
    roll-forward that the regulation does not grant would hand the user days
    they do not have.
    """
    while not is_business_day(day):
        day += timedelta(days=1)
    return day


def business_days_between(start: date, end: date) -> int:
    """Business days strictly after ``start`` up to and including ``end``.

    Negative when ``end`` precedes ``start``.
    """
    if end == start:
        return 0
    step = 1 if end > start else -1
    sign = step
    day = start
    count = 0
    while day != end:
        day += timedelta(days=step)
        if is_business_day(day):
            count += 1
    return count * sign
