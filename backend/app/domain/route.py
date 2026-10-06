"""The appeal route: levels, deadlines, required elements.

Everything in this module is computed by the rules engine. The LLM never writes
to any of it. A deadline without a ``rule_id`` and a :class:`Citation` is not a
deadline we are willing to show someone.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.case import PlanType
from app.domain.trace import Citation, TraceNode

ReviewLevel = Literal[
    "internal_1",
    "internal_2",
    "external",
    "expedited_internal",
    "expedited_external",
]

#: Marker prefixed to any warning about a value we have not checked against its
#: source. Surfaced in RouteDetermination.warnings and as a UI banner.
UNVERIFIED_MARKER = "UNVERIFIED"


class DayUnit(StrEnum):
    """Units a regulation actually uses.

    ``MONTHS`` and ``HOURS`` are here because the regulations use them and
    converting them to days would be our invention, not the rule's: 45 CFR
    147.136(d) says "4 months", which is not 120 days, and (b)(2)(ii)(B) says
    "72 hours", which is not 3 calendar days.
    """

    CALENDAR = "calendar"
    BUSINESS = "business"
    MONTHS = "months"
    HOURS = "hours"


class DeadlineItem(BaseModel):
    """A date someone's appeal rights depend on.

    Safety-critical. The arithmetic lives in ``app.rules.deadlines`` as pure
    functions, is unit-tested against a table of worked examples, and is always
    displayed with the rule it came from.

    When the regulation leaves the trigger unclear, the engine computes the
    earlier, more conservative date, sets ``ambiguous`` and fills
    ``ambiguity_note``. The UI must display that note -- a conservative date
    presented as certain is still a misrepresentation.
    """

    id: str
    label: str = Field(description="e.g. 'File internal appeal'")
    due_date: date
    trigger_date: date
    trigger_description: str = Field(description="e.g. '180 days from denial date'")
    rule_id: str
    citation: Citation
    is_calendar_days: bool = Field(
        description="Calendar vs business days is explicit per item, never inferred"
    )
    count: int | None = Field(default=None, description="The day count applied")
    ambiguous: bool = Field(
        default=False, description="True when the regulation's trigger is unclear"
    )
    ambiguity_note: str | None = Field(
        default=None,
        description="What is unclear and which reading we took. Required when ambiguous.",
    )

    def model_post_init(self, _context: object) -> None:
        if self.ambiguous and not self.ambiguity_note:
            raise ValueError(
                f"deadline {self.id!r} is ambiguous but carries no ambiguity_note; "
                "an unexplained conservative date misleads the user"
            )


class RequiredElement(BaseModel):
    """Something the filing must contain for this step to be properly made."""

    key: str
    label: str
    detail: str | None = None
    rule_id: str
    citation: Citation
    mandatory: bool = True


class RouteStep(BaseModel):
    """One level of review, with its deadline and what it requires."""

    order: int = Field(ge=1)
    level: ReviewLevel
    label: str
    who_files: str = Field(description="'You file' / 'They answer' / 'Reviewer decides'")
    required_elements: list[RequiredElement] = Field(default_factory=list)
    review_body: str
    insurer_response_window_days: int | None = None
    deadline: DeadlineItem
    citation: Citation


class RouteDetermination(BaseModel):
    """The engine's answer, pinned to the rulebase version that produced it.

    ``trace`` is the full justification chain. ``warnings`` carries anything the
    user must know about the determination's own reliability -- unverified
    values, an unsupported plan type, an expedited track applied on the user's
    own declaration of urgency.
    """

    id: UUID | None = None
    case_id: UUID | None = None
    rulebase_version: str
    facts_hash: str
    plan_type: PlanType
    steps: list[RouteStep] = Field(default_factory=list)
    deadlines: list[DeadlineItem] = Field(default_factory=list)
    trace: list[TraceNode] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    computed_at: datetime | None = None

    def has_unverified_values(self) -> bool:
        return any(w.startswith(UNVERIFIED_MARKER) for w in self.warnings)

    def next_deadline(self) -> DeadlineItem | None:
        """Soonest deadline. Drives the header pill present on every case screen."""
        return min(self.deadlines, key=lambda d: d.due_date, default=None)
