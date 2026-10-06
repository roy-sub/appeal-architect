"""The case: what the user told us, and what we read from their documents.

The enum values are wire values. They appear in the database, in the ASP facts
and in the frontend's types, so they are fixed vocabulary -- changing a string
here is a migration, not a rename.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PlanType(StrEnum):
    """What kind of insurance this is. Decides which regulation governs."""

    ACA_MARKETPLACE = "aca_marketplace"
    EMPLOYER_FULLY_INSURED = "employer_fully_insured"
    EMPLOYER_SELF_FUNDED = "employer_self_funded"  # ERISA -- phase 7
    MEDICARE_ADVANTAGE = "medicare_advantage"  # phase 7
    MEDICAID = "medicaid"  # phase 7
    UNKNOWN = "unknown"


#: Plan types the rulebase covers today. Anything else routes to UNKNOWN and the
#: determination carries a warning rather than a guess.
SUPPORTED_PLAN_TYPES: frozenset[PlanType] = frozenset(
    {PlanType.ACA_MARKETPLACE, PlanType.EMPLOYER_FULLY_INSURED}
)


class DenialReason(StrEnum):
    """The insurer's stated ground for refusing. Seeds the argument graph."""

    NOT_MEDICALLY_NECESSARY = "not_medically_necessary"
    PRIOR_AUTH_MISSING = "prior_auth_missing"
    OUT_OF_NETWORK = "out_of_network"
    EXPERIMENTAL = "experimental_investigational"
    CODING_ERROR = "coding_error"
    NOT_COVERED_BENEFIT = "not_covered_benefit"
    OTHER = "other"


class ServiceTiming(StrEnum):
    """Whether the service has happened yet. Changes the insurer's response window."""

    PRE_SERVICE = "pre"
    POST_SERVICE = "post"
    CONCURRENT = "concurrent"


class CaseStage(StrEnum):
    """Case lifecycle (spec 8). Transitions are enforced by the case service."""

    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    CONFIRMED = "confirmed"
    ROUTED = "routed"
    ARGUING = "arguing"
    EVIDENCE = "evidence"
    LETTER_READY = "letter_ready"
    SENT = "sent"
    RESPONDED = "responded"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class DocumentKind(StrEnum):
    DENIAL_LETTER = "denial_letter"
    EOB = "eob"
    PLAN_DOC = "plan_doc"
    MEDICAL_RECORD = "medical_record"
    PHYSICIAN_LETTER = "physician_letter"
    OTHER = "other"


class FactStatus(StrEnum):
    """The confirmation gate.

    Only CONFIRMED and EDITED facts reach the rules engine. There is no code path
    from PENDING to a conclusion -- see :mod:`app.services.route` and
    ``tests/test_boundary.py``.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    REJECTED = "rejected"


#: The only statuses the engine will read. Everything else is a proposal.
ENGINE_READABLE_STATUSES: frozenset[FactStatus] = frozenset(
    {FactStatus.CONFIRMED, FactStatus.EDITED}
)


class SourceSpan(BaseModel):
    """Character offsets into a document's extracted text.

    Real offsets, not approximations: the document viewer highlights exactly
    these characters, so a user can see the sentence a proposed fact came from
    before they confirm it. ``page`` is 1-indexed to match what the viewer shows.
    """

    page: int = Field(ge=1)
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, v: int, info: Any) -> int:
        start = info.data.get("start")
        if start is not None and v < start:
            raise ValueError("span end must not precede span start")
        return v


class ExtractedFact(BaseModel):
    """A proposal from the LLM. Not a fact until the user says so.

    This is the only shape in which LLM output enters the system (spec 4.3). The
    route service reads ``value`` only when ``status`` is in
    :data:`ENGINE_READABLE_STATUSES`; when the user edited the proposal,
    ``edited_value`` is what counts.
    """

    id: UUID | None = None
    case_id: UUID | None = None
    document_id: UUID | None = None
    field: str = Field(description="The CaseFacts field this proposes a value for")
    value: Any = Field(description="What the model read")
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SourceSpan | None = Field(
        default=None,
        description="Where in the document this came from. None only for user-entered facts.",
    )
    status: FactStatus = FactStatus.PENDING
    confirmed_at: datetime | None = None
    edited_value: Any = None

    def effective_value(self) -> Any:
        """The value the engine should use, or raise if this fact is not confirmed.

        Deliberately raises rather than returning None: a silent None here would
        become a missing premise, and a missing premise becomes a wrong route.
        """
        if self.status not in ENGINE_READABLE_STATUSES:
            raise ValueError(
                f"fact {self.field!r} has status {self.status.value!r}; "
                "only confirmed or edited facts may reach the engine"
            )
        if self.status is FactStatus.EDITED:
            return self.edited_value
        return self.value

    def is_low_confidence(self) -> bool:
        """Drives the 'The scan is unclear here' line in the extraction review."""
        return self.confidence < 0.65


class CaseFacts(BaseModel):
    """The confirmed picture of the case. The sole input to the rules engine.

    Every field here is either user-entered or a confirmed extraction. Nothing
    reaches this model while it is still a proposal.
    """

    plan_type: PlanType
    state: str = Field(min_length=2, max_length=2, description="Two-letter US state code")
    insurer_name: str
    member_id_present: bool
    claim_number: str | None = None
    denial_date: date = Field(description="Trigger date for most deadlines")
    denial_received_date: date | None = Field(
        default=None,
        description=(
            "When the member received the notice. Where this differs from "
            "denial_date the regulation's trigger is ambiguous and the engine "
            "takes the earlier, more conservative date."
        ),
    )
    service_date: date | None = None
    service_timing: ServiceTiming
    denial_reasons: list[DenialReason] = Field(min_length=1)
    cited_policy_language: str | None = None
    claim_amount_usd: Decimal | None = None
    is_urgent_medical: bool = Field(
        default=False,
        description=(
            "User's own declaration that delay threatens their health. Drives the "
            "expedited track, so a determination that relies on it says so."
        ),
    )
    filer: Literal["member", "authorized_rep", "provider"]

    @field_validator("state")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @field_validator("denial_reasons")
    @classmethod
    def _dedupe(cls, v: list[DenialReason]) -> list[DenialReason]:
        # Order-preserving dedupe: the first reason stated is the primary one and
        # the argument graph leads with it.
        return list(dict.fromkeys(v))

    def facts_hash(self) -> str:
        """Stable digest for route idempotency (spec 8).

        Keyed on (case_id, facts_hash, rulebase_version), so recomputing a route
        from identical facts under an identical rulebase returns the stored
        determination instead of re-running the solver.
        """
        payload = self.model_dump(mode="json", exclude_none=False)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
