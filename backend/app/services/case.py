"""Case lifecycle.

Phase 1: create and list. The stage machine, documents, extraction and the
engine hand-off arrive in phase 4.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.api.v1.cases import CaseSummary
from app.db.client import get_client
from app.domain.case import CaseStage

#: Allowed stage transitions (spec 8). A case may also be abandoned to RESOLVED
#: from anywhere -- the user is entitled to stop.
STAGE_TRANSITIONS: dict[CaseStage, frozenset[CaseStage]] = {
    CaseStage.UPLOADED: frozenset({CaseStage.EXTRACTED}),
    CaseStage.EXTRACTED: frozenset({CaseStage.CONFIRMED}),
    CaseStage.CONFIRMED: frozenset({CaseStage.ROUTED}),
    CaseStage.ROUTED: frozenset({CaseStage.ARGUING}),
    CaseStage.ARGUING: frozenset({CaseStage.EVIDENCE}),
    CaseStage.EVIDENCE: frozenset({CaseStage.LETTER_READY}),
    CaseStage.LETTER_READY: frozenset({CaseStage.SENT}),
    CaseStage.SENT: frozenset({CaseStage.RESPONDED}),
    CaseStage.RESPONDED: frozenset({CaseStage.ESCALATED, CaseStage.RESOLVED}),
    CaseStage.ESCALATED: frozenset({CaseStage.RESPONDED, CaseStage.RESOLVED}),
    CaseStage.RESOLVED: frozenset(),
}


def can_transition(current: CaseStage, target: CaseStage) -> bool:
    if target is CaseStage.RESOLVED:
        return current is not CaseStage.RESOLVED
    return target in STAGE_TRANSITIONS.get(current, frozenset())


def _rows(data: object) -> list[dict[str, object]]:
    """Narrow what the Supabase client hands back.

    Its ``.data`` is typed as a broad JSON union, so a bad shape would otherwise
    only surface as an attribute error deep in validation.
    """
    if data is None:
        return []
    if not isinstance(data, list):
        raise TypeError(f"expected a list of rows from Supabase, got {type(data).__name__}")
    rows: list[dict[str, object]] = []
    for row in data:
        if not isinstance(row, dict):
            raise TypeError(f"expected row objects from Supabase, got {type(row).__name__}")
        rows.append(row)
    return rows


async def list_cases_for_user(user_id: str) -> list[CaseSummary]:
    """Cases for this user, soonest deadline first, undated cases last."""
    client = get_client()
    result = (
        client.table("cases")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    summaries = [CaseSummary.model_validate(row) for row in _rows(result.data)]
    return sorted(
        summaries,
        key=lambda c: (
            c.next_deadline is None,
            c.next_deadline or datetime.max.replace(tzinfo=UTC),
        ),
    )


async def create_case_for_user(
    user_id: str, *, title: str, insurer_name: str | None
) -> CaseSummary:
    client = get_client()
    result = (
        client.table("cases")
        .insert(
            {
                "user_id": user_id,
                "title": title,
                "insurer_name": insurer_name,
                "stage": CaseStage.UPLOADED.value,
            }
        )
        .execute()
    )
    rows = _rows(result.data)
    if not rows:
        raise RuntimeError("Supabase accepted the insert but returned no row")
    return CaseSummary.model_validate(rows[0])
