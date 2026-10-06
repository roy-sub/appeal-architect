"""Deadline reminders: the schedule, the copy, and the PHI discipline.

The reminder email is a core feature and also the part most likely to leak:
it lands in an inbox that may be read on a shared screen. So the copy is tested
for what it must NOT contain as much as for what it must.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services.reminders import (
    REMINDER_DAYS,
    TONE,
    _due_window,
    reminder_body,
    reminder_subject,
)


def test_the_schedule_is_the_specified_one() -> None:
    assert REMINDER_DAYS == (30, 14, 7, 3, 1)


def test_every_reminder_day_has_its_own_opening() -> None:
    """A missing entry would send "Deadline coming up" for a one-day warning."""
    for days in REMINDER_DAYS:
        assert days in TONE, f"no opening line for the {days}-day reminder"


def test_the_due_window_maps_dates_back_to_days_before() -> None:
    today = date(2026, 10, 6)
    window = _due_window(today)
    assert len(window) == len(REMINDER_DAYS)
    for days in REMINDER_DAYS:
        assert window[(today + timedelta(days=days)).isoformat()] == days


def test_the_window_does_not_include_today_or_the_past() -> None:
    """A reminder about a deadline that has passed is cruel and useless."""
    today = date(2026, 10, 6)
    window = _due_window(today)
    assert today.isoformat() not in window
    assert (today - timedelta(days=1)).isoformat() not in window


# ---- the copy --------------------------------------------------------------


def _body(**overrides):
    base = {
        "case_title": "Anthem — infusion denial",
        "deadline_label": "File your internal appeal",
        "due_date": date(2027, 3, 13),
        "days_before": 14,
        "ambiguous": False,
    }
    return reminder_body(**{**base, **overrides})


def test_the_email_names_the_deadline_and_the_date() -> None:
    plain, html = _body()
    for text in (plain, html):
        assert "File your internal appeal" in text
        assert "13 March 2027" in text
        assert "14" in text


def test_an_ambiguous_deadline_says_so_in_the_email() -> None:
    plain, html = _body(ambiguous=True)
    assert "more cautious reading" in plain
    assert "early than late" in plain
    assert "more cautious reading" in html


def test_a_certain_deadline_carries_no_caveat() -> None:
    plain, _ = _body(ambiguous=False)
    assert "more cautious reading" not in plain


def test_the_email_carries_the_disclaimer() -> None:
    from app.site import DISCLAIMER

    plain, html = _body()
    assert DISCLAIMER in plain
    assert "prepares documents and explains procedure" in html


def test_the_email_contains_no_clinical_detail() -> None:
    """The PHI rule for reminders. This may be read on a shared screen, and the
    user did not consent to their diagnosis arriving by email."""
    plain, html = _body(case_title="Case 1")
    for text in (plain, _visible(html)):
        lowered = text.lower()
        for leak in (
            "diagnosis",
            "medically necessary",
            "infusion",
            "prescription",
            "treatment for",
            "condition",
        ):
            assert leak not in lowered, f"the reminder email mentions {leak!r}"


def test_the_subject_does_not_count_down_in_the_inbox() -> None:
    """Never animate a countdown, and never put one in a subject line: a number
    shrinking in someone's peripheral vision while they are unwell is cruel."""
    for days in REMINDER_DAYS:
        subject = reminder_subject("A case", days)
        assert subject.startswith(TONE[days])
        assert "!" not in subject


def test_the_one_day_reminder_reads_as_tomorrow_not_a_number() -> None:
    assert TONE[1] == "Due tomorrow"


@pytest.mark.parametrize("days", REMINDER_DAYS)
def test_day_pluralisation_is_right(days: int) -> None:
    plain, _ = _body(days_before=days)
    if days == 1:
        assert "1 day from today" in plain
    else:
        assert f"{days} days from today" in plain


def _visible(html: str) -> str:
    """The text a reader sees, with tags and the doctype stripped.

    A copy rule is about what reaches the reader, so markup is not in scope --
    `<!doctype html>` contains an exclamation mark and says nothing to anyone.
    """
    import re

    without_tags = re.sub(r"<[^>]*>", " ", html)
    return re.sub(r"\s+", " ", without_tags).strip()


def test_no_exclamation_marks_in_anything_the_reader_sees() -> None:
    """House voice: the product never gushes, least of all at someone unwell."""
    plain, html = _body()
    assert "!" not in plain
    assert "!" not in _visible(html)


def test_the_idempotency_contract_is_documented_in_the_schema() -> None:
    """The unique constraint is what makes a double-firing cron harmless.

    Asserted against the migration so removing it cannot pass unnoticed.
    """
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parent.parent / "app" / "db" / "migrations" / "001_init.sql"
    ).read_text(encoding="utf-8")
    assert "unique (deadline_id, days_before)" in migration
