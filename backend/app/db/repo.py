"""Thin data access over Supabase.

Every function takes the ``user_id`` derived from a verified JWT and scopes by
it. The backend uses the service-role key and therefore bypasses RLS, so this
module is the enforcement point for normal traffic; RLS is the backstop for
anything that reaches Postgres another way.
"""

from __future__ import annotations

from typing import Any

from app.db.client import get_client
from app.problem import forbidden, not_found


def narrow_rows(data: object) -> list[dict[str, Any]]:
    """Narrow what the Supabase client hands back.

    Its ``.data`` is typed as a broad JSON union, so a bad shape would otherwise
    surface only as an attribute error deep inside validation.
    """
    if data is None:
        return []
    if not isinstance(data, list):
        raise TypeError(f"expected rows from Supabase, got {type(data).__name__}")
    out: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            raise TypeError(f"expected row objects, got {type(row).__name__}")
        out.append(row)
    return out


def one(data: object) -> dict[str, Any] | None:
    rows = narrow_rows(data)
    return rows[0] if rows else None


# ---- cases -----------------------------------------------------------------


def get_case(case_id: str, user_id: str) -> dict[str, Any]:
    """Fetch a case, or raise. Scoped by user, so a wrong id is a 404 either way.

    A case belonging to someone else returns the same 404 as one that does not
    exist: telling a caller that an id is real but not theirs is free
    information about another person's account.
    """
    result = (
        get_client()
        .table("cases")
        .select("*")
        .eq("id", case_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = one(result.data)
    if row is None:
        raise not_found("case")
    return row


def update_case(case_id: str, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    get_case(case_id, user_id)
    result = (
        get_client().table("cases").update(patch).eq("id", case_id).eq("user_id", user_id).execute()
    )
    row = one(result.data)
    if row is None:  # pragma: no cover
        raise forbidden()
    return row


def delete_case(case_id: str, user_id: str) -> None:
    get_case(case_id, user_id)
    get_client().table("cases").delete().eq("id", case_id).eq("user_id", user_id).execute()


# ---- generic child-table helpers ------------------------------------------
#
# Every child table hangs off cases.id, so one pair of helpers covers them all
# once the case has been checked.


def list_for_case(
    table: str, case_id: str, user_id: str, *, order: str | None = None, desc: bool = False
) -> list[dict[str, Any]]:
    get_case(case_id, user_id)
    query = get_client().table(table).select("*").eq("case_id", case_id)
    if order:
        query = query.order(order, desc=desc)
    return narrow_rows(query.execute().data)


def insert_for_case(
    table: str, case_id: str, user_id: str, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    get_case(case_id, user_id)
    if not rows:
        return []
    payload = [{**row, "case_id": case_id} for row in rows]
    return narrow_rows(get_client().table(table).insert(payload).execute().data)


def upsert_for_case(
    table: str,
    case_id: str,
    user_id: str,
    rows: list[dict[str, Any]],
    *,
    on_conflict: str,
) -> list[dict[str, Any]]:
    get_case(case_id, user_id)
    if not rows:
        return []
    payload = [{**row, "case_id": case_id} for row in rows]
    return narrow_rows(
        get_client().table(table).upsert(payload, on_conflict=on_conflict).execute().data
    )


def replace_for_case(
    table: str, case_id: str, user_id: str, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Delete this case's rows in ``table`` and insert the new set.

    Used where a recomputation supersedes everything that came before -- the
    deadline set after a route is recomputed, for instance. Keeping stale rows
    beside fresh ones would show a user two different deadlines for one step.
    """
    get_case(case_id, user_id)
    get_client().table(table).delete().eq("case_id", case_id).execute()
    return insert_for_case(table, case_id, user_id, rows)


def get_child(table: str, row_id: str, case_id: str, user_id: str) -> dict[str, Any]:
    get_case(case_id, user_id)
    result = (
        get_client()
        .table(table)
        .select("*")
        .eq("id", row_id)
        .eq("case_id", case_id)
        .limit(1)
        .execute()
    )
    row = one(result.data)
    if row is None:
        raise not_found("record")
    return row


def update_child(
    table: str, row_id: str, case_id: str, user_id: str, patch: dict[str, Any]
) -> dict[str, Any]:
    get_child(table, row_id, case_id, user_id)
    result = (
        get_client().table(table).update(patch).eq("id", row_id).eq("case_id", case_id).execute()
    )
    row = one(result.data)
    if row is None:  # pragma: no cover
        raise not_found("record")
    return row


def log_event(case_id: str, kind: str, detail: dict[str, Any] | None = None) -> None:
    """Append to the case timeline.

    Never raises into the caller: the timeline is a record of what happened, and
    failing to write it must not fail the thing that happened.
    """
    try:
        get_client().table("case_events").insert(
            {"case_id": case_id, "kind": kind, "detail": detail or {}}
        ).execute()
    except Exception:
        import logging

        logging.getLogger("appeal_architect").warning("could not log case event %s", kind)
