"""The rules engine: routes, traces, citations, determinism, state overrides.

Every assertion here is a property the product promises:

- every conclusion carries a trace, a citation and a rule id
- exactly one answer set on the route path (more is a rulebase bug)
- an unsupported plan type produces no route rather than a guessed one
- unverified values reach the user as a warning
- the federal-default / state-override path works, proven with the synthetic
  state `XX` so no real legal value has to be invented to test it
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.domain.case import CaseFacts, DenialReason, PlanType, ServiceTiming
from app.domain.route import UNVERIFIED_MARKER
from app.rules import generate
from app.rules.runner import determine_route, solve_models
from app.rules.trace import EXPLANATIONS, WARNINGS

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def facts(**overrides) -> CaseFacts:
    base = {
        "plan_type": PlanType.ACA_MARKETPLACE,
        "state": "CA",
        "insurer_name": "Example Health",
        "member_id_present": True,
        "claim_number": "CLM-4471902",
        "denial_date": date(2026, 9, 14),
        "service_timing": ServiceTiming.POST_SERVICE,
        "denial_reasons": [DenialReason.NOT_MEDICALLY_NECESSARY],
        "filer": "member",
    }
    return CaseFacts(**{**base, **overrides})


# ===========================================================================
# Determinism
# ===========================================================================


def test_exactly_one_answer_set() -> None:
    """More than one answer set on the route path is a rulebase bug.

    Asking for two and getting one is the assertion; asking for one would prove
    nothing.
    """
    models = solve_models(facts(), limit=2)
    assert len(models) == 1, "the rulebase is nondeterministic on the route path"


@pytest.mark.parametrize("timing", list(ServiceTiming))
@pytest.mark.parametrize("urgent", [False, True])
@pytest.mark.parametrize("filer", ["member", "authorized_rep", "provider"])
def test_deterministic_across_the_fact_space(timing, urgent, filer) -> None:
    """Determinism is not a property of one happy path."""
    models = solve_models(
        facts(service_timing=timing, is_urgent_medical=urgent, filer=filer), limit=2
    )
    assert len(models) == 1


def test_the_same_facts_give_the_same_route_twice() -> None:
    a = determine_route(facts())
    b = determine_route(facts())
    assert a.facts_hash == b.facts_hash
    assert [d.due_date for d in a.deadlines] == [d.due_date for d in b.deadlines]
    assert [n.rule_id for n in a.trace] == [n.rule_id for n in b.trace]


# ===========================================================================
# Every conclusion is justified and cited
# ===========================================================================


def test_every_trace_node_carries_a_rule_id() -> None:
    route = determine_route(facts())
    assert route.trace
    assert all(node.rule_id for node in route.trace)


def test_every_deadline_carries_a_rule_id_and_a_citation() -> None:
    route = determine_route(facts())
    assert route.deadlines
    for deadline in route.deadlines:
        assert deadline.rule_id, f"{deadline.id} has no rule id"
        assert deadline.citation.source, f"{deadline.id} has no citation source"
        assert "missing from citations.csv" not in deadline.citation.source, (
            f"{deadline.id} cites rule {deadline.rule_id} which citations.csv does not list"
        )


def test_every_required_element_carries_a_citation() -> None:
    route = determine_route(facts())
    elements = [e for step in route.steps for e in step.required_elements]
    assert elements
    for element in elements:
        assert element.rule_id and element.citation.source
        assert "missing from citations.csv" not in element.citation.source, (
            f"required element {element.key} cites {element.rule_id}, "
            "which citations.csv does not list"
        )


def test_every_procedural_rule_has_a_plain_language_explanation() -> None:
    """A rule with no gloss renders bare ASP at a frightened person.

    The explanations are written by hand -- an LLM gloss of a legal conclusion is
    the thing this architecture exists to prevent.

    `fed.required.*` rules are excluded because their user-facing text is the
    element's own `label` and `detail` from the table, asserted separately in
    test_every_required_element_reads_as_plain_language. Giving them a second
    gloss would mean two strings to keep in step.
    """
    route = determine_route(facts(is_urgent_medical=True, filer="authorized_rep"))
    missing = sorted(
        {
            node.rule_id
            for node in route.trace
            if node.rule_id.startswith("fed.")
            and not node.rule_id.startswith("fed.required.")
            and node.rule_id not in EXPLANATIONS
        }
    )
    assert not missing, f"rule ids with no entry in EXPLANATIONS: {missing}"


def test_every_required_element_reads_as_plain_language() -> None:
    """Each element carries its own label and detail, which is what the user sees."""
    route = determine_route(facts(is_urgent_medical=True, filer="authorized_rep"))
    elements = [e for step in route.steps for e in step.required_elements]
    assert elements
    for element in elements:
        assert element.label and not element.label.endswith("."), (
            f"{element.key}: the label is a noun phrase, not a sentence"
        )
        assert element.detail, f"{element.key} has no detail line"
        assert "!" not in element.label and "!" not in element.detail, (
            f"{element.key}: the product never uses exclamation marks"
        )


def test_every_warning_the_rulebase_can_raise_has_product_copy() -> None:
    """A warning code with no copy would show the user a bare identifier."""
    rulebase_text = ""
    for path in sorted((Path(__file__).parent.parent / "app/rules/rulebase").glob("*.lp")):
        rulebase_text += path.read_text(encoding="utf-8")

    import re

    codes = set(re.findall(r'warning\("([^"]+)"\)', rulebase_text))
    # The constant-defined one, declared with #const in 00_core.lp.
    codes.add("plan_type_unsupported")
    missing = sorted(codes - set(WARNINGS))
    assert not missing, f"warning codes with no entry in WARNINGS: {missing}"


# ===========================================================================
# The route itself
# ===========================================================================


def test_standard_aca_route_is_internal_then_external() -> None:
    route = determine_route(facts())
    assert [s.level for s in route.steps] == ["internal_1", "external"]
    assert route.steps[0].who_files == "You file"
    assert "independent" in route.steps[1].review_body.lower()


def test_the_headline_filing_deadline_is_13_march_2027() -> None:
    """The engine's answer for the design prototype's own demo case.

    The prototype said 22 Mar 2027. It was nine days late.
    """
    route = determine_route(facts())
    internal = next(d for d in route.deadlines if d.id == "internal_appeal")
    assert internal.due_date == date(2027, 3, 13)
    assert internal.ambiguous is True
    assert internal.ambiguity_note and "earlier" in internal.ambiguity_note


def test_the_external_step_is_undated_until_the_internal_appeal_is_answered() -> None:
    """No fabricated date, and the step says why."""
    route = determine_route(facts())
    external = next(s for s in route.steps if s.level == "external")
    assert external.deadline is None
    assert external.starts_after == 1
    assert external.pending_reason and "has not happened yet" in external.pending_reason


def test_the_external_step_gets_a_date_once_the_final_denial_exists() -> None:
    route = determine_route(facts(), final_adverse_date=date(2027, 1, 20))
    external = next(s for s in route.steps if s.level == "external")
    assert external.deadline is not None
    assert external.deadline.due_date == date(2027, 5, 20)


@pytest.mark.parametrize(
    ("timing", "expected_days"),
    [
        (ServiceTiming.PRE_SERVICE, 30),
        (ServiceTiming.POST_SERVICE, 60),
        (ServiceTiming.CONCURRENT, 30),
    ],
)
def test_insurer_response_window_follows_the_confirmed_service_timing(
    timing: ServiceTiming, expected_days: int
) -> None:
    route = determine_route(facts(service_timing=timing))
    response = next(d for d in route.deadlines if d.id == "insurer_response")
    assert response.count == expected_days


def test_next_deadline_is_the_filing_deadline_not_the_insurers_own() -> None:
    """Sanity check on ordering: the user's own action should surface first only
    when it is genuinely soonest. Here the insurer's window is shorter, and the
    engine reports it as such rather than hiding it."""
    route = determine_route(facts())
    nxt = route.next_deadline()
    assert nxt is not None
    assert nxt.due_date == min(d.due_date for d in route.deadlines)


# ===========================================================================
# The expedited track
# ===========================================================================


def test_urgency_shortens_the_insurers_clock_not_the_users_filing_window() -> None:
    """The correctness point that is easy to get backwards.

    "Expedited" governs how fast the insurer must answer. It does NOT shorten the
    member's own filing window. Modelling it the other way round would shorten a
    real deadline on the strength of a self-declaration.
    """
    standard = determine_route(facts())
    urgent = determine_route(facts(is_urgent_medical=True))

    standard_filing = next(d for d in standard.deadlines if d.id == "internal_appeal")
    urgent_filing = next(d for d in urgent.deadlines if d.id == "internal_appeal")
    assert urgent_filing.due_date == standard_filing.due_date

    standard_response = next(d for d in standard.deadlines if d.id == "insurer_response")
    urgent_response = next(d for d in urgent.deadlines if d.id == "insurer_response")
    assert urgent_response.due_date < standard_response.due_date
    assert urgent_response.count == 72
    assert urgent_response.is_calendar_days is False


def test_the_expedited_route_says_it_rests_on_the_users_own_statement() -> None:
    """A self-declaration that changes a legal conclusion is always disclosed."""
    route = determine_route(facts(is_urgent_medical=True))
    joined = " ".join(route.warnings).lower()
    assert "your statement" in joined or "you said" in joined
    assert "doctor" in joined


def test_the_expedited_route_adds_the_urgent_external_level() -> None:
    route = determine_route(facts(is_urgent_medical=True))
    assert "expedited_external" in [s.level for s in route.steps]


def test_urgency_requires_a_written_urgency_statement() -> None:
    route = determine_route(facts(is_urgent_medical=True))
    keys = {e.key for step in route.steps for e in step.required_elements}
    assert "urgency_statement" in keys


# ===========================================================================
# Who files
# ===========================================================================


@pytest.mark.parametrize(
    ("filer", "expected"),
    [
        ("member", "You file"),
        ("authorized_rep", "Your representative files"),
        ("provider", "Your doctor's office files"),
    ],
)
def test_who_files_reflects_the_confirmed_filer(filer: str, expected: str) -> None:
    route = determine_route(facts(filer=filer))
    assert route.steps[0].who_files == expected


@pytest.mark.parametrize("filer", ["authorized_rep", "provider"])
def test_a_non_member_filer_must_attach_authorisation(filer: str) -> None:
    route = determine_route(facts(filer=filer))
    keys = {e.key for step in route.steps for e in step.required_elements}
    assert "rep_authorisation" in keys


def test_a_member_filing_for_themselves_needs_no_authorisation() -> None:
    route = determine_route(facts(filer="member"))
    keys = {e.key for step in route.steps for e in step.required_elements}
    assert "rep_authorisation" not in keys


# ===========================================================================
# Unsupported plan types produce no route, not a guess
# ===========================================================================


@pytest.mark.parametrize(
    "plan_type",
    [
        PlanType.EMPLOYER_SELF_FUNDED,
        PlanType.MEDICARE_ADVANTAGE,
        PlanType.MEDICAID,
        PlanType.UNKNOWN,
    ],
)
def test_an_unsupported_plan_type_gets_no_steps_and_no_deadlines(plan_type) -> None:
    """A confident wrong track is worse than an honest "we cannot work this out".

    No steps, no dates, and a warning that explains it.
    """
    route = determine_route(facts(plan_type=plan_type))
    assert route.steps == []
    assert route.deadlines == []
    assert route.warnings
    assert any("cannot work out" in w or "do not know" in w for w in route.warnings)


def test_an_employer_plan_warns_about_a_possible_second_internal_level() -> None:
    """Group plans may run two internal rounds where the individual market runs one.

    We model one and say so: filing the first on time is correct either way, so
    the conservative route is also the safe one.
    """
    route = determine_route(facts(plan_type=PlanType.EMPLOYER_FULLY_INSURED))
    assert any("two rounds" in w for w in route.warnings)
    assert route.steps, "a supported plan type must still produce a route"


# ===========================================================================
# Unverified values reach the user
# ===========================================================================


def test_the_route_warns_that_its_legal_values_are_unverified() -> None:
    """Hard rule 5. Every seed value is unverified today, so every route says so."""
    route = determine_route(facts())
    assert route.has_unverified_values()
    banner = next(w for w in route.warnings if w.startswith(UNVERIFIED_MARKER))
    assert "not yet been checked" in banner
    assert "check them against your own letter" in banner.lower()


def test_no_table_row_claims_to_be_verified() -> None:
    """A row flipped to verified=true without a human reading the source would
    silently remove the user's warning. Pinned until someone does that work."""
    rulebase = generate.load_rulebase(include_test_state=True)
    claimed = [r.rule_id for r in rulebase.deadlines if r.verified]
    claimed += [r.rule_id for r in rulebase.required if r.verified]
    claimed += [r.rule_id for r in rulebase.overrides if r.verified]
    assert not claimed, (
        "these rows claim verified=true; if that is real, update this test and say "
        f"in the changelog who checked them: {claimed}"
    )


