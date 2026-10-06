"""Letter generation, editing and export."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db import repo
from app.deps import CurrentUserDep
from app.problem import ErrorCode, Problem
from app.services import letters as letters_service

router = APIRouter(tags=["letters"])


class LetterOut(BaseModel):
    id: UUID
    case_id: UUID
    argument_graph_id: UUID | None = None
    version: int
    body: dict[str, Any]
    storage_path_pdf: str | None = None
    storage_path_docx: str | None = None
    generated_at: datetime


class ParagraphPatch(BaseModel):
    """One edited paragraph.

    ``argument_node_id`` is preserved from the generated letter rather than
    accepted from the client: a user may rewrite a paragraph's words, but they
    cannot reassign which argument it came from, because the backlink is what
    makes the letter traceable.
    """

    index: int = Field(ge=0)
    text: str = Field(min_length=1)


class LetterPatch(BaseModel):
    paragraphs: list[ParagraphPatch]


@router.post("/cases/{case_id}/letter", response_model=LetterOut)
async def generate_letter(case_id: str, user: CurrentUserDep) -> LetterOut:
    """Write the next version of the appeal letter.

    Every paragraph is either tagged to an argument node the solver accepted, or
    rendered from the fixed procedural template. Untagged model prose is dropped.

    Gated on the Appeal Package. The route, the deadlines and the rule behind
    each one are never gated -- see app/api/v1/billing.py.
    """
    from app.api.v1.billing import require_paid

    require_paid(user.id)
    return LetterOut.model_validate(letters_service.generate_letter(case_id, user.id))


@router.get("/cases/{case_id}/letters", response_model=list[LetterOut])
async def list_letters(case_id: str, user: CurrentUserDep) -> list[LetterOut]:
    rows = repo.list_for_case("letters", case_id, user.id, order="version", desc=True)
    return [LetterOut.model_validate(row) for row in rows]


@router.patch("/cases/{case_id}/letters/{letter_id}", response_model=LetterOut)
async def edit_letter(
    case_id: str, letter_id: str, payload: LetterPatch, user: CurrentUserDep
) -> LetterOut:
    """Apply the user's edits, keeping each paragraph's argument backlink."""
    letter = repo.get_child("letters", letter_id, case_id, user.id)
    body = dict(letter.get("body") or {})
    paragraphs = list(body.get("paragraphs") or [])

    for edit in payload.paragraphs:
        if edit.index >= len(paragraphs):
            raise Problem(
                422,
                ErrorCode.VALIDATION_FAILED,
                f"There is no paragraph {edit.index} in this letter.",
            )
        paragraphs[edit.index] = {**paragraphs[edit.index], "text": edit.text}

    body["paragraphs"] = paragraphs
    body["edited_by_user"] = True
    updated = repo.update_child("letters", letter_id, case_id, user.id, {"body": body})
    repo.log_event(case_id, "letter_edited", {"paragraphs": len(payload.paragraphs)})
    return LetterOut.model_validate(updated)


class ExportResult(BaseModel):
    url: str
    format: Literal["pdf", "docx"]
    expires_in_seconds: int


@router.get("/cases/{case_id}/letters/{letter_id}/export", response_model=ExportResult)
async def export_letter(
    case_id: str,
    letter_id: str,
    user: CurrentUserDep,
    format: Literal["pdf", "docx"] = "pdf",
) -> ExportResult:
    """Render and return a short-lived signed URL."""
    from app.services import storage

    url = letters_service.export(case_id, letter_id, user.id, format)
    return ExportResult(url=url, format=format, expires_in_seconds=storage.SIGNED_URL_TTL_SECONDS)
