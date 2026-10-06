"""The scheduled reminder job.

Protected by a shared secret, idempotent, and called once daily by `pg_cron` or
a Render Cron Job. There is no worker process and nothing always-on.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import require_job_secret
from app.services import reminders

router = APIRouter(prefix="/internal", tags=["internal"])


class ReminderRunResult(BaseModel):
    checked: int
    sent: int
    skipped_already_sent: int
    failed: int
    details: list[dict[str, Any]] = []


@router.post(
    "/run-reminders",
    response_model=ReminderRunResult,
    dependencies=[Depends(require_job_secret)],
)
async def run_reminders(
    today: Annotated[date | None, None] = None, dry_run: bool = False
) -> ReminderRunResult:
    """Send the reminders due today.

    Safe to run twice: ``reminders_sent`` is unique on
    ``(deadline_id, days_before)``, so a second run reports everything as
    already sent and writes nothing. That is also how you check the cron is
    wired without emailing anyone twice.
    """
    run = reminders.run_reminders(today=today, dry_run=dry_run)
    return ReminderRunResult(
        checked=run.checked,
        sent=run.sent,
        skipped_already_sent=run.skipped_already_sent,
        failed=run.failed,
        details=run.details,
    )