# ===========================================================================
# The state-override mechanism, proven without inventing a real value
# ===========================================================================


def test_the_real_state_tables_are_empty_so_the_federal_baseline_governs() -> None:
    """CA, NY and TX ship with zero override rows, deliberately.

    We have no statute source for them. A plausible-looking invented state
    deadline, shown with a citation beside it as the date someone's rights
    expire, is the most harmful artefact this codebase could contain.
    """
    overrides = generate.read_state_overrides(include_test_state=False)
    assert overrides == [], (
        "a real state override appeared. If it came from a statute you read, "
        "update this test and the changelog. If not, remove it."
    )


@pytest.mark.parametrize("state", ["CA", "NY", "TX"])
def test_every_supported_state_falls_through_to_the_federal_window(state: str) -> None:
    route = determine_route(facts(state=state))
    internal = next(d for d in route.deadlines if d.id == "internal_appeal")
    assert internal.count == 180
    assert internal.rule_id.startswith("fed.")


def test_a_state_override_displaces_the_federal_default() -> None:
    """The override mechanism, exercised with the synthetic test state.

    `XX` is not a US state code, so no real user can reach it, and the federal
    default / state override path is still fully proven.
    """
    federal = determine_route(facts(state="CA"), include_test_state=True)
    overridden = determine_route(facts(state="XX"), include_test_state=True)

    fed_internal = next(d for d in federal.deadlines if d.id == "internal_appeal")
    xx_internal = next(d for d in overridden.deadlines if d.id == "internal_appeal")

    assert fed_internal.count == 180 and fed_internal.rule_id.startswith("fed.")
    assert xx_internal.count == 240 and xx_internal.rule_id.startswith("xx.")
    assert xx_internal.due_date > fed_internal.due_date


