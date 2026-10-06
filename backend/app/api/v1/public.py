"""The free triage tool. No account, rate-limited.

Four questions, an honest verdict, and the rule behind the deadline. This is
the funnel and the goodwill, so it has to be genuinely useful and genuinely
honest — including when the honest answer is "we cannot tell you yet".

It calls the same rules engine as the authenticated route. There is no second,
looser code path for the free tool: a deadline shown to someone who has not
signed up is as consequential as one shown to someone who has.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.config import get_settings
from app.domain.case import CaseFacts, DenialReason, PlanType, ServiceTiming
from app.problem import ErrorCode, Problem
from app.rules.runner import determine_route

logger = logging.getLogger("appeal_architect.public")

router = APIRouter(prefix="/public", tags=["public"])

#: Rate limit for the unauthenticated tool. Generous enough that a household
#: behind one address is never blocked, tight enough that the endpoint is not a
#: free rules API.
RATE_LIMIT_PER_HOUR = 20
RATE_WINDOW = timedelta(hours=1)

#: Published appeal and overturn statistics are deliberately NOT asserted here.
#: The honest answer about whether an appeal is worth making is a general one.
WORTH_IT = (
    "Most people never appeal, and a large share of those who do get the decision "
    "changed. That is a fact about appeals in general. It is not a prediction about "
    "your case, and nobody can give you one."
)


class TriageRequest(BaseModel):
    plan_type: PlanType = Field(description="Where the insurance comes from")
    state: str = Field(min_length=2, max_length=2)
    denial_date: date | None = Field(default=None, description="The date printed on the letter")
    service_timing: ServiceTiming = ServiceTiming.POST_SERVICE
    denial_reason: DenialReason = DenialReason.OTHER
    is_urgent_medical: bool = False


class TriageDeadline(BaseModel):
    label: str
    due_date: date
    days_remaining: int
    trigger_description: str
    rule_id: str
    citation: str
    ambiguous: bool
    ambiguity_note: str | None = None


class TriageResponse(BaseModel):
    """What the free check produces.

    ``track`` is None when we cannot work it out. That is a real outcome and the
    tool says so plainly rather than guessing, because a guessed track sends
    someone to the wrong reviewer with the wrong form.
    """

    track: str | None
    levels: list[str]
    deadline: TriageDeadline | None
    worth_appealing: str
    warnings: list[str]
    rulebase_version: str
    counted_from_today: date


def _client_fingerprint(request: Request) -> str:
    """A salted hash of the caller's address. The raw IP is never stored."""
    forwarded = request.headers.get("x-forwarded-for", "")
    address = forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    salt = get_settings().internal_job_secret or "appeal-architect-triage"
    return hashlib.sha256(f"{salt}:{address}".encode()).hexdigest()


def _enforce_rate_limit(request: Request) -> None:
    """A Postgres counter rather than Redis.

    The free tier has no Redis, and an in-process bucket resets every time
    Render puts the service to sleep -- which is most of the time. A table
    survives restarts and costs nothing.
    """
    settings = get_settings()
    if not settings.supabase_configured:
        return

    from app.db.client import get_client
    from app.db.repo import narrow_rows

    fingerprint = _client_fingerprint(request)
    since = (datetime.now(tz=UTC) - RATE_WINDOW).isoformat()
    client = get_client()

    recent = narrow_rows(
        client.table("public_triage_hits")
        .select("id")
        .eq("ip_hash", fingerprint)
        .gte("created_at", since)
        .execute()
        .data
    )
    if len(recent) >= RATE_LIMIT_PER_HOUR:
        raise Problem(
            429,
            ErrorCode.RATE_LIMITED,
            "That is a lot of checks from one connection in an hour. Wait a little and "
            "try again, or open an account to keep your case.",
        )

    client.table("public_triage_hits").insert({"ip_hash": fingerprint}).execute()
    # Opportunistic sweep, so the table does not grow without bound and no
    # separate cleanup job is needed.
    client.table("public_triage_hits").delete().lt(
        "created_at", (datetime.now(tz=UTC) - timedelta(days=2)).isoformat()
    ).execute()


