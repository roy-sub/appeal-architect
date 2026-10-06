"""Confirmed facts → ASP facts.

The one entry point into the solver, and the narrowest point in the system. It
takes a :class:`CaseFacts` — which by construction holds only confirmed or
user-edited values — and emits the ground atoms the rulebase reasons over.

Nothing else may put facts into the solver. That is what makes "nothing
unconfirmed reaches the engine" true of the code and not just of the intent.
"""

from __future__ import annotations

from app.domain.case import CaseFacts


def _atom(value: str) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in value.lower())
    if not cleaned or not cleaned[0].isalpha():
        raise ValueError(f"cannot use {value!r} as an ASP constant")
    return cleaned


def case_to_facts(facts: CaseFacts) -> str:
    """Render confirmed case facts as `.lp` atoms."""
    lines = [
        "%% ---- case facts (confirmed by the user) ----",
        f"plan_type({_atom(facts.plan_type.value)}).",
        f"state({_atom(facts.state)}).",
        f"service_timing({_atom(facts.service_timing.value)}).",
        f"filer({_atom(facts.filer)}).",
    ]
    for reason in facts.denial_reasons:
        lines.append(f"denial_reason({_atom(reason.value)}).")
    if facts.is_urgent_medical:
        lines.append("urgent.")
    if facts.denial_received_date is not None:
        # Drives the disclosure warning in 30_deadlines.lp: without a receipt
        # date the filing window is counted from the letter date instead.
        lines.append("has_received_date.")
    return "\n".join(lines) + "\n"