def test_an_override_is_traced_to_the_state_rule_not_the_federal_one() -> None:
    route = determine_route(facts(state="XX"), include_test_state=True)
    rule_ids = {node.rule_id for node in route.trace}
    assert any(r.startswith("xx.") for r in rule_ids)
    assert "fed.internal_appeal.window" not in rule_ids, (
        "the federal rule should be displaced, not sit alongside the override"
    )


def test_the_override_path_works_for_a_month_unit_too() -> None:
    """Proves the mechanism is not day-count specific."""
    route = determine_route(
        facts(state="XX"), final_adverse_date=date(2027, 1, 20), include_test_state=True
    )
    external = next(d for d in route.deadlines if d.id == "external_review")
    assert external.count == 6 and external.rule_id.startswith("xx.")
    assert external.due_date == date(2027, 7, 20)


def test_the_test_state_is_absent_from_a_production_build() -> None:
    """A fixture that leaked into the live rulebase would be a real legal value."""
    assert generate.read_state_overrides(include_test_state=False) == []
    production = generate.load_rulebase(include_test_state=False)
    assert not any(r.state == "xx" for r in production.overrides)


# ===========================================================================
# Golden route fixtures
# ===========================================================================


def _golden_files() -> list[Path]:
    return sorted(GOLDEN_DIR.glob("*.json"))


