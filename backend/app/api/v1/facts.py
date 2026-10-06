"""Proposed facts, and the confirm / edit / reject actions on them.

This is the trust model's hinge. Every proposal is shown with the source text it
came from, and nothing reaches the rules engine until a person has said yes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import CurrentUserDep
from app.domain.case import FactStatus
from app.services import facts as facts_service

router = APIRouter(prefix="/cases/{case_id}/facts", tags=["facts"])


class FactOut(BaseModel):
    id: UUID
    document_id: UUID | None
    field: str
    value: Any
    edited_value: Any = None
    confidence: float
    source_page: int | None = None
    source_start: int | None = None
    source_end: int | None = None
    status: FactStatus
    confirmed_at: datetime | None = None


class FactsResponse(BaseModel):
    facts: list[FactOut]
    #: Required fields still neither confirmed nor set. While this is non-empty,
    #: POST /route is a 409 — the roadmap stays gated, as the brief requires.
    pending_required: list[str]
    ready_for_route: bool


class EditRequest(BaseModel):
    value: Any


@router.get("", response_model=FactsResponse)
async def list_facts(case_id: str, user: CurrentUserDep) -> FactsResponse:
    rows = facts_service.list_facts(case_id, user.id)
    pending = facts_service.pending_required_fields(case_id, user.id)
    return FactsResponse(
        facts=[FactOut.model_validate(row) for row in rows],
        pending_required=pending,
        ready_for_route=not pending,
    )


@router.post("/{fact_id}/confirm", response_model=FactOut)
async def confirm_fact(case_id: str, fact_id: str, user: CurrentUserDep) -> FactOut:
    return FactOut.model_validate(facts_service.confirm(case_id, fact_id, user.id))


@router.post("/{fact_id}/edit", response_model=FactOut)
async def edit_fact(
    case_id: str, fact_id: str, payload: EditRequest, user: CurrentUserDep
) -> FactOut:
    """Correct a proposal.

    Extraction gets things wrong, and that has to feel normal rather than like a
    failure — so this is an ordinary action, not an error path.
    """
    return FactOut.model_validate(facts_service.edit(case_id, fact_id, user.id, payload.value))


@router.post("/{fact_id}/reject", response_model=FactOut)
async def reject_fact(case_id: str, fact_id: str, user: CurrentUserDep) -> FactOut:
    return FactOut.model_validate(facts_service.reject(case_id, fact_id, user.id))
