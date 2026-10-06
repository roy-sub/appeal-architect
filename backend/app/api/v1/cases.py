"""Case CRUD, the timeline, and escalation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.db import repo
from app.deps import CurrentUserDep
from app.domain.case import CaseStage, PlanType, ServiceTiming
from app.problem import ErrorCode, Problem

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseSummary(BaseModel):
    """One row in the case list.

    ``next_deadline`` is computed server-side and sent as a date. The frontend
    does no date arithmetic beyond "days until" -- spec 11.
    """

    id: UUID
    title: str
    insurer_name: str | None = None
    claim_number: str | None = None
    stage: CaseStage
    plan_type: PlanType = PlanType.UNKNOWN
    state: str | None = None
    denial_date: date | None = None
    denial_received_date: date | None = None
    service_date: date | None = None
    service_timing: ServiceTiming | None = None
    claim_amount_usd: Decimal | None = None
    is_urgent_medical: bool = False
    filer: Literal["member", "authorized_rep", "provider"] = "member"
    final_adverse_date: date | None = None
    next_deadline: date | None = None
    next_deadline_label: str | None = None
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    insurer_name: str | None = Field(default=None, max_length=200)


class CasePatch(BaseModel):
    """Everything the user can set directly.

    Dates and the plan type live here as well as in extracted facts, because a
    user who knows the answer should be able to type it rather than wait for a
    document to be read.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    insurer_name: str | None = Field(default=None, max_length=200)
    claim_number: str | None = Field(default=None, max_length=100)
    plan_type: PlanType | None = None
    state: str | None = Field(default=None, min_length=2, max_length=2)
    denial_date: date | None = None
    denial_received_date: date | None = None
    service_date: date | None = None
    service_timing: ServiceTiming | None = None
    claim_amount_usd: Decimal | None = None
    is_urgent_medical: bool | None = None
    filer: Literal["member", "authorized_rep", "provider"] | None = None


def _summary(row: dict[str, Any]) -> CaseSummary:
    return CaseSummary.model_validate(row)


def _with_next_deadline(row: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Attach the soonest unacknowledged deadline, so the list can lead with it."""
    deadlines = repo.list_for_case("deadlines", str(row["id"]), user_id, order="due_date")
    soonest = next((d for d in deadlines if not d.get("acknowledged_at")), None)
    if soonest:
        row = {**row, "next_deadline": soonest["due_date"], "next_deadline_label": soonest["label"]}
    return row


@router.get("", response_model=list[CaseSummary])
async def list_cases(user: CurrentUserDep) -> list[CaseSummary]:
    """This user's cases, soonest deadline first.

    Sorted by how soon each case needs the user, not by when it was added: the
    caregiver managing three of these on a phone needs the urgent one at the top.
    """
    from app.db.client import get_client

    result = get_client().table("cases").select("*").eq("user_id", user.id).execute()
    enriched = [_with_next_deadline(row, user.id) for row in repo.narrow_rows(result.data)]
    enriched.sort(
        key=lambda row: (
            row.get("next_deadline") is None,
            str(row.get("next_deadline") or "9999-12-31"),
            str(row.get("created_at") or ""),
        )
    )
    return [_summary(row) for row in enriched]


@router.post("", response_model=CaseSummary, status_code=status.HTTP_201_CREATED)
async def create_case(payload: CaseCreate, user: CurrentUserDep) -> CaseSummary:
    """Open a case. ``user_id`` comes from the verified token, never the body."""
    from app.db.client import get_client

    result = (
        get_client()
        .table("cases")
        .insert(
            {
                "user_id": user.id,
                "title": payload.title,
                "insurer_name": payload.insurer_name,
                "stage": CaseStage.UPLOADED.value,
            }
        )
        .execute()
    )
    rows = repo.narrow_rows(result.data)
    if not rows:  # pragma: no cover
        raise Problem(500, ErrorCode.INTERNAL_ERROR, "The case could not be created.")
    repo.log_event(str(rows[0]["id"]), "case_opened", {"title": payload.title})
    return _summary(rows[0])


@router.get("/{case_id}", response_model=CaseSummary)
async def get_case(case_id: str, user: CurrentUserDep) -> CaseSummary:
    row = repo.get_case(case_id, user.id)
    return _summary(_with_next_deadline(row, user.id))


@router.patch("/{case_id}", response_model=CaseSummary)
async def patch_case(case_id: str, payload: CasePatch, user: CurrentUserDep) -> CaseSummary:
    patch = payload.model_dump(exclude_none=True, mode="json")
    if not patch:
        return _summary(repo.get_case(case_id, user.id))
    if "state" in patch:
        patch["state"] = str(patch["state"]).upper()
    row = repo.update_case(case_id, user.id, patch)
    repo.log_event(case_id, "case_updated", {"fields": sorted(patch)})
    return _summary(_with_next_deadline(row, user.id))


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: str, user: CurrentUserDep) -> None:
    """Delete a case and everything hanging off it, including its files."""
    from app.services import storage

    repo.get_case(case_id, user.id)
    storage.remove_case_objects("documents", case_id)
    storage.remove_case_objects("letters", case_id)
    repo.delete_case(case_id, user.id)


class TimelineEvent(BaseModel):
    id: UUID
    kind: str
    detail: dict[str, Any] = {}
    created_at: datetime


@router.get("/{case_id}/timeline", response_model=list[TimelineEvent])
async def get_timeline(case_id: str, user: CurrentUserDep) -> list[TimelineEvent]:
    """Everything that happened, newest first.

    This is the record the user may need later: what was uploaded, confirmed,
    generated and sent, and when.
    """
    rows = repo.list_for_case("case_events", case_id, user.id, order="created_at", desc=True)
    return [TimelineEvent.model_validate(row) for row in rows]


class EscalateRequest(BaseModel):
    final_adverse_date: date = Field(
        description="The date of the insurer's final answer on the internal appeal"
    )


@router.post("/{case_id}/escalate", response_model=CaseSummary)
async def escalate_case(
    case_id: str, payload: EscalateRequest, user: CurrentUserDep
) -> CaseSummary:
    """Record the insurer's final internal denial and move to external review.

    This is what gives the external-review step a real date: until the final
    answer exists there is nothing to count from, and the engine refuses to
    invent a trigger.
    """
    case = repo.get_case(case_id, user.id)
    if payload.final_adverse_date < date.fromisoformat(
        str(case.get("denial_date") or "1900-01-01")
    ):
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            "The final decision cannot be dated before the original denial. Check the "
            "date on the letter.",
        )

    repo.update_case(
        case_id,
        user.id,
        {
            "final_adverse_date": payload.final_adverse_date.isoformat(),
            "stage": CaseStage.ESCALATED.value,
        },
    )
    repo.log_event(
        case_id, "escalated", {"final_adverse_date": payload.final_adverse_date.isoformat()}
    )

    # Recompute, so the external-review deadline appears with a real date.
    from app.services import route as route_service

    route_service.compute_route(case_id, user.id)
    return _summary(_with_next_deadline(repo.get_case(case_id, user.id), user.id))
