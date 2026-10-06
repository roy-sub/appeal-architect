"""Appeal-track rules used by the free triage check.

Each track carries the internal-appeal window and the regulation that sets it,
so every determination can show the rule it came from.
"""
from datetime import date, timedelta

RULES_VERSION = "2026.10.1"
RULES_AS_OF = date(2026, 10, 5)

TRACKS = {
    "employer": {
        "name": "Employer plan — internal appeal, then independent external review",
        "window_days": 180,
        "rule": "29 C.F.R. § 2560.503-1(h)(3)(i)",
    },
    "marketplace": {
        "name": "Individual marketplace plan — internal appeal, then external review",
        "window_days": 180,
        "rule": "45 C.F.R. § 147.136(b)(2)",
    },
    "medicare": {
        "name": "Medicare — redetermination, then reconsideration",
        "window_days": 65,
        "rule": "42 C.F.R. § 422.582(b)",
    },
    "medicaid": {
        "name": "Medicaid managed care — plan appeal, then state fair hearing",
        "window_days": 60,
        "rule": "42 C.F.R. § 438.402(c)(2)(ii)",
    },
}


def determine(source: str, letter_date: date | None, today: date) -> dict:
    """Return the likely track and deadline. Never guesses when the plan type is unknown."""
    track = TRACKS.get(source)
    if track is None:
        return {"track": None, "deadline": None, "days_remaining": None,
                "note": "We cannot route this without knowing where the insurance comes from."}
    deadline = days_left = None
    if letter_date is not None:
        deadline = letter_date + timedelta(days=track["window_days"])
        days_left = (deadline - today).days
    return {
        "track": track["name"],
        "rule": track["rule"],
        "window_days": track["window_days"],
        "deadline": deadline,
        "days_remaining": days_left,
        "stamp": f"Rules current as of {RULES_AS_OF:%-d %b %Y} · version {RULES_VERSION}",
    }
