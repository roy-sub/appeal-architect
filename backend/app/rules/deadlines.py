"""Deadline arithmetic. Safety-critical -- read the whole module before editing.

A wrong deadline can cost someone their appeal rights permanently. There is no
recovering from it, no error message, and no second chance: the door closes and
the user finds out later.

So this module holds pure functions only, with no I/O and no dependency on the
solver. The ASP layer produces ``(item, count, unit, trigger)``; this resolves it
to a date. ``tests/test_deadlines.py`` runs it against a table of worked examples
and is the test you never let go red.

Three rules it obeys:

1. **Calendar versus business days is explicit per item, never inferred.** The
   unit comes from the transcribed table, not from a guess about what a
   regulation probably meant.
2. **Months are months, hours are hours.** 45 CFR 147.136(d) says "4 months",
   which is not 120 days. (b)(2)(ii)(B) says "72 hours", which is not 3 calendar
   days. Converting either would be our invention rather than the rule's.
3. **Under ambiguity, take the earlier date and say so.** Where the regulation's
   trigger is unclear, the conservative reading wins and the result carries a
   note the UI must display.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from app.domain.route import DayUnit
from app.rules.calendar import add_business_days

# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------


class TriggerUnavailable(Exception):
    """The date this deadline counts from has not happened yet.

    Raised rather than substituting a placeholder. A route that dates the
    external-review decision from the original denial letter produces a decision
    date *before* the request date, which is visibly nonsense -- and the
    invisible version of the same error is a date a user might act on. The step
    is shown undated instead, reading "starts after step 1", which is what the
    design specifies and what is actually true.
    """

    def __init__(self, trigger: str, explanation: str) -> None:
        super().__init__(explanation)
        self.trigger = trigger
        self.explanation = explanation


@dataclass(frozen=True)
class TriggerDates:
    """The dates a deadline can be counted from.

    ``denial_date`` is what the letter is dated. ``denial_received_date`` is when
    the member says it reached them, which is the trigger the federal rule
    actually names -- and the one we usually do not know.
    """

    denial_date: date
    denial_received_date: date | None = None
    service_date: date | None = None
    final_adverse_date: date | None = None


@dataclass(frozen=True)
class ResolvedDeadline:
    """A due date plus everything needed to show the user how it was reached."""

    due_date: date
    trigger_date: date
    trigger_description: str
    ambiguous: bool
    ambiguity_note: str | None


#: The note shown whenever a deadline is counted from the letter's date because
#: the receipt date is unknown. The regulation counts from receipt, so counting
#: from the earlier date is the conservative reading -- and the user is told,
#: because a conservative date presented as certain is still a misrepresentation.
RECEIPT_AMBIGUITY_NOTE = (
    "The rule counts this from the day you received the letter, and we do not know "
    "that date. We counted from the date printed on the letter instead, which gives "
    "you the earlier of the two deadlines. If you know when it actually arrived, add "
    "it and we will recalculate. Either way, check the date against your own letter "
    "before you rely on it."
)


def resolve_trigger(trigger: str, dates: TriggerDates) -> tuple[date, str, bool, str | None]:
    """Pick the date a deadline counts from.

    Returns ``(trigger_date, description, ambiguous, note)``.

    The one genuinely ambiguous case is ``denial_received_date``. When the member
    has told us when the letter arrived we use that, because it is what the rule
    says. When they have not, we fall back to the letter's own date -- earlier,
    therefore safer -- and flag it.
    """
    if trigger == "denial_date":
        return dates.denial_date, "the date printed on your denial letter", False, None

    if trigger == "denial_received_date":
        if dates.denial_received_date is not None:
            return (
                dates.denial_received_date,
                "the day you told us the letter reached you",
                False,
                None,
            )
        return (
            dates.denial_date,
            "the date printed on your denial letter",
            True,
            RECEIPT_AMBIGUITY_NOTE,
        )

    if trigger == "service_date":
        if dates.service_date is None:
            raise TriggerUnavailable(
                trigger,
                "This deadline counts from the date of service, which we do not have yet.",
            )
        return dates.service_date, "the date of service", False, None

    if trigger == "final_adverse_date":
        if dates.final_adverse_date is not None:
            return (
                dates.final_adverse_date,
                "the date of the insurer's final decision on your internal appeal",
                False,
                None,
            )
        # On a first appeal this has not happened yet, so there is no date to
        # give. The step is shown undated rather than dated from something else.
        raise TriggerUnavailable(
            trigger,
            "This step starts when the insurer gives its final answer on your internal "
            "appeal. That has not happened yet, so there is no deadline to show you. "
            "We will work it out the moment you have their answer.",
        )

    raise ValueError(f"unknown deadline trigger {trigger!r}")


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------


def add_calendar_days(start: date, count: int) -> date:
    """``count`` calendar days after ``start``, with ``start`` as day zero.

    Day one is the day after the trigger. 14 Sep 2026 + 180 calendar days is
    13 Mar 2027.
    """
    if count < 0:
        raise ValueError("count must not be negative")
    return start + timedelta(days=count)


def add_months(start: date, count: int) -> date:
    """``count`` calendar months after ``start``.

    Month arithmetic clamps to the end of a short month: 31 Jan plus one month is
    28 Feb, not 3 March. That is the conservative direction, and it is what
    "four months" means to a court.
    """
    if count < 0:
        raise ValueError("count must not be negative")
    shifted: date = start + relativedelta(months=count)
    return shifted


def add_hours_as_date(start: date, count: int) -> date:
    """The calendar date an hours-based window lands on.

    An hours window is really a timestamp deadline and we do not know the hour
    the clock started, so we report the date it falls on and let the UI say
    "within 72 hours". 72 hours from a Monday is the following Thursday.

    Rounding is **down** -- 72 hours is 3 days, not 4 -- because rounding up
    would hand the user time the rule did not give.
    """
    if count < 0:
        raise ValueError("count must not be negative")
    return start + timedelta(days=count // 24)


def resolve_deadline(
    *,
    count: int,
    unit: DayUnit | str,
    trigger: str,
    dates: TriggerDates,
) -> ResolvedDeadline:
    """Turn a rulebase row into a dated deadline with its explanation."""
    unit = DayUnit(unit)
    trigger_date, trigger_phrase, ambiguous, note = resolve_trigger(trigger, dates)

    if unit is DayUnit.CALENDAR:
        due = add_calendar_days(trigger_date, count)
        description = f"{count} calendar days from {trigger_phrase}"
    elif unit is DayUnit.BUSINESS:
        due = add_business_days(trigger_date, count)
        description = f"{count} business days from {trigger_phrase}"
    elif unit is DayUnit.MONTHS:
        due = add_months(trigger_date, count)
        description = f"{count} months from {trigger_phrase}"
    elif unit is DayUnit.HOURS:
        due = add_hours_as_date(trigger_date, count)
        description = f"{count} hours from {trigger_phrase}"
    else:  # pragma: no cover -- DayUnit is exhaustive
        raise ValueError(f"unhandled unit {unit!r}")

    return ResolvedDeadline(
        due_date=due,
        trigger_date=trigger_date,
        trigger_description=description,
        ambiguous=ambiguous,
        ambiguity_note=note,
    )


def days_until(due: date, today: date) -> int:
    """Whole days from ``today`` to ``due``. Negative once the window has closed."""
    return (due - today).days
