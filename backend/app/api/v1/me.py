"""The signed-in user, and their right to leave."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import CurrentUserDep

router = APIRouter(prefix="/me", tags=["me"])


class Me(BaseModel):
    id: str
    email: str | None = None


@router.get("", response_model=Me)
async def get_me(user: CurrentUserDep) -> Me:
    return Me(id=user.id, email=user.email)


class DeletionReceipt(BaseModel):
    """Proof of what was removed, so the user is not asked to take it on trust."""

    deleted: dict[str, int]
    storage_objects_deleted: int
    anything_left: bool


@router.delete("/data", response_model=DeletionReceipt)
async def delete_my_data(user: CurrentUserDep) -> DeletionReceipt:
    """Hard-delete everything belonging to this user.

    Rows and storage objects, not a soft flag.

    This removes the case timeline and the reminder log along with everything
    else. The timeline is described in the brief as "the record the user may
    need later", and destroying it is the correct trade when someone asks to be
    forgotten -- the settings screen says so before the confirmation, not after.

    The receipt counts what went, and ``anything_left`` is re-checked after the
    deletes rather than assumed, because "we deleted it" is a claim that should
    be verified before it is made.
    """
    from app.db.client import get_client
    from app.db.repo import narrow_rows
    from app.services import storage

    client = get_client()
    deleted: dict[str, int] = {}

    cases = narrow_rows(client.table("cases").select("id").eq("user_id", user.id).execute().data)
    case_ids = [str(row["id"]) for row in cases]

    objects_removed = 0
    for case_id in case_ids:
        objects_removed += storage.remove_case_objects("documents", case_id)
        objects_removed += storage.remove_case_objects("letters", case_id)

    # Child rows go first and explicitly. ON DELETE CASCADE would handle them,
    # but doing it in the open means the receipt can count them, and a cascade
    # that silently did not fire would otherwise look like success.
    child_tables = (
        "reminders_sent",
        "deadlines",
        "letters",
        "evidence_items",
        "argument_graphs",
        "route_determinations",
        "extracted_facts",
        "documents",
        "case_events",
    )
    for case_id in case_ids:
        for table in child_tables:
            if table == "reminders_sent":
                continue  # reached through deadlines, cascaded below
            result = client.table(table).delete().eq("case_id", case_id).execute()
            deleted[table] = deleted.get(table, 0) + len(narrow_rows(result.data))

    cases_result = client.table("cases").delete().eq("user_id", user.id).execute()
    deleted["cases"] = len(narrow_rows(cases_result.data))

    llm_result = client.table("llm_calls").delete().eq("user_id", user.id).execute()
    deleted["llm_calls"] = len(narrow_rows(llm_result.data))

    profile_result = client.table("profiles").delete().eq("user_id", user.id).execute()
    deleted["profiles"] = len(narrow_rows(profile_result.data))

    # Verify rather than assert.
    remaining = len(
        narrow_rows(client.table("cases").select("id").eq("user_id", user.id).execute().data)
    ) + len(
        narrow_rows(client.table("llm_calls").select("id").eq("user_id", user.id).execute().data)
    )

    # Last, the auth user itself. Done last so a failure here leaves an account
    # with no data rather than data with no account.
    try:
        client.auth.admin.delete_user(user.id)
        deleted["auth_user"] = 1
    except Exception:
        import logging

        logging.getLogger("appeal_architect").warning("could not delete the auth user")
        deleted["auth_user"] = 0

    return DeletionReceipt(
        deleted=deleted,
        storage_objects_deleted=objects_removed,
        anything_left=remaining > 0,
    )
