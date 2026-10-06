"""Deadline arithmetic. THE SAFETY-CRITICAL TEST FILE.

A wrong deadline can cost someone their appeal rights permanently. There is no
error message and no second chance: the window closes and they find out later.

So this file is a table of worked examples, each one computed by hand and
commented with the reasoning. It covers leap years, year boundaries,
holiday-adjacent triggers, month-end clamping, and the conservative path under
an ambiguous trigger.

Never let this file go red. Never weaken an assertion to make it pass. If the
code and a case here disagree, work out which is right on paper first.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.route import DayUnit
from app.rules.deadlines import (
    RECEIPT_AMBIGUITY_NOTE,
    TriggerDates,
    TriggerUnavailable,
    add_calendar_days,
    add_hours_as_date,
    add_months,
    days_until,
    resolve_deadline,
    resolve_trigger,
)

# ===========================================================================
# Calendar-day arithmetic
# ===========================================================================

#: (start, days, expected, why). Each hand-computed.
CALENDAR_CASES: list[tuple[date, int, date, str]] = [
    # The product's headline case. The design prototype said 22 Mar 2027, which
    # is nine days late -- someone trusting it could file after their window shut.
    # Sep 16 + Oct 31 + Nov 30 + Dec 31 + Jan 31 + Feb 28 = 167, + 13 = 180.
    (date(2026, 9, 14), 180, date(2027, 3, 13), "the headline case: 2027 is not a leap year"),
    # The same count one year earlier, crossing a leap February.
    # Sep 16 + Oct 31 + Nov 30 + Dec 31 + Jan 31 + Feb 29 = 168, + 12 = 180.
    (date(2023, 9, 14), 180, date(2024, 3, 12), "crosses 29 Feb 2024, so one day earlier"),
    # Leap day as the trigger itself.
    (date(2024, 2, 29), 1, date(2024, 3, 1), "leap day plus one"),
    (date(2024, 2, 29), 365, date(2025, 2, 28), "leap day plus a full year lands 28 Feb"),
    # Year boundary.
    (date(2026, 12, 31), 1, date(2027, 1, 1), "new year's eve plus one"),
    (date(2026, 12, 15), 30, date(2027, 1, 14), "crosses into the new year"),
    # Day one is the day after the trigger, so day zero is the trigger itself.
    (date(2026, 9, 14), 0, date(2026, 9, 14), "zero days is the trigger date itself"),
    # The federal response windows.
    (date(2026, 9, 14), 30, date(2026, 10, 14), "pre-service insurer response"),
    (date(2026, 9, 14), 60, date(2026, 11, 13), "post-service insurer response"),
    (date(2026, 9, 14), 45, date(2026, 10, 29), "standard external review decision"),
    # A February trigger into a leap year.
    (date(2028, 1, 31), 29, date(2028, 2, 29), "lands exactly on leap day"),
    # A trigger immediately before the observed 4 July holiday. Calendar days do
    # not care about holidays, which is the point of the unit being explicit.
    (date(2026, 7, 2), 5, date(2026, 7, 7), "calendar days ignore the holiday weekend"),
]


@pytest.mark.parametrize(("start", "days", "expected", "why"), CALENDAR_CASES)
def test_calendar_day_arithmetic(start: date, days: int, expected: date, why: str) -> None:
    assert add_calendar_days(start, days) == expected, why


def test_the_prototype_deadline_was_wrong_in_the_dangerous_direction() -> None:
    """Pinned explicitly, because this is the error the engine exists to prevent.

    The design prototype showed 22 Mar 2027 / 168 days for a 14 Sep 2026 denial.
    The correct date is 13 Mar 2027. The prototype was NINE DAYS LATE, so a user
    who trusted it would have filed after their window closed.
    """
    correct = add_calendar_days(date(2026, 9, 14), 180)
    assert correct == date(2027, 3, 13)
    assert correct < date(2027, 3, 22), "the prototype's date is later than the real one"
    assert (date(2027, 3, 22) - correct).days == 9


def test_negative_calendar_count_is_refused() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        add_calendar_days(date(2026, 9, 14), -1)


# ===========================================================================
# Month arithmetic — 45 CFR 147.136(d) says "4 months", not 120 days
# ===========================================================================

MONTH_CASES: list[tuple[date, int, date, str]] = [
    (date(2026, 9, 14), 4, date(2027, 1, 14), "the external-review window, same day of month"),
    # Month-end clamping: 31 Jan plus one month is 28 Feb, not 3 March. Clamping
    # down is the conservative direction and is what a court reads "one month" as.
    (date(2027, 1, 31), 1, date(2027, 2, 28), "clamps to the end of a short month"),
    (date(2024, 1, 31), 1, date(2024, 2, 29), "clamps to leap-year February"),
    (date(2026, 10, 31), 4, date(2027, 2, 28), "four months from 31 Oct clamps to 28 Feb"),
    (date(2026, 11, 30), 4, date(2027, 3, 30), "30 Nov + 4 months"),
    (date(2026, 12, 31), 4, date(2027, 4, 30), "31 Dec + 4 months clamps to 30 Apr"),
]


@pytest.mark.parametrize(("start", "months", "expected", "why"), MONTH_CASES)
def test_month_arithmetic(start: date, months: int, expected: date, why: str) -> None:
    assert add_months(start, months) == expected, why


def test_four_months_is_not_one_hundred_and_twenty_days() -> None:
    """The distinction the spec insists on, pinned.

    Treating "4 months" as 120 days would be our invention rather than the
    rule's, and in this case it shortens the window by five days.
    """
    start = date(2026, 9, 14)
    assert add_months(start, 4) == date(2027, 1, 14)
    assert add_calendar_days(start, 120) == date(2027, 1, 12)
    assert add_months(start, 4) != add_calendar_days(start, 120)


# ===========================================================================
# Hour arithmetic — "not later than 72 hours"
# ===========================================================================


def test_seventy_two_hours_is_three_days_not_four() -> None:
    """Rounds down. Rounding up would hand the user a day the rule did not give."""
    assert add_hours_as_date(date(2026, 9, 14), 72) == date(2026, 9, 17)


def test_hours_round_down_to_whole_days() -> None:
    assert add_hours_as_date(date(2026, 9, 14), 23) == date(2026, 9, 14)
    assert add_hours_as_date(date(2026, 9, 14), 24) == date(2026, 9, 15)
    assert add_hours_as_date(date(2026, 9, 14), 47) == date(2026, 9, 15)


def test_hour_window_crosses_a_year_boundary() -> None:
    assert add_hours_as_date(date(2026, 12, 30), 72) == date(2027, 1, 2)


# ===========================================================================
# Triggers, and the conservative path under ambiguity
# ===========================================================================


def test_unknown_receipt_date_takes_the_earlier_date_and_discloses_it() -> None:
    """Spec 6.4. The regulation counts from receipt; we usually do not know it.

    Counting from the letter's own date gives the earlier -- therefore safer --
    deadline, and the user is told, because a conservative date presented as
    certain is still a misrepresentation.
    """
    dates = TriggerDates(denial_date=date(2026, 9, 14))
    trigger_date, description, ambiguous, note = resolve_trigger("denial_received_date", dates)

    assert trigger_date == date(2026, 9, 14)
    assert ambiguous is True
    assert note == RECEIPT_AMBIGUITY_NOTE
    assert "earlier" in note
    assert "check the date against your own letter" in note.lower()
    assert "printed on your denial letter" in description


def test_known_receipt_date_is_used_and_is_not_ambiguous() -> None:
    """With receipt known the trigger is determined, so nothing is flagged.

    It is also the later date, which is correct: the rule says receipt, and we
    are not entitled to shorten a window we know the real start of.
    """
    dates = TriggerDates(denial_date=date(2026, 9, 14), denial_received_date=date(2026, 9, 19))
    trigger_date, _, ambiguous, note = resolve_trigger("denial_received_date", dates)

    assert trigger_date == date(2026, 9, 19)
    assert ambiguous is False
    assert note is None


def test_the_conservative_reading_is_genuinely_the_earlier_deadline() -> None:
    """The property that makes the fallback safe, asserted rather than assumed."""
    known = resolve_deadline(
        count=180,
        unit=DayUnit.CALENDAR,
        trigger="denial_received_date",
        dates=TriggerDates(denial_date=date(2026, 9, 14), denial_received_date=date(2026, 9, 21)),
    )
    unknown = resolve_deadline(
        count=180,
        unit=DayUnit.CALENDAR,
        trigger="denial_received_date",
        dates=TriggerDates(denial_date=date(2026, 9, 14)),
    )
    assert unknown.due_date < known.due_date
    assert unknown.ambiguous and not known.ambiguous


def test_denial_date_trigger_is_never_ambiguous() -> None:
    dates = TriggerDates(denial_date=date(2026, 9, 14))
    _, _, ambiguous, note = resolve_trigger("denial_date", dates)
    assert ambiguous is False and note is None


def test_a_trigger_that_has_not_happened_yet_refuses_to_be_dated() -> None:
    """No placeholder date for the external review before the internal appeal ends.

    Dating it from the original denial produced a decision date BEFORE the
    request date -- visibly nonsense, and the invisible version of the same error
    is a date a user might act on.
    """
    dates = TriggerDates(denial_date=date(2026, 9, 14))
    with pytest.raises(TriggerUnavailable) as caught:
        resolve_trigger("final_adverse_date", dates)
    assert "has not happened yet" in caught.value.explanation


def test_final_adverse_date_is_used_once_it_exists() -> None:
    dates = TriggerDates(denial_date=date(2026, 9, 14), final_adverse_date=date(2027, 1, 20))
    resolved = resolve_deadline(
        count=4, unit=DayUnit.MONTHS, trigger="final_adverse_date", dates=dates
    )
    assert resolved.due_date == date(2027, 5, 20)
    assert resolved.ambiguous is False


def test_service_date_trigger_without_a_service_date_refuses() -> None:
    with pytest.raises(TriggerUnavailable):
        resolve_trigger("service_date", TriggerDates(denial_date=date(2026, 9, 14)))


def test_an_unknown_trigger_name_is_a_bug_not_a_default() -> None:
    with pytest.raises(ValueError, match="unknown deadline trigger"):
        resolve_trigger("whenever", TriggerDates(denial_date=date(2026, 9, 14)))


# ===========================================================================
# resolve_deadline — the full path, including the business-day unit
# ===========================================================================


def test_business_day_unit_skips_a_holiday_adjacent_trigger() -> None:
    """A business-day window starting beside the observed 4 July holiday.

    From Thu 2 Jul 2026, counting business days only:
        Fri 3 Jul   observed Independence Day   — skipped
        Sat 4, Sun 5                            — skipped
        Mon 6 Jul   business day 1
        Tue 7 Jul   business day 2
        Wed 8 Jul   business day 3
        Thu 9 Jul   business day 4
        Fri 10 Jul  business day 5              <- the answer
    """
    resolved = resolve_deadline(
        count=5,
        unit=DayUnit.BUSINESS,
        trigger="denial_date",
        dates=TriggerDates(denial_date=date(2026, 7, 2)),
    )
    assert resolved.due_date == date(2026, 7, 10)
    assert "business days" in resolved.trigger_description


def test_calendar_and_business_units_differ_and_are_never_interchanged() -> None:
    """Calendar vs business is explicit per item, never inferred."""
    dates = TriggerDates(denial_date=date(2026, 7, 2))
    calendar = resolve_deadline(count=5, unit=DayUnit.CALENDAR, trigger="denial_date", dates=dates)
    business = resolve_deadline(count=5, unit=DayUnit.BUSINESS, trigger="denial_date", dates=dates)
    # Five calendar days from Thu 2 Jul is Tue 7 Jul. Five business days, with
    # the observed holiday and the weekend skipped, is Fri 10 Jul -- three days
    # later. Inferring the unit instead of reading it from the table would move a
    # real deadline by three days.
    assert calendar.due_date == date(2026, 7, 7)
    assert business.due_date == date(2026, 7, 10)
    assert calendar.due_date < business.due_date


@pytest.mark.parametrize("unit", list(DayUnit))
def test_every_unit_is_handled(unit: DayUnit) -> None:
    """A unit added to the enum but not to the resolver would be a silent bug."""
    resolved = resolve_deadline(
        count=3,
        unit=unit,
        trigger="denial_date",
        dates=TriggerDates(denial_date=date(2026, 9, 14)),
    )
    assert resolved.due_date >= date(2026, 9, 14)
    assert resolved.trigger_description


def test_resolve_deadline_accepts_the_unit_as_a_string() -> None:
    """The ASP layer hands over a string, so the string path is the real one."""
    resolved = resolve_deadline(
        count=180,
        unit="calendar",
        trigger="denial_date",
        dates=TriggerDates(denial_date=date(2026, 9, 14)),
    )
    assert resolved.due_date == date(2027, 3, 13)


def test_an_unknown_unit_is_refused() -> None:
    with pytest.raises(ValueError):
        resolve_deadline(
            count=1,
            unit="fortnights",
            trigger="denial_date",
            dates=TriggerDates(denial_date=date(2026, 9, 14)),
        )


# ===========================================================================
# days_until — the one piece of arithmetic the frontend mirrors
# ===========================================================================


def test_days_until_counts_down_and_goes_negative_after_the_window_shuts() -> None:
    due = date(2027, 3, 13)
    assert days_until(due, date(2026, 10, 6)) == 158
    assert days_until(due, due) == 0
    assert days_until(due, date(2027, 3, 14)) == -1


def test_days_until_for_the_headline_case_is_not_the_prototypes_number() -> None:
    """The prototype claimed 168 days. From its own stated 'today' it is 159."""
    due = add_calendar_days(date(2026, 9, 14), 180)
    assert days_until(due, date(2026, 10, 5)) == 159