TRACK_NAMES: dict[PlanType, str] = {
    PlanType.ACA_MARKETPLACE: (
        "Marketplace plan — internal appeal, then independent external review"
    ),
    PlanType.EMPLOYER_FULLY_INSURED: (
        "Employer plan — internal appeal, then independent external review"
    ),
}


@router.post("/triage", response_model=TriageResponse)
async def triage(payload: TriageRequest, request: Request) -> TriageResponse:
    """The free check. Same engine as the paid route, no account needed."""
    _enforce_rate_limit(request)

    today = datetime.now(tz=UTC).date()
    denial_date = payload.denial_date or today

    facts = CaseFacts(
        plan_type=payload.plan_type,
        state=payload.state,
        insurer_name="your insurer",
        member_id_present=True,
        denial_date=denial_date,
        service_timing=payload.service_timing,
        denial_reasons=[payload.denial_reason],
        is_urgent_medical=payload.is_urgent_medical,
        filer="member",
    )
    route = determine_route(facts)

    deadline = None
    internal = next((d for d in route.deadlines if d.id == "internal_appeal"), None)
    if internal is not None and payload.denial_date is not None:
        deadline = TriageDeadline(
            label=internal.label,
            due_date=internal.due_date,
            days_remaining=(internal.due_date - today).days,
            trigger_description=internal.trigger_description,
            rule_id=internal.rule_id,
            citation=internal.citation.label(),
            ambiguous=internal.ambiguous,
            ambiguity_note=internal.ambiguity_note,
        )

    warnings = list(route.warnings)
    if payload.denial_date is None:
        warnings.append(
            "We cannot give you a date without the date on your letter. Everything "
            "else here still applies."
        )

    return TriageResponse(
        track=TRACK_NAMES.get(payload.plan_type),
        levels=[step.label for step in route.steps],
        deadline=deadline,
        worth_appealing=WORTH_IT,
        warnings=warnings,
        rulebase_version=route.rulebase_version,
        counted_from_today=today,
    )


class TriageOptions(BaseModel):
    """Drives the question screens, so the options cannot drift from the enums."""

    plan_types: list[dict[str, str]]
    service_timings: list[dict[str, str]]
    denial_reasons: list[dict[str, str]]


PLAN_TYPE_LABELS: dict[PlanType, str] = {
    PlanType.ACA_MARKETPLACE: "I bought it myself on the marketplace",
    PlanType.EMPLOYER_FULLY_INSURED: "Through my job or a family member's job",
    PlanType.EMPLOYER_SELF_FUNDED: "Through my job, and the employer pays claims itself",
    PlanType.MEDICARE_ADVANTAGE: "Medicare Advantage",
    PlanType.MEDICAID: "Medicaid",
    PlanType.UNKNOWN: "I am not sure",
}

TIMING_LABELS: dict[ServiceTiming, str] = {
    ServiceTiming.PRE_SERVICE: "It has not happened yet",
    ServiceTiming.POST_SERVICE: "It already happened",
    ServiceTiming.CONCURRENT: "I am in the middle of it",
}

REASON_LABELS: dict[DenialReason, str] = {
    DenialReason.NOT_MEDICALLY_NECESSARY: "Not medically necessary",
    DenialReason.PRIOR_AUTH_MISSING: "Prior authorisation was missing",
    DenialReason.OUT_OF_NETWORK: "The provider was out of network",
    DenialReason.EXPERIMENTAL: "Experimental or investigational",
    DenialReason.CODING_ERROR: "A coding or billing problem",
    DenialReason.NOT_COVERED_BENEFIT: "Not a covered benefit",
    DenialReason.OTHER: "Something else, or it is not clear",
}


@router.get("/triage/options", response_model=TriageOptions)
async def triage_options() -> TriageOptions:
    return TriageOptions(
        plan_types=[{"value": k.value, "label": v} for k, v in PLAN_TYPE_LABELS.items()],
        service_timings=[{"value": k.value, "label": v} for k, v in TIMING_LABELS.items()],
        denial_reasons=[{"value": k.value, "label": v} for k, v in REASON_LABELS.items()],
    )
