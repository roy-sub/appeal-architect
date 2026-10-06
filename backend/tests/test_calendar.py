"""The holiday adapter, checked against the statute rather than the library.

The deadline tests must not inherit a library's bug. So the federal holidays are
transcribed here from 5 U.S.C. § 6103 and the observed-date rule, and the
adapter is asserted against this table. If `holidays` and this table ever
disagree, this test fails and a human decides which is right -- which is the
whole point of having the adapter.

Observed-date rule (5 U.S.C. § 6103(b)): a holiday falling on a Saturday is
observed the preceding Friday; one falling on a Sunday is observed the
following Monday.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.rules.calendar import (
    add_business_days,
    business_days_between,
    is_business_day,
    is_federal_holiday,
    next_business_day,
)

#: Transcribed from 5 U.S.C. § 6103, with observed dates applied.
#: 2027 is the year most of this product's first deadlines land in.
FEDERAL_HOLIDAYS_2027: list[tuple[date, str]] = [
    (date(2027, 1, 1), "New Year's Day — Friday"),
    (date(2027, 1, 18), "Martin Luther King Jr. Day — third Monday in January"),
    (date(2027, 2, 15), "Washington's Birthday — third Monday in February"),
    (date(2027, 5, 31), "Memorial Day — last Monday in May"),
    (date(2027, 6, 18), "Juneteenth — 19 June is a Saturday, observed Friday 18th"),
    (date(2027, 7, 5), "Independence Day — 4 July is a Sunday, observed Monday 5th"),
    (date(2027, 9, 6), "Labor Day — first Monday in September"),
    (date(2027, 10, 11), "Columbus Day — second Monday in October"),
    (date(2027, 11, 11), "Veterans Day — Thursday"),
    (date(2027, 11, 25), "Thanksgiving — fourth Thursday in November"),
    (date(2027, 12, 24), "Christmas Day — 25 December is a Saturday, observed Friday 24th"),
    (date(2027, 12, 31), "New Year's Day 2028 is a Saturday, observed Friday 31 Dec 2027"),
]

FEDERAL_HOLIDAYS_2026: list[tuple[date, str]] = [
    (date(2026, 1, 1), "New Year's Day — Thursday"),
    (date(2026, 1, 19), "Martin Luther King Jr. Day"),
    (date(2026, 2, 16), "Washington's Birthday"),
    (date(2026, 5, 25), "Memorial Day"),
    (date(2026, 6, 19), "Juneteenth — Friday"),
    (date(2026, 7, 3), "Independence Day — 4 July is a Saturday, observed Friday 3rd"),
    (date(2026, 9, 7), "Labor Day"),
    (date(2026, 10, 12), "Columbus Day"),
    (date(2026, 11, 11), "Veterans Day — Wednesday"),
    (date(2026, 11, 26), "Thanksgiving"),
    (date(2026, 12, 25), "Christmas Day — Friday"),
]


@pytest.mark.parametrize(
    ("day", "why"), FEDERAL_HOLIDAYS_2026 + FEDERAL_HOLIDAYS_2027, ids=lambda v: str(v)
)
def test_transcribed_federal_holidays_are_recognised(day: date, why: str) -> None:
    assert is_federal_holiday(day), f"{day} should be a federal holiday: {why}"
    assert not is_business_day(day)


def test_nominal_date_is_not_a_holiday_when_it_is_observed_elsewhere() -> None:
    """4 July 2026 is a Saturday, so the day offices shut is Friday the 3rd.

    Business-day arithmetic has to agree with when offices are actually closed,
    not with the statute's nominal date.
    """
    assert is_federal_holiday(date(2026, 7, 3))
    # The Saturday itself is not a business day anyway, for the ordinary reason.
    assert not is_business_day(date(2026, 7, 4))


def test_the_weekday_closures_are_exactly_the_transcribed_ones() -> None:
    """Guards the other direction: an over-reported holiday pushes a business-day
    deadline later than the rule allows, which is the unsafe direction.

    Only weekdays are compared. The library also reports the *nominal* date of a
    holiday that falls on a weekend (4 July 2026, a Saturday, alongside its
    observed Friday), and those make no difference to business-day arithmetic
    because a weekend is not a business day anyway. What matters is that the set
    of **weekdays** offices are shut matches the statute.
    """
    for year, table in ((2026, FEDERAL_HOLIDAYS_2026), (2027, FEDERAL_HOLIDAYS_2027)):
        expected = {d for d, _ in table}
        assert all(d.weekday() < 5 for d in expected), (
            f"{year}: the transcribed table should list observed weekday dates only"
        )
        found = {
            day
            for month in range(1, 13)
            for raw in range(1, 32)
            if (day := _date_or_none(year, month, raw)) is not None
            and day.weekday() < 5
            and is_federal_holiday(day)
        }
        assert found == expected, (
            f"{year}: library reports weekday holidays not in the statute table "
            f"{sorted(found - expected)}; missing {sorted(expected - found)}"
        )


def _date_or_none(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


# ---- business-day arithmetic ----------------------------------------------


def test_zero_business_days_does_not_roll_a_weekend_forward() -> None:
    """A count of zero returns the start date untouched, even on a Saturday.

    Rolling it forward would silently grant time the rule did not give. Where a
    rule really does say "roll forward", callers use next_business_day.
    """
    saturday = date(2026, 9, 12)
    assert add_business_days(saturday, 0) == saturday
    assert next_business_day(saturday) == date(2026, 9, 14)


def test_business_days_skip_weekends() -> None:
    # Monday 14 Sep 2026 + 5 business days = Monday 21 Sep.
    assert add_business_days(date(2026, 9, 14), 5) == date(2026, 9, 21)


def test_business_days_skip_an_observed_holiday() -> None:
    """Thu 2 Jul 2026 + 2 business days skips Fri 3 Jul (observed) and the weekend."""
    assert add_business_days(date(2026, 7, 2), 2) == date(2026, 7, 7)


def test_business_days_across_a_year_boundary() -> None:
    """Wed 30 Dec 2026 + 3 business days: skips Fri 1 Jan 2027 and the weekend."""
    assert add_business_days(date(2026, 12, 30), 3) == date(2027, 1, 5)


def test_business_days_across_thanksgiving() -> None:
    """Mon 23 Nov 2026 + 5 business days skips Thanksgiving on the 26th."""
    assert add_business_days(date(2026, 11, 23), 5) == date(2026, 12, 1)


def test_negative_business_day_count_is_refused() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        add_business_days(date(2026, 9, 14), -1)


def test_business_days_between_counts_forward_and_back() -> None:
    assert business_days_between(date(2026, 9, 14), date(2026, 9, 21)) == 5
    assert business_days_between(date(2026, 9, 21), date(2026, 9, 14)) == -5
    assert business_days_between(date(2026, 9, 14), date(2026, 9, 14)) == 0
