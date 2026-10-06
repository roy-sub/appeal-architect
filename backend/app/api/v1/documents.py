"""Document upload, text, and the extraction it triggers."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel

from app.db import repo
from app.deps import CurrentUserDep
from app.domain.case import CaseStage, DocumentKind
from app.problem import ErrorCode, Problem
from app.services import ingestion, llm, storage

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])

#: Upload ceiling. A phone photo is 2-6 MB and a scanned letter under 10; past
#: this it is a plan document somebody meant to send separately.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class DocumentOut(BaseModel):
    id: UUID
    kind: DocumentKind
    filename: str
    mime: str
    page_count: int | None
    ocr_used: bool
    uploaded_at: datetime


class DocumentText(BaseModel):
    """The stored text, which is what source spans index into."""

    id: UUID
    page_count: int
    text: str
    ocr_used: bool


class UploadResult(BaseModel):
    document: DocumentOut
    facts_proposed: int
    pages_transcribed: int


@router.get("", response_model=list[DocumentOut])
async def list_documents(case_id: str, user: CurrentUserDep) -> list[DocumentOut]:
    rows = repo.list_for_case("documents", case_id, user.id, order="uploaded_at")
    return [DocumentOut.model_validate(row) for row in rows]


@router.post("", response_model=UploadResult, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: str,
    user: CurrentUserDep,
    file: Annotated[UploadFile, File()],
    kind: Annotated[DocumentKind, Form()] = DocumentKind.DENIAL_LETTER,
) -> UploadResult:
    """Upload a document, read it, and propose facts from it.

    The proposals come back as ``pending``. Nothing reaches the rules engine
    until the user confirms or corrects each one, with the quoted source text
    shown beside it.
    """
    repo.get_case(case_id, user.id)
    llm.check_monthly_cap(user.id)

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise Problem(
            413,
            ErrorCode.VALIDATION_FAILED,
            f"That file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB. If it "
            "is a plan document, upload just the pages about this treatment.",
        )

    mime = file.content_type or "application/octet-stream"
    document = ingestion.read_document(data, mime, user_id=user.id)

    path = storage.object_path(case_id, file.filename or "upload")
    storage.upload("documents", path, data, mime)

    rows = repo.insert_for_case(
        "documents",
        case_id,
        user.id,
        [
            {
                "kind": kind.value,
                "storage_path": path,
                "filename": storage.safe_filename(file.filename or "upload"),
                "mime": mime,
                "page_count": document.page_count,
                "extracted_text": document.full_text,
                "ocr_used": document.used_transcription,
            }
        ],
    )
    stored = rows[0]

    proposals = ingestion.propose_facts(document, user_id=user.id)
    if proposals:
        repo.insert_for_case(
            "extracted_facts",
            case_id,
            user.id,
            [
                {
                    "document_id": stored["id"],
                    "field": fact.field,
                    "value": fact.value,
                    "confidence": fact.confidence,
                    "source_page": fact.source_span.page if fact.source_span else None,
                    "source_start": fact.source_span.start if fact.source_span else None,
                    "source_end": fact.source_span.end if fact.source_span else None,
                    "status": fact.status.value,
                }
                for fact in proposals
            ],
        )

    repo.update_case(case_id, user.id, {"stage": CaseStage.EXTRACTED.value})
    repo.log_event(
        case_id,
        "document_uploaded",
        {
            "kind": kind.value,
            "pages": document.page_count,
            "transcribed": document.used_transcription,
            "facts_proposed": len(proposals),
        },
    )

    return UploadResult(
        document=DocumentOut.model_validate(stored),
        facts_proposed=len(proposals),
        pages_transcribed=sum(1 for page in document.pages if page.transcribed),
    )


@router.get("/{document_id}/text", response_model=DocumentText)
async def get_document_text(case_id: str, document_id: str, user: CurrentUserDep) -> DocumentText:
    """The document's text, for the viewer to highlight spans against."""
    row = repo.get_child("documents", document_id, case_id, user.id)
    return DocumentText(
        id=row["id"],
        page_count=row.get("page_count") or 1,
        text=row.get("extracted_text") or "",
        ocr_used=bool(row.get("ocr_used")),
    )


class SignedUrl(BaseModel):
    url: str
    expires_in_seconds: int


@router.get("/{document_id}/url", response_model=SignedUrl)
async def get_document_url(case_id: str, document_id: str, user: CurrentUserDep) -> SignedUrl:
    """A short-lived signed URL. The bucket is private; nothing is served publicly."""
    row = repo.get_child("documents", document_id, case_id, user.id)
    return SignedUrl(
        url=storage.signed_url("documents", row["storage_path"]),
        expires_in_seconds=storage.SIGNED_URL_TTL_SECONDS,
    )
