"""The solver. Confirmed facts in, a justified route determination out.

PURE: no network, no LLM, no database. See docs/ARCHITECTURE.md and
tests/test_boundary.py.

Determinism matters here. The route path is solved with ``--models=1`` in
production; :func:`solve_models` lets the tests ask for two and fail if a second
answer set exists, because more than one answer set on the route path is a
rulebase bug rather than a choice to present to the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

import clingo

from app.domain.case import SUPPORTED_PLAN_TYPES, CaseFacts
from app.domain.route import (
    UNVERIFIED_MARKER,
    DeadlineItem,
    RequiredElement,
    RouteDetermination,
    RouteStep,
)
from app.domain.trace import Citation, TraceNode
from app.rules import generate
from app.rules.deadlines import TriggerDates, TriggerUnavailable, resolve_deadline
from app.rules.facts import case_to_facts
from app.rules.trace import build_trace, warning_text

RULEBASE_DIR = Path(__file__).resolve().parent / "rulebase"

#: Loaded in filename order: 00_core, 10_plan_type, 20_track, 30_deadlines,
#: 40_required, 50_expedited, then the state layers.
PROGRAM_GLOB = "*.lp"

#: Human labels for each review level and actor, so the API never ships a bare
#: ASP constant to the UI.
LEVEL_LABELS: dict[str, str] = {
    "internal_1": "Internal appeal",
    "internal_2": "Second internal appeal",
    "external": "Independent external review",
    "expedited_internal": "Urgent internal appeal",
    "expedited_external": "Urgent external review",
}

WHO_LABELS: dict[str, str] = {
    "member_files": "You file",
    "representative_files": "Your representative files",
    "provider_files": "Your doctor's office files",
    "member_requests": "You request",
}

BODY_LABELS: dict[str, str] = {
    "insurer_internal_reviewer": "A reviewer at the insurer who was not part of the first decision",
    "independent_review_organisation": "An independent review organisation, not the insurer",
}

#: Which deadline item belongs to which review level.
LEVEL_DEADLINE_ITEM: dict[str, str] = {
    "internal_1": "internal_appeal",
    "internal_2": "internal_appeal",
    "external": "external_review",
    "expedited_external": "external_review",
}

#: Deadline labels, in the product's voice.
DEADLINE_LABELS: dict[str, str] = {
    "internal_appeal": "File your internal appeal",
    "insurer_response": "The insurer must answer by",
    "external_review": "Request external review",
    "external_review_decision": "The reviewer must decide by",
}


class RulebaseUnsatisfiable(RuntimeError):
    """No answer set. Means an unjustified conclusion — a rulebase bug."""


class RulebaseNondeterministic(RuntimeError):
    """More than one answer set on the route path. Also a rulebase bug."""


@dataclass
class Model:
    """One answer set, as the atoms the runner cares about."""

    tracks: list[str]
    steps: list[tuple[int, str]]
    deadline_specs: list[tuple[str, int, str, str, str, str]]
    requires: list[tuple[str, str, str]]
    review_bodies: dict[str, str]
    who_files: dict[str, str]
    warnings: list[str]
    because: list[clingo.Symbol]
    supported: bool


@lru_cache(maxsize=4)
def _program_text(include_test_state: bool) -> str:
    """The rulebase: generated facts plus every `.lp` file, in filename order."""
    rulebase = generate.load_rulebase(include_test_state=include_test_state)
    parts = [generate.to_facts(rulebase)]
    for path in sorted(RULEBASE_DIR.glob(PROGRAM_GLOB)):
        parts.append(f"\n%% ==== {path.name} ====\n")
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _parse_model(model: clingo.Model) -> Model:
    tracks: list[str] = []
    steps: list[tuple[int, str]] = []
    deadline_specs: list[tuple[str, int, str, str, str, str]] = []
    requires: list[tuple[str, str, str]] = []
    review_bodies: dict[str, str] = {}
    who_files: dict[str, str] = {}
    warnings: list[str] = []
    because: list[clingo.Symbol] = []
    supported = False

    for atom in model.symbols(shown=True):
        name, args = atom.name, atom.arguments
        if name == "track":
            tracks.append(args[0].name)
        elif name == "step":
            steps.append((args[0].number, args[1].name))
        elif name == "deadline_spec":
            deadline_specs.append(
                (
                    args[0].name,
                    args[1].number,
                    args[2].name,
                    args[3].name,
                    args[4].name,
                    args[5].string,
                )
            )
        elif name == "requires":
            requires.append((args[0].name, args[1].name, args[2].string))
        elif name == "review_body":
            review_bodies[args[0].name] = args[1].name
        elif name == "who_files":
            who_files[args[0].name] = args[1].name
        elif name == "warning":
            warnings.append(args[0].string)
        elif name == "because":
            because.append(atom)
        elif name == "supported":
            supported = True

    return Model(
        tracks=tracks,
        steps=sorted(steps),
        deadline_specs=sorted(deadline_specs),
        requires=sorted(requires),
        review_bodies=review_bodies,
        who_files=who_files,
        warnings=sorted(set(warnings)),
        because=because,
        supported=supported,
    )


def solve_models(
    facts: CaseFacts, *, limit: int = 1, include_test_state: bool = False
) -> list[Model]:
    """Solve, returning up to ``limit`` answer sets.

    ``limit=2`` is how the tests assert determinism.
    """
    control = clingo.Control([f"--models={limit}"])
    control.add("base", [], _program_text(include_test_state))
    control.add("case", [], case_to_facts(facts))
    control.ground([("base", []), ("case", [])])

    models: list[Model] = []
    with control.solve(yield_=True) as handle:
        for model in handle:
            models.append(_parse_model(model))
    return models


def solve(facts: CaseFacts, *, include_test_state: bool = False) -> Model:
    """Solve the route path deterministically.

    Raises if there is no answer set (an unjustified conclusion tripped the
    integrity constraint) rather than returning a partial route.
    """
    models = solve_models(facts, limit=1, include_test_state=include_test_state)
    if not models:
        raise RulebaseUnsatisfiable(
            "the rulebase produced no answer set for these facts. Most likely a "
            "derived atom is missing its because/3 justification — see "
            "rulebase/00_core.lp."
        )
    return models[0]


# ---------------------------------------------------------------------------
# Model → RouteDetermination
# ---------------------------------------------------------------------------


def _trigger_dates(facts: CaseFacts, final_adverse_date: date | None = None) -> TriggerDates:
    return TriggerDates(
        denial_date=facts.denial_date,
        denial_received_date=facts.denial_received_date,
        service_date=facts.service_date,
        final_adverse_date=final_adverse_date,
    )


def _fallback_citation(rule_id: str) -> Citation:
    """A citation for a rule the citations table does not list.

    Never silently blank: the rule id is carried through so the gap is visible,
    and `verified` stays False.
    """
    return Citation(source="(citation missing from citations.csv)", locator=rule_id)


def determine_route(
    facts: CaseFacts,
    *,
    rulebase_version: str | None = None,
    final_adverse_date: date | None = None,
    include_test_state: bool = False,
) -> RouteDetermination:
    """The whole route: steps, deadlines, required elements, trace, warnings."""
    rulebase = generate.load_rulebase(include_test_state=include_test_state)
    version = rulebase_version or rulebase.version
    model = solve(facts, include_test_state=include_test_state)
    citations = rulebase.citations
    dates = _trigger_dates(facts, final_adverse_date)

    warnings = [warning_text(code) for code in model.warnings]

    # Unverified values are surfaced, never swallowed. Only rules this
    # determination actually used are named.
    used_rule_ids = {spec[5] for spec in model.deadline_specs} | {r[2] for r in model.requires}
    unverified = sorted(set(rulebase.unverified_rule_ids()) & used_rule_ids)
    if unverified:
        warnings.insert(
            0,
            f"{UNVERIFIED_MARKER}: {len(unverified)} of the legal values behind this "
            "route have not yet been checked against the regulation they cite. The "
            "dates below are our best reading, not a verified one. Check them against "
            "your own letter and your plan document before you rely on them.",
        )

    if facts.plan_type not in SUPPORTED_PLAN_TYPES:
        # No steps, no deadlines, no guess. The warning carries the explanation.
        return RouteDetermination(
            rulebase_version=version,
            facts_hash=facts.facts_hash(),
            plan_type=facts.plan_type,
            steps=[],
            deadlines=[],
            trace=build_trace(model.because, citations),
            warnings=warnings,
            computed_at=datetime.now(tz=UTC),
        )

    # ---- deadlines -------------------------------------------------------
    deadlines: list[DeadlineItem] = []
    by_item: dict[str, DeadlineItem] = {}
    #: Items whose trigger has not happened yet, with the reason to show.
    pending_items: dict[str, str] = {}
    for item, count, unit, trigger, source, rule_id in model.deadline_specs:
        try:
            resolved = resolve_deadline(count=count, unit=unit, trigger=trigger, dates=dates)
        except TriggerUnavailable as unavailable:
            # No date to give, so none is invented. The step says why.
            pending_items[item] = unavailable.explanation
            continue
        deadline = DeadlineItem(
            id=item,
            label=DEADLINE_LABELS.get(item, item.replace("_", " ").capitalize()),
            due_date=resolved.due_date,
            trigger_date=resolved.trigger_date,
            trigger_description=resolved.trigger_description,
            rule_id=rule_id,
            citation=citations.get(rule_id) or _fallback_citation(rule_id),
            is_calendar_days=unit == "calendar",
            source_layer=source,
            count=count,
            ambiguous=resolved.ambiguous,
            ambiguity_note=resolved.ambiguity_note,
        )
        deadlines.append(deadline)
        by_item[item] = deadline

    # ---- required elements per level -------------------------------------
    elements_by_level: dict[str, list[RequiredElement]] = {}
    required_rows = {r.rule_id: r for r in rulebase.required}
    for level, key, rule_id in model.requires:
        row = required_rows.get(rule_id)
        if row is None:  # pragma: no cover -- generator guarantees this
            continue
        elements_by_level.setdefault(level, []).append(
            RequiredElement(
                key=key,
                label=row.label,
                detail=row.detail or None,
                rule_id=rule_id,
                citation=citations.get(rule_id) or _fallback_citation(rule_id),
                mandatory=row.mandatory == "mandatory",
            )
        )

    # ---- steps -----------------------------------------------------------
    steps: list[RouteStep] = []
    ordered_levels = sorted(model.steps)
    for index, (order, level) in enumerate(ordered_levels):
        item = LEVEL_DEADLINE_ITEM.get(level, "internal_appeal")
        step_deadline: DeadlineItem | None = by_item.get(item)
        pending_reason = pending_items.get(item)
        if step_deadline is None and pending_reason is None:  # pragma: no cover
            continue

        response = by_item.get("insurer_response") if level.startswith("internal") else None
        if level in {"external", "expedited_external"}:
            response = by_item.get("external_review_decision")

        steps.append(
            RouteStep(
                order=order,
                level=level,  # type: ignore[arg-type]
                label=LEVEL_LABELS.get(level, level),
                who_files=WHO_LABELS.get(model.who_files.get(level, ""), "You file"),
                required_elements=sorted(
                    elements_by_level.get(level, []),
                    key=lambda e: (not e.mandatory, e.key),
                ),
                review_body=BODY_LABELS.get(model.review_bodies.get(level, ""), "A reviewer"),
                insurer_response_window_days=(
                    response.count if response and response.is_calendar_days else None
                ),
                deadline=step_deadline,
                starts_after=(
                    ordered_levels[index - 1][0] if step_deadline is None and index > 0 else None
                ),
                pending_reason=pending_reason if step_deadline is None else None,
                citation=step_deadline.citation if step_deadline else None,
            )
        )

    trace: list[TraceNode] = build_trace(model.because, citations)

    return RouteDetermination(
        rulebase_version=version,
        facts_hash=facts.facts_hash(),
        plan_type=facts.plan_type,
        steps=steps,
        deadlines=sorted(deadlines, key=lambda d: d.due_date),
        trace=trace,
        warnings=warnings,
        computed_at=datetime.now(tz=UTC),
    )
