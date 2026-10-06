"""The argument graph.

A Dung abstract argumentation framework (Dung 1995) -- arguments plus a binary
attack relation -- with a structured layer that builds those arguments from
schemes and confirmed facts. Acceptability is computed by ASP encodings of
grounded, preferred and stable semantics in ``app/argumentation/semantics.lp``.

The solver computes defeat. The application never asserts it, and neither does
the LLM: an argument is in ``grounded_extension`` because the solver put it
there, which is what makes "solid ground" a claim we can stand behind.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.trace import Citation, TraceNode

AttackKind = Literal["rebut", "undermine", "undercut"]
ArgumentSide = Literal["insurer", "patient"]
ArgumentStrength = Literal["strong", "conditional"]

#: User-facing tier labels. Fixed strings from the design brief -- these exact
#: words, nowhere paraphrased.
TIER_SOLID_GROUND = "Solid ground"
TIER_WORTH_ADDING = "Worth adding"
TIER_LEFT_OUT = "Left out"


class Premise(BaseModel):
    """One thing an argument depends on, and the evidence that establishes it."""

    id: str
    text: str
    evidence_key: str | None = Field(default=None, description="Key into the evidence checklist")
    satisfied: bool = Field(
        default=False, description="Whether the evidence for this premise is on file"
    )


class Argument(BaseModel):
    """One argument in the framework.

    ``required_evidence`` unsatisfied does not remove the argument -- the UI shows
    it as "needs this to hold", so the user can see what would make it stand.
    """

    id: str
    side: ArgumentSide
    scheme_id: str | None = Field(
        default=None, description="None for the insurer's own stated reason"
    )
    claim: str = Field(description="The rendered assertion")
    premises: list[Premise] = Field(default_factory=list)
    required_evidence: list[str] = Field(
        default_factory=list, description="evidence_item keys this argument needs"
    )
    citations: list[Citation] = Field(default_factory=list)
    strength: ArgumentStrength = "conditional"

    def unsatisfied_evidence(self) -> list[str]:
        return [p.evidence_key for p in self.premises if p.evidence_key and not p.satisfied]


class Attack(BaseModel):
    """A directed attack. ``note`` is the plain-language reason, for the UI."""

    source_id: str
    target_id: str
    kind: AttackKind
    note: str = ""


class ArgumentGraph(BaseModel):
    """The framework plus its computed extensions, pinned to a schemes version.

    - ``grounded_extension`` -- the unique sceptical extension. This is "Solid ground".
    - ``worth_adding`` -- in some preferred extension but not in grounded. "Worth adding".
    - ``defeated`` -- in no preferred extension. "Left out", kept visible so the user
      can see it was considered.
    """

    id: UUID | None = None
    case_id: UUID | None = None
    schemes_version: str
    arguments: list[Argument] = Field(default_factory=list)
    attacks: list[Attack] = Field(default_factory=list)
    grounded_extension: list[str] = Field(default_factory=list)
    preferred_extensions: list[list[str]] = Field(default_factory=list)
    stable_extensions: list[list[str]] = Field(default_factory=list)
    worth_adding: list[str] = Field(default_factory=list)
    defeated: list[str] = Field(default_factory=list)
    trace: list[TraceNode] = Field(default_factory=list)
    computed_at: datetime | None = None

    def by_id(self, argument_id: str) -> Argument | None:
        return next((a for a in self.arguments if a.id == argument_id), None)

    def tier_of(self, argument_id: str) -> str | None:
        """The user-facing tier for an argument, or None if it is the insurer's."""
        if argument_id in self.grounded_extension:
            return TIER_SOLID_GROUND
        if argument_id in self.worth_adding:
            return TIER_WORTH_ADDING
        if argument_id in self.defeated:
            return TIER_LEFT_OUT
        return None
