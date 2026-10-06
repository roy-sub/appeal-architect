"""Case list and creation.

Phase 1 covers only what the empty case list needs. Upload, extraction, route
and arguments arrive in phase 4.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.deps import CurrentUserDep
from app.domain.case import CaseStage, PlanType

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
    denial_date: datetime | None = None
    next_deadline: datetime | None = None
    next_deadline_label: str | None = None
    created_at: datetime
    updated_at: datetime


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    insurer_name: str | None = Field(default=None, max_length=200)


@router.get("", response_model=list[CaseSummary])
async def list_cases(user: CurrentUserDep) -> list[CaseSummary]:
    """This user's cases, soonest deadline first.

    Sorted by how soon each case needs the user, not by when it was added: the
    caregiver managing three of these on a phone needs the urgent one at the top.
    """
    from app.services.case import list_cases_for_user

    return await list_cases_for_user(user.id)


@router.post("", response_model=CaseSummary, status_code=status.HTTP_201_CREATED)
async def create_case(payload: CaseCreate, user: CurrentUserDep) -> CaseSummary:
    """Open a case. ``user_id`` comes from the verified token, never the body."""
    from app.services.case import create_case_for_user

    return await create_case_for_user(
        user.id, title=payload.title, insurer_name=payload.insurer_name
    )
