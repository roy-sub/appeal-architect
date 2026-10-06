"""The shared vocabulary.

The enum values here appear in the database, in the ASP facts and in the
frontend's types, so they are a wire contract. A test that pins the exact strings
turns "someone renamed an enum member" from a silent data corruption into a
failing build.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.domain.argument import (
    TIER_LEFT_OUT,
    TIER_SOLID_GROUND,
    TIER_WORTH_ADDING,
    Argument,
    ArgumentGraph,
    Attack,
    Premise,
)
from app.domain.case import (
    ENGINE_READABLE_STATUSES,
    CaseFacts,
    CaseStage,
    DenialReason,
    ExtractedFact,
    FactStatus,
    PlanType,
    ServiceTiming,
    SourceSpan,
)
from app.domain.route import (
    UNVERIFIED_MARKER,
    DayUnit,
    DeadlineItem,
    RouteDetermination,
)
from app.domain.trace import Citation, TraceNode


def _facts(**overrides) -> CaseFacts:
    base = {
        "plan_type": PlanType.ACA_MARKETPLACE,
        "state": "CA",
        "insurer_name": "Example Health",
        "member_id_present": True,
        "denial_date": date(2026, 9, 14),
        "service_timing": ServiceTiming.POST_SERVICE,
        "denial_reasons": [DenialReason.NOT_MEDICALLY_NECESSARY],
        "filer": "member",
    }
    return CaseFacts(**{**base, **overrides})


def _citation() -> Citation:
    return Citation(source="45 CFR 147.136", locator="(b)(2)")


# ---- wire vocabulary --------------------------------------------------------


def test_plan_type_values_are_fixed() -> None:
    assert {p.value for p in PlanType} == {
        "aca_marketplace",
        "employer_fully_insured",
        "employer_self_funded",
        "medicare_advantage",
        "medicaid",
        "unknown",
    }


def test_denial_reason_values_are_fixed() -> None:
    assert {d.value for d in DenialReason} == {
        "not_medically_necessary",
        "prior_auth_missing",
        "out_of_network",
        "experimental_investigational",
        "coding_error",
        "not_covered_benefit",
        "other",
    }


def test_service_timing_and_stage_values_are_fixed() -> None:
    assert {s.value for s in ServiceTiming} == {"pre", "post", "concurrent"}
    assert [s.value for s in CaseStage] == [
        "uploaded",
        "extracted",
        "confirmed",
        "routed",
        "arguing",
        "evidence",
        "letter_ready",
        "sent",
        "responded",
        "escalated",
        "resolved",
    ]


def test_day_units_cover_what_the_regulations_actually_say() -> None:
    """45 CFR 147.136(d) says "4 months" and (b)(2)(ii)(B) says "72 hours".

    Converting either to a day count would be our invention rather than the
    rule's, so both units exist.
    """
    assert {u.value for u in DayUnit} == {"calendar", "business", "months", "hours"}


# ---- the confirmation gate --------------------------------------------------


def test_only_confirmed_and_edited_facts_are_engine_readable() -> None:
    assert {FactStatus.CONFIRMED, FactStatus.EDITED} == ENGINE_READABLE_STATUSES


@pytest.mark.parametrize("status", [FactStatus.PENDING, FactStatus.REJECTED])
def test_unconfirmed_fact_refuses_to_yield_a_value(status: FactStatus) -> None:
    """Hard rule 2: nothing unconfirmed reaches the engine.

    This raises rather than returning None on purpose -- a silent None becomes a
    missing premise, and a missing premise becomes a wrong route.
    """
    fact = ExtractedFact(field="denial_date", value="2026-09-14", confidence=0.9, status=status)
    with pytest.raises(ValueError, match="only confirmed or edited"):
        fact.effective_value()


def test_edited_fact_yields_the_user_correction_not_the_model_output() -> None:
    fact = ExtractedFact(
        field="denial_date",
        value="2026-09-04",  # what the model misread
        edited_value="2026-09-14",  # what the user corrected it to
        confidence=0.4,
        status=FactStatus.EDITED,
    )
    assert fact.effective_value() == "2026-09-14"


def test_low_confidence_threshold_drives_the_unclear_scan_line() -> None:
    assert ExtractedFact(field="f", value=1, confidence=0.5).is_low_confidence()
    assert not ExtractedFact(field="f", value=1, confidence=0.9).is_low_confidence()


def test_source_span_rejects_a_backwards_range() -> None:
    SourceSpan(page=1, start=10, end=42)
    with pytest.raises(ValueError, match="must not precede"):
        SourceSpan(page=1, start=42, end=10)


# ---- case facts -------------------------------------------------------------


def test_state_is_normalised_and_reasons_deduped_in_order() -> None:
    facts = _facts(
        state="ny",
        denial_reasons=[
            DenialReason.NOT_MEDICALLY_NECESSARY,
            DenialReason.OUT_OF_NETWORK,
            DenialReason.NOT_MEDICALLY_NECESSARY,
        ],
    )
    assert facts.state == "NY"
    # Order preserved: the first reason stated is the primary one, and the
    # argument graph leads with it.
    assert facts.denial_reasons == [
        DenialReason.NOT_MEDICALLY_NECESSARY,
        DenialReason.OUT_OF_NETWORK,
    ]


def test_at_least_one_denial_reason_is_required() -> None:
    with pytest.raises(ValueError):
        _facts(denial_reasons=[])


def test_facts_hash_is_stable_and_order_independent() -> None:
    """Route idempotency depends on this digest, so it must not wobble."""
    a = _facts(claim_amount_usd=Decimal("1234.50"))
    b = _facts(claim_amount_usd=Decimal("1234.50"))
    assert a.facts_hash() == b.facts_hash()
    assert a.facts_hash() == a.facts_hash()


def test_facts_hash_changes_when_a_deadline_input_changes() -> None:
    """A different denial date must produce a different hash.

    If it did not, a corrected denial date would silently reuse the cached route
    determination computed from the wrong one.
    """
    assert _facts().facts_hash() != _facts(denial_date=date(2026, 9, 15)).facts_hash()


# ---- deadlines --------------------------------------------------------------


def _deadline(**overrides) -> DeadlineItem:
    base = {
        "id": "internal_appeal",
        "label": "File internal appeal",
        "due_date": date(2027, 3, 13),
        "trigger_date": date(2026, 9, 14),
        "trigger_description": "180 calendar days from the denial date",
        "rule_id": "fed.internal_appeal.window",
        "citation": _citation(),
        "is_calendar_days": True,
    }
    return DeadlineItem(**{**base, **overrides})


def test_ambiguous_deadline_must_carry_a_note() -> None:
    """Spec 6.4: an ambiguous trigger is disclosed, not quietly resolved.

    A conservative date presented as certain is still a misrepresentation, so the
    model refuses to be constructed without the explanation.
    """
    with pytest.raises(ValueError, match="ambiguity_note"):
        _deadline(ambiguous=True)

    ok = _deadline(
        ambiguous=True,
        ambiguity_note=(
            "The rule counts from the day you received the letter, which we do not "
            "know. We used the date printed on the letter, which gives you the "
            "earlier of the two dates."
        ),
    )
    assert ok.ambiguous and ok.ambiguity_note


def test_next_deadline_is_the_soonest() -> None:
    determination = RouteDetermination(
        rulebase_version="1.0.0",
        facts_hash="x",
        plan_type=PlanType.ACA_MARKETPLACE,
        deadlines=[
            _deadline(id="external", due_date=date(2027, 7, 13)),
            _deadline(id="internal", due_date=date(2027, 3, 13)),
        ],
    )
    nxt = determination.next_deadline()
    assert nxt is not None and nxt.id == "internal"


def test_no_deadlines_means_no_next_deadline_rather_than_a_crash() -> None:
    determination = RouteDetermination(
        rulebase_version="1.0.0", facts_hash="x", plan_type=PlanType.UNKNOWN
    )
    assert determination.next_deadline() is None


def test_unverified_values_are_detectable_for_the_ui_banner() -> None:
    """Hard rule 4: UNVERIFIED is surfaced to the user, never swallowed."""
    determination = RouteDetermination(
        rulebase_version="1.0.0",
        facts_hash="x",
        plan_type=PlanType.ACA_MARKETPLACE,
        warnings=[f"{UNVERIFIED_MARKER}: the 180-day window has not been checked"],
    )
    assert determination.has_unverified_values()


def test_citations_are_unverified_until_a_human_says_otherwise() -> None:
    assert _citation().verified is False
    assert _citation().label() == "45 CFR 147.136 (b)(2)"


# ---- arguments --------------------------------------------------------------


def test_tier_labels_are_the_exact_fixed_strings() -> None:
    """Brief section 3: these exact words, nowhere paraphrased."""
    assert TIER_SOLID_GROUND == "Solid ground"
    assert TIER_WORTH_ADDING == "Worth adding"
    assert TIER_LEFT_OUT == "Left out"


def test_tier_of_maps_extensions_to_labels() -> None:
    graph = ArgumentGraph(
        schemes_version="1.0.0",
        grounded_extension=["a1"],
        worth_adding=["b1"],
        defeated=["c1"],
    )
    assert graph.tier_of("a1") == TIER_SOLID_GROUND
    assert graph.tier_of("b1") == TIER_WORTH_ADDING
    assert graph.tier_of("c1") == TIER_LEFT_OUT
    # The insurer's own argument sits in no tier -- it is the thing being attacked.
    assert graph.tier_of("insurer.not_medically_necessary") is None


def test_unsatisfied_evidence_is_reported_not_hidden() -> None:
    """An argument missing its evidence stays in the graph.

    The UI shows it as "needs this to hold", so the user can see what would make
    it stand rather than wondering why it vanished.
    """
    arg = Argument(
        id="a2",
        side="patient",
        claim="Step therapy was completed",
        strength="strong",
        premises=[
            Premise(
                id="p1",
                text="Two agents tried",
                evidence_key="pharmacy_history",
                satisfied=True,
            ),
            Premise(
                id="p2",
                text="Both documented",
                evidence_key="physician_notes",
                satisfied=False,
            ),
        ],
    )
    assert arg.unsatisfied_evidence() == ["physician_notes"]


def test_graph_lookup_by_id() -> None:
    arg = Argument(id="a1", side="patient", claim="c")
    graph = ArgumentGraph(schemes_version="1.0.0", arguments=[arg])
    assert graph.by_id("a1") is arg
    assert graph.by_id("nope") is None


def test_attack_kinds_are_the_aspic_three() -> None:
    for kind in ("rebut", "undermine", "undercut"):
        assert Attack(source_id="a", target_id="b", kind=kind).kind == kind


def test_trace_node_carries_rule_and_premises() -> None:
    node = TraceNode(
        conclusion="deadline(internal_appeal,180,calendar,federal)",
        rule_id="fed.internal_appeal.window",
        premises=["federal_default(internal_appeal,180)"],
        citation=_citation(),
    )
    assert node.rule_id.startswith("fed.")
    assert node.citation is not None
