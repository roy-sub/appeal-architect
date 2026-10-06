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
    deleted: dict[str, int]
    storage_objects_deleted: int


@router.delete("/data", response_model=DeletionReceipt)
async def delete_my_data(user: CurrentUserDep) -> DeletionReceipt:
    """Hard-delete everything belonging to this user.

    Rows and storage objects, not a soft flag (spec 9). This removes the case
    timeline and the reminder log too: that is the correct trade when someone
    asks to be forgotten, even though it destroys a record they might later
    want. The settings screen says so before the confirmation.

    Implemented in phase 7, where its test proves nothing is left behind.
    """
    from app.problem import ErrorCode, Problem

    raise Problem(
        501,
        ErrorCode.SERVICE_NOT_CONFIGURED,
        "Deleting your data is not available yet. It arrives with the settings "
        "screen, and it will delete rather than hide.",
    )
