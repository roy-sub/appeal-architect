"""Confirmed facts → a persisted route determination.

Idempotent per ``(case_id, facts_hash, rulebase_version)``: recomputing from
identical facts under identical rules returns the stored determination instead
of re-running the solver, so the user never sees two different answers to the
same question.

This module imports the rules engine. The engine does not import it, and cannot:
see docs/ARCHITECTURE.md.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.db import repo
from app.domain.case import CaseStage
from app.domain.route import RouteDetermination
from app.rules.runner import determine_route
from app.services import facts as facts_service


def _final_adverse_date(case_id: str, user_id: str) -> date | None:
    """When the insurer gave its final internal answer, if it has.

    Recorded on the case when the user escalates. Until then the external-review
    step is correctly undated rather than dated from something else.
    """
    case = repo.get_case(case_id, user_id)
    raw = case.get("final_adverse_date")
    return date.fromisoformat(str(raw)[:10]) if raw else None


def get_stored(case_id: str, user_id: str) -> dict[str, Any] | None:
    rows = repo.list_for_case(
        "route_determinations", case_id, user_id, order="computed_at", desc=True
    )
    return rows[0] if rows else None


def compute_route(case_id: str, user_id: str) -> RouteDetermination:
    """Work out the route and persist it.

    Raises a 409 naming the pending fields when any required fact is
    unconfirmed. Nothing here fills a gap with a default: a default would become
    a premise, and a premise becomes a deadline.
    """
    case_facts = facts_service.build_case_facts(case_id, user_id)
    determination = determine_route(
        case_facts, final_adverse_date=_final_adverse_date(case_id, user_id)
    )

    stored = get_stored(case_id, user_id)
    if (
        stored
        and stored.get("facts_hash") == determination.facts_hash
        and stored.get("rulebase_version") == determination.rulebase_version
    ):
        # Identical facts, identical rules. Return what is already recorded
        # rather than writing a second row that says the same thing.
        return _from_row(stored)

    payload = determination.model_dump(mode="json")
    row = {
        "rulebase_version": determination.rulebase_version,
        "facts_hash": determination.facts_hash,
        "plan_type": determination.plan_type.value,
        "steps": payload["steps"],
        "deadlines": payload["deadlines"],
        "trace": payload["trace"],
        "warnings": payload["warnings"],
        "computed_at": datetime.now(tz=UTC).isoformat(),
    }
    repo.insert_for_case("route_determinations", case_id, user_id, [row])

    # The deadlines table is what the reminder job reads, so it is replaced
    # wholesale: a stale row beside a fresh one would show two dates for a step
    # and could email the user about the wrong one.
    repo.replace_for_case(
        "deadlines",
        case_id,
        user_id,
        [
            {
                "item_id": deadline.id,
                "label": deadline.label,
                "due_date": deadline.due_date.isoformat(),
                "trigger_date": deadline.trigger_date.isoformat(),
                "rule_id": deadline.rule_id,
                "citation": deadline.citation.model_dump(mode="json"),
                "ambiguous": deadline.ambiguous,
                "ambiguity_note": deadline.ambiguity_note,
            }
            for deadline in determination.deadlines
        ],
    )

    if determination.steps:
        repo.update_case(case_id, user_id, {"stage": CaseStage.ROUTED.value})
    repo.log_event(
        case_id,
        "route_computed",
        {
            "rulebase_version": determination.rulebase_version,
            "steps": len(determination.steps),
            "warnings": len(determination.warnings),
        },
    )
    return determination


def _from_row(row: dict[str, Any]) -> RouteDetermination:
    return RouteDetermination.model_validate(
        {
            "id": row["id"],
            "case_id": row["case_id"],
            "rulebase_version": row["rulebase_version"],
            "facts_hash": row["facts_hash"],
            "plan_type": row["plan_type"],
            "steps": row["steps"],
            "deadlines": row["deadlines"],
            "trace": row["trace"],
            "warnings": row["warnings"],
            "computed_at": row["computed_at"],
        }
    )
