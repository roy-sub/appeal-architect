"""Confirmed facts + evidence on file → a persisted argument graph.

Recomputed whenever the evidence changes, because attaching a document is what
moves an argument from "Worth adding" to "Solid ground" — and the solver is
what notices, not this module.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.argumentation.builder import build_framework
from app.argumentation.explain import build_graph, evidence_checklist
from app.db import repo
from app.domain.argument import ArgumentGraph
from app.domain.case import CaseStage
from app.services import facts as facts_service


def evidence_on_file(case_id: str, user_id: str) -> set[str]:
    rows = repo.list_for_case("evidence_items", case_id, user_id)
    return {row["key"] for row in rows if row.get("status") == "have"}


def get_stored(case_id: str, user_id: str) -> dict[str, Any] | None:
    rows = repo.list_for_case("argument_graphs", case_id, user_id, order="computed_at", desc=True)
    return rows[0] if rows else None


def compute_graph(case_id: str, user_id: str) -> ArgumentGraph:
    """Build the framework, solve it, persist the result and refresh the checklist."""
    case_facts = facts_service.build_case_facts(case_id, user_id)
    case = repo.get_case(case_id, user_id)
    confirmed = facts_service.confirmed_values(case_id, user_id)

    built = build_framework(
        case_facts,
        evidence_on_file=evidence_on_file(case_id, user_id),
        service=str(confirmed.get("service_description") or "the requested service"),
        condition=str(confirmed.get("condition") or "this condition"),
    )
    graph = build_graph(built)

    payload = graph.model_dump(mode="json")
    repo.insert_for_case(
        "argument_graphs",
        case_id,
        user_id,
        [
            {
                "schemes_version": graph.schemes_version,
                "arguments": payload["arguments"],
                "attacks": payload["attacks"],
                "grounded": payload["grounded_extension"],
                "preferred": payload["preferred_extensions"],
                "stable": payload["stable_extensions"],
                "worth_adding": payload["worth_adding"],
                "defeated": payload["defeated"],
                "trace": payload["trace"],
                "computed_at": datetime.now(tz=UTC).isoformat(),
            }
        ],
    )

    _sync_evidence(case_id, user_id, graph)

    if case.get("stage") in {CaseStage.ROUTED.value, CaseStage.CONFIRMED.value}:
        repo.update_case(case_id, user_id, {"stage": CaseStage.ARGUING.value})
    repo.log_event(
        case_id,
        "arguments_computed",
        {
            "schemes_version": graph.schemes_version,
            "solid": len(graph.grounded_extension),
            "worth_adding": len(graph.worth_adding),
            "left_out": len(graph.defeated),
        },
    )
    return graph


def _sync_evidence(case_id: str, user_id: str, graph: ArgumentGraph) -> None:
    """Derive the checklist from the accepted arguments, keeping what is on file.

    Upserted rather than replaced, so a document the user already attached is
    never quietly detached by a recomputation.
    """
    existing = {row["key"]: row for row in repo.list_for_case("evidence_items", case_id, user_id)}
    on_file = {key for key, row in existing.items() if row.get("status") == "have"}

    rows = []
    for item in evidence_checklist(graph, evidence_on_file=on_file):
        key = str(item["key"])
        previous = existing.get(key)
        rows.append(
            {
                "key": key,
                "label": str(item["label"]),
                "why_needed": _why(item),
                "argument_node_ids": item["supports"],
                "status": previous["status"] if previous else "missing",
                "document_id": previous.get("document_id") if previous else None,
            }
        )
    repo.upsert_for_case("evidence_items", case_id, user_id, rows, on_conflict="case_id,key")


def _why(item: dict[str, Any]) -> str:
    """Why this piece of evidence is being asked for, in the product's voice."""
    supports = item.get("supports") or []
    count = len(supports)
    base = f"Supports {count} of your arguments." if count != 1 else "Supports one argument."
    if item.get("unlocks_a_tier_change"):
        return (
            base + " This is the one that closes off the insurer's likely answer, which "
            "moves the argument onto solid ground."
        )
    return base


def get_checklist(case_id: str, user_id: str) -> list[dict[str, Any]]:
    return repo.list_for_case("evidence_items", case_id, user_id, order="key")


def attach_evidence(
    case_id: str, user_id: str, key: str, document_id: str | None
) -> dict[str, Any]:
    """Mark a checklist item as satisfied, then recompute the graph.

    The recomputation is the point: the tier a document unlocks is computed by
    the solver, so the user sees the argument move rather than being told it did.
    """
    rows = repo.list_for_case("evidence_items", case_id, user_id)
    match = next((row for row in rows if row["key"] == key), None)
    if match is None:
        from app.problem import not_found

        raise not_found("evidence item")

    updated = repo.update_child(
        "evidence_items",
        match["id"],
        case_id,
        user_id,
        {"status": "have", "document_id": document_id},
    )
    repo.log_event(case_id, "evidence_attached", {"key": key})
    compute_graph(case_id, user_id)
    return updated
