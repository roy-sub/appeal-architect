"""The argument graph and the evidence checklist derived from it."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.argumentation.explain import TIER_EXPLANATIONS, argument_detail
from app.deps import CurrentUserDep
from app.domain.argument import ArgumentGraph
from app.problem import not_found
from app.services import arguments as arguments_service

router = APIRouter(prefix="/cases/{case_id}", tags=["arguments"])


class GraphResponse(BaseModel):
    graph: ArgumentGraph
    #: The fixed tier copy, so the UI never paraphrases it.
    tier_explanations: dict[str, str]


def _from_row(row: dict[str, Any]) -> ArgumentGraph:
    return ArgumentGraph.model_validate(
        {
            "id": row["id"],
            "case_id": row["case_id"],
            "schemes_version": row["schemes_version"],
            "arguments": row["arguments"],
            "attacks": row["attacks"],
            "grounded_extension": row["grounded"],
            "preferred_extensions": row["preferred"],
            "stable_extensions": row.get("stable") or [],
            "worth_adding": row["worth_adding"],
            "defeated": row["defeated"],
            "trace": row["trace"],
            "computed_at": row["computed_at"],
        }
    )


@router.post("/arguments", response_model=GraphResponse)
async def compute_arguments(case_id: str, user: CurrentUserDep) -> GraphResponse:
    graph = arguments_service.compute_graph(case_id, user.id)
    return GraphResponse(graph=graph, tier_explanations=TIER_EXPLANATIONS)


@router.get("/arguments", response_model=GraphResponse)
async def get_arguments(case_id: str, user: CurrentUserDep) -> GraphResponse:
    stored = arguments_service.get_stored(case_id, user.id)
    if stored is None:
        raise not_found("argument graph")
    return GraphResponse(graph=_from_row(stored), tier_explanations=TIER_EXPLANATIONS)


@router.get("/arguments/{argument_id}", response_model=dict)
async def get_argument_detail(
    case_id: str, argument_id: str, user: CurrentUserDep
) -> dict[str, Any]:
    """One argument in full: what it asserts, what it needs, what they would say back."""
    stored = arguments_service.get_stored(case_id, user.id)
    if stored is None:
        raise not_found("argument graph")
    graph = _from_row(stored)
    on_file = arguments_service.evidence_on_file(case_id, user.id)
    try:
        return argument_detail(graph, argument_id, evidence_on_file=on_file)
    except KeyError:
        raise not_found("argument") from None


class EvidenceItemOut(BaseModel):
    key: str
    label: str
    why_needed: str | None = None
    argument_node_ids: list[str] = []
    status: str
    document_id: str | None = None


class AttachRequest(BaseModel):
    document_id: str | None = None


@router.get("/evidence", response_model=list[EvidenceItemOut])
async def get_evidence(case_id: str, user: CurrentUserDep) -> list[EvidenceItemOut]:
    return [
        EvidenceItemOut.model_validate(row)
        for row in arguments_service.get_checklist(case_id, user.id)
    ]


@router.post("/evidence/{key}/attach", response_model=EvidenceItemOut)
async def attach_evidence(
    case_id: str, key: str, payload: AttachRequest, user: CurrentUserDep
) -> EvidenceItemOut:
    """Mark an item satisfied. The graph is recomputed, so a tier may move."""
    return EvidenceItemOut.model_validate(
        arguments_service.attach_evidence(case_id, user.id, key, payload.document_id)
    )
