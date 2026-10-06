"""Call the reminder endpoint. Run daily by a cron job.

    python -m app.jobs.send_reminders

A thin client rather than a second implementation: the endpoint holds the logic
and the idempotency, so running this twice is harmless and running it by hand to
check the wiring cannot double-email anyone.

Exits non-zero on failure so the cron runner reports it. A reminder job that
fails quietly is the same as no reminder job.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    import httpx

    base = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
    secret = os.environ.get("INTERNAL_JOB_SECRET", "")
    if not secret:
        print("INTERNAL_JOB_SECRET is not set; refusing to run", file=sys.stderr)
        return 2

    try:
        # Render's free web service sleeps after 15 minutes idle, and the first
        # request wakes it. The generous timeout is for that cold start, not for
        # the work itself.
        response = httpx.post(
            f"{base}/api/v1/internal/run-reminders",
            headers={"X-Internal-Job-Secret": secret},
            timeout=120,
        )
    except httpx.HTTPError as error:
        print(f"could not reach the API: {error}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        print(f"reminder run failed: HTTP {response.status_code}", file=sys.stderr)
        return 1

    result = response.json()
    print(
        "reminders: checked={checked} sent={sent} already={skipped_already_sent} "
        "failed={failed}".format(**result)
    )
    return 1 if result.get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