def test_golden_fixtures_exist() -> None:
    assert _golden_files(), "no golden route fixtures found in tests/golden/"


@pytest.mark.parametrize("path", _golden_files(), ids=lambda p: p.stem)
def test_golden_route(path: Path) -> None:
    """Each fixture is a worked example: these facts, this route, these dates."""
    case = json.loads(path.read_text(encoding="utf-8"))
    given = case["facts"]
    expected = case["expect"]

    route = determine_route(
        CaseFacts(
            plan_type=PlanType(given["plan_type"]),
            state=given["state"],
            insurer_name=given.get("insurer_name", "Example Health"),
            member_id_present=given.get("member_id_present", True),
            claim_number=given.get("claim_number"),
            denial_date=date.fromisoformat(given["denial_date"]),
            denial_received_date=(
                date.fromisoformat(given["denial_received_date"])
                if given.get("denial_received_date")
                else None
            ),
            service_timing=ServiceTiming(given["service_timing"]),
            denial_reasons=[DenialReason(r) for r in given["denial_reasons"]],
            is_urgent_medical=given.get("is_urgent_medical", False),
            filer=given.get("filer", "member"),
        ),
        final_adverse_date=(
            date.fromisoformat(given["final_adverse_date"])
            if given.get("final_adverse_date")
            else None
        ),
    )

    assert [s.level for s in route.steps] == expected["levels"], case["why"]

    for item, due in expected["deadlines"].items():
        found = next((d for d in route.deadlines if d.id == item), None)
        assert found is not None, f"{item} missing from the route"
        assert found.due_date.isoformat() == due, f"{item}: {case['why']}"

    for item in expected.get("undated", []):
        assert all(d.id != item for d in route.deadlines), (
            f"{item} should have no date yet: {case['why']}"
        )

    for item in expected.get("ambiguous", []):
        found = next(d for d in route.deadlines if d.id == item)
        assert found.ambiguous, f"{item} should be flagged ambiguous"
        assert found.ambiguity_note


def test_a_deadline_records_which_layer_produced_it() -> None:
    """'California law gives you longer' is information the user wants, so the
    engine carries the layer rather than flattening everything to one number."""
    federal = determine_route(facts(state="CA"), include_test_state=True)
    overridden = determine_route(facts(state="XX"), include_test_state=True)

    fed_internal = next(d for d in federal.deadlines if d.id == "internal_appeal")
    xx_internal = next(d for d in overridden.deadlines if d.id == "internal_appeal")

    assert fed_internal.source_layer == "federal"
    assert xx_internal.source_layer == "xx"
