"""Deadline reminders. One scheduled job, no worker process.

A single idempotent endpoint finds deadlines at 30 / 14 / 7 / 3 / 1 days out
with no reminder already logged, sends the email, and logs it. Called once daily
by ``pg_cron`` or a Render Cron Job. No Celery, no Redis, nothing always-on.

Idempotency is enforced by the database: ``reminders_sent`` is unique on
``(deadline_id, days_before)``. That matters because a cron that double-fires
must not email someone twice about the same deadline — and because running the
job by hand to check it works has to be safe.

The email names the deadline and the case title. It does **not** carry the
denial reason, the treatment, or any clinical detail: a reminder lands in an
inbox that may be read on a shared screen.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from app.config import get_settings
from app.db.client import get_client
from app.db.repo import narrow_rows

logger = logging.getLogger("appeal_architect.reminders")

#: Days before a deadline that we write. Chosen so the last one still leaves
#: time to act, and the first one arrives while gathering evidence is realistic.
REMINDER_DAYS = (30, 14, 7, 3, 1)


@dataclass
class ReminderRun:
    """What one run did. Returned by the endpoint so a cron log is meaningful."""

    checked: int = 0
    sent: int = 0
    skipped_already_sent: int = 0
    failed: int = 0
    details: list[dict[str, Any]] = field(default_factory=list)


def _due_window(today: date) -> dict[str, int]:
    """Map each reminder date to its days-before value."""
    from datetime import timedelta

    return {(today + timedelta(days=n)).isoformat(): n for n in REMINDER_DAYS}


def run_reminders(*, today: date | None = None, dry_run: bool = False) -> ReminderRun:
    """Find the deadlines due a reminder today and write to their owners."""
    today = today or datetime.now(tz=UTC).date()
    window = _due_window(today)
    run = ReminderRun()

    client = get_client()
    result = (
        client.table("deadlines")
        .select("*")
        .in_("due_date", list(window))
        .is_("acknowledged_at", "null")
        .execute()
    )
    deadlines = narrow_rows(result.data)
    run.checked = len(deadlines)

    for deadline in deadlines:
        days_before = window[str(deadline["due_date"])]

        already = (
            client.table("reminders_sent")
            .select("id")
            .eq("deadline_id", deadline["id"])
            .eq("days_before", days_before)
            .limit(1)
            .execute()
        )
        if narrow_rows(already.data):
            run.skipped_already_sent += 1
            continue

        case = narrow_rows(
            client.table("cases")
            .select("id,title,user_id,insurer_name")
            .eq("id", deadline["case_id"])
            .limit(1)
            .execute()
            .data
        )
        if not case:  # pragma: no cover -- cascade should prevent this
            continue
        owner = case[0]

        email = _recipient(owner["user_id"])
        if not email:
            logger.warning("no email address for a case owner; skipping reminder")
            run.failed += 1
            continue

        if dry_run:
            run.details.append(
                {"deadline_id": deadline["id"], "days_before": days_before, "dry_run": True}
            )
            continue

        try:
            send_reminder_email(
                to=email,
                case_title=str(owner["title"]),
                deadline_label=str(deadline["label"]),
                due_date=date.fromisoformat(str(deadline["due_date"])),
                days_before=days_before,
                ambiguous=bool(deadline.get("ambiguous")),
            )
        except Exception:
            logger.warning("could not send a reminder", exc_info=False)
            run.failed += 1
            continue

        # Logged only after a successful send, so a failure is retried tomorrow
        # rather than silently swallowed.
        client.table("reminders_sent").insert(
            {"deadline_id": deadline["id"], "days_before": days_before}
        ).execute()
        run.sent += 1
        run.details.append({"deadline_id": deadline["id"], "days_before": days_before})

    logger.info(
        "reminder run: checked=%d sent=%d already=%d failed=%d",
        run.checked,
        run.sent,
        run.skipped_already_sent,
        run.failed,
    )
    return run


def _recipient(user_id: str) -> str | None:
    """The owner's email, from Supabase Auth."""
    try:
        response = get_client().auth.admin.get_user_by_id(user_id)
        return getattr(response.user, "email", None)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

#: How each reminder opens. Calm, specific, never alarming -- and never a
#: countdown in a subject line, because a number shrinking in someone's inbox
#: while they are unwell is cruel.
TONE: dict[int, str] = {
    30: "You have a month",
    14: "Two weeks left",
    7: "A week left",
    3: "Three days left",
    1: "Due tomorrow",
}


def reminder_subject(case_title: str, days_before: int) -> str:
    return f"{TONE.get(days_before, 'Deadline coming up')} — {case_title}"


def reminder_body(
    *,
    case_title: str,
    deadline_label: str,
    due_date: date,
    days_before: int,
    ambiguous: bool,
) -> tuple[str, str]:
    """Returns (plain text, html).

    Deliberately contains no clinical detail. This may be read on a shared
    screen, and the user did not consent to their diagnosis arriving by email.
    """
    from app.site import DISCLAIMER

    note = ""
    if ambiguous:
        note = (
            "\n\nThis date is our more cautious reading of the rule. Your plan may "
            "allow a little longer, but we would rather you were early than late."
        )

    plain = f"""{TONE.get(days_before, "Deadline coming up")}.

{deadline_label} for "{case_title}" is due on {due_date:%-d %B %Y}.

That is {days_before} {"day" if days_before == 1 else "days"} from today.{note}

Open your case to see what this step needs and the rule the date comes from.

—

{DISCLAIMER}
"""

    note_block = (
        f'<p style="font-size:15px;line-height:24px;color:#5E5850;'
        f'margin:0 0 14px">{note.strip()}</p>'
        if note
        else ""
    )

    html = f"""<!doctype html>
<html><body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;
  color:#1C1A17;background:#F2EDE4;margin:0;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#FFFCF7;
    border:1px solid #DED5C6;padding:28px">
    <div style="font-family:ui-monospace,monospace;font-size:11px;
      letter-spacing:.06em;color:#5E5850">APPEAL ARCHITECT</div>
    <h1 style="font-size:22px;line-height:30px;margin:14px 0 8px;font-weight:600">
      {TONE.get(days_before, "Deadline coming up")}</h1>
    <p style="font-size:16px;line-height:26px;margin:0 0 14px">
      <strong>{deadline_label}</strong> for &ldquo;{case_title}&rdquo; is due on
      <strong>{due_date:%-d %B %Y}</strong> &mdash; {days_before}
      {"day" if days_before == 1 else "days"} from today.</p>
    {note_block}
    <p style="font-size:16px;line-height:26px;margin:0 0 20px">
      Open your case to see what this step needs and the rule the date comes from.</p>
    <p style="font-size:13px;line-height:21px;color:#1C1A17;border-top:1px solid #DED5C6;
      padding-top:14px;margin:0">{DISCLAIMER}</p>
  </div>
</body></html>
"""
    return plain, html


def send_reminder_email(
    *,
    to: str,
    case_title: str,
    deadline_label: str,
    due_date: date,
    days_before: int,
    ambiguous: bool,
) -> None:
    settings = get_settings()
    if not settings.email_configured:
        logger.warning("email is not configured; reminder not sent")
        raise RuntimeError("email not configured")

    plain, html = reminder_body(
        case_title=case_title,
        deadline_label=deadline_label,
        due_date=due_date,
        days_before=days_before,
        ambiguous=ambiguous,
    )

    import httpx

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={
            "from": settings.from_email,
            "to": [to],
            "subject": reminder_subject(case_title, days_before),
            "text": plain,
            "html": html,
        },
        timeout=20,
    )
    response.raise_for_status()
