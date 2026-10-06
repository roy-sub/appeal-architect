"""Justification: where a conclusion came from.

Every derived conclusion in this system carries a trace and a citation. The ASP
layer emits ``because(Conclusion, RuleId, Premises)`` for each derived atom
(rulebase convention, spec 6.3); :class:`TraceNode` is that atom in Python.

A conclusion without a trace is a bug, not a conclusion.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A pointer to the authority a conclusion rests on.

    ``verified`` is False until a human has checked ``locator`` against the real
    source. Unverified citations surface to the user as such -- we would rather
    show someone "we have not checked this" than a confident wrong deadline.
    """

    source: str = Field(
        description="29 CFR 2560.503-1, 45 CFR 147.136, a state statute, or 'plan_document'"
    )
    locator: str = Field(description="Subsection or clause, e.g. '(b)(2)(ii)(B)'")
    title: str | None = Field(default=None, description="Human-readable name of the source")
    quote: str | None = Field(
        default=None, description="The operative sentence, transcribed verbatim"
    )
    url: str | None = None
    verified: bool = Field(
        default=False,
        description="True only once a human has confirmed this against the source",
    )

    def label(self) -> str:
        return f"{self.source} {self.locator}".strip()


class TraceNode(BaseModel):
    """One ``because/3`` atom: this conclusion, by this rule, from these premises."""

    conclusion: str = Field(description="The derived atom, as rendered by the solver")
    rule_id: str = Field(description="fed.*, ca.*, ny.*, tx.*, aca.* or scheme id")
    premises: list[str] = Field(
        default_factory=list, description="The atoms this conclusion was derived from"
    )
    citation: Citation | None = None
    explanation: str | None = Field(
        default=None, description="Plain-language gloss, grade-8 reading level"
    )
