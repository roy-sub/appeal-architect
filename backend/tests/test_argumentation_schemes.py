"""The scheme library and the builder.

Two properties the product depends on:

1. Defeat is **computed**, never asserted. Known rebuttals become real arguments
   in the framework, so the solver decides.
2. Missing evidence does not delete an argument. It marks the premise
   unsatisfied, and the UI shows "needs this to hold".
"""

from __future__ import annotations

from datetime import date

import pytest

from app.argumentation.builder import (
    INSURER_CLAIMS,
    SchemeError,
    build_framework,
    load_schemes,
    schemes_for,
)
from app.argumentation.explain import (
    TIER_EXPLANATIONS,
    argument_detail,
    build_graph,
    evidence_checklist,
)
from app.domain.argument import TIER_SOLID_GROUND, TIER_WORTH_ADDING
from app.domain.case import CaseFacts, DenialReason, PlanType, ServiceTiming

#: The five denial reasons the MVP covers (spec 7.2).
MVP_REASONS = [
    DenialReason.NOT_MEDICALLY_NECESSARY,
    DenialReason.PRIOR_AUTH_MISSING,
    DenialReason.OUT_OF_NETWORK,
    DenialReason.EXPERIMENTAL,
    DenialReason.CODING_ERROR,
]


def facts(**overrides) -> CaseFacts:
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


# ===========================================================================
# The library
# ===========================================================================


def test_the_library_loads() -> None:
    schemes, version = load_schemes()
    assert schemes and version


@pytest.mark.parametrize("reason", MVP_REASONS, ids=lambda r: r.value)
def test_each_mvp_denial_reason_has_three_to_five_schemes(reason: DenialReason) -> None:
    """Spec 7.2. Fewer than three and the graph is thin; more than five and the
    user is reading a list rather than seeing an argument."""
    found = schemes_for(reason)
    assert 3 <= len(found) <= 5, f"{reason.value} has {len(found)} schemes"


@pytest.mark.parametrize("reason", MVP_REASONS, ids=lambda r: r.value)
def test_every_scheme_has_at_least_one_known_rebuttal(reason: DenialReason) -> None:
    """A scheme with no rebuttal cannot be contested, so the solver has nothing
    to compute and the tier would be a label rather than a result."""
    for scheme in schemes_for(reason):
        assert scheme.known_rebuttals, f"{scheme.id} has no known rebuttals"


def test_every_premise_names_the_evidence_that_establishes_it() -> None:
    schemes, _ = load_schemes()
    for scheme in schemes:
        for premise in scheme.premises:
            assert premise.get("evidence"), (
                f"{scheme.id}: premise {premise['id']} names no evidence, so the "
                "checklist cannot tell the user what to get"
            )


def test_every_rebuttal_says_what_would_answer_it() -> None:
    """A rebuttal with no answer is a dead end: the user is told the insurer has
    a reply and given no way to close it off."""
    schemes, _ = load_schemes()
    for scheme in schemes:
        for rebuttal in scheme.known_rebuttals:
            assert rebuttal.get("defeated_by_evidence"), (
                f"{scheme.id}: rebuttal {rebuttal['id']} names no "
                "defeated_by_evidence, leaving the user nothing to do"
            )


def test_scheme_ids_are_unique_and_namespaced() -> None:
    schemes, _ = load_schemes()
    ids = [s.id for s in schemes]
    assert len(ids) == len(set(ids))
    assert all("." in i for i in ids), "scheme ids are namespaced, e.g. mn.plan_own_criteria"


def test_every_insurer_reason_has_a_sentence() -> None:
    """Otherwise the graph's first card shows an enum value."""
    for reason in DenialReason:
        assert reason in INSURER_CLAIMS
        assert INSURER_CLAIMS[reason].endswith(".")


def test_claim_templates_read_as_sentences_not_jargon() -> None:
    schemes, _ = load_schemes()
    for scheme in schemes:
        claim = scheme.claim_template
        assert claim[0].isupper() or claim.startswith("{"), f"{scheme.id}: not a sentence"
        assert "!" not in claim, f"{scheme.id}: the product never uses exclamation marks"
        for banned in ("guaranteed", "we'll win", "fight back", "loophole"):
            assert banned not in claim.lower(), f"{scheme.id} uses banned language: {banned}"


def test_a_malformed_scheme_is_refused(tmp_path) -> None:
    from app.argumentation import builder

    bad = tmp_path / "bad.yaml"
    bad.write_text("id: x\ndenial_reason: nonsense\nside: patient\n", encoding="utf-8")
    with pytest.raises(SchemeError):
        builder._load_scheme(bad)


def test_a_scheme_with_an_unknown_attack_kind_is_refused(tmp_path) -> None:
    from app.argumentation import builder

    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "id: x\ndenial_reason: coding_error\nside: patient\n"
        "claim_template: Something\nstrength: strong\n"
        "premises:\n  - id: p\n    text: t\n    evidence: e\n"
        "attacks:\n  - target: insurer.coding_error\n    kind: shouts_at\n",
        encoding="utf-8",
    )
    with pytest.raises(SchemeError, match="attack kind"):
        builder._load_scheme(bad)


# ===========================================================================
# Building the framework
# ===========================================================================


def test_the_insurers_reason_becomes_an_argument() -> None:
    built = build_framework(facts())
    insurer = [a for a in built.arguments if a.side == "insurer"]
    assert any(a.id == "insurer.not_medically_necessary" for a in insurer)


def test_known_rebuttals_become_real_arguments_in_the_framework() -> None:
    """The property that makes defeat computed rather than asserted."""
    built = build_framework(facts())
    rebuttals = [a.id for a in built.arguments if ".rebuttal." in a.id]
    assert rebuttals
    for rebuttal in rebuttals:
        assert any(attack.source_id == rebuttal for attack in built.attacks), (
            f"{rebuttal} is in the framework but attacks nothing"
        )


def test_missing_evidence_marks_the_premise_but_keeps_the_argument() -> None:
    """Spec 7.2. The UI shows "needs this to hold" rather than hiding it."""
    built = build_framework(facts(), evidence_on_file=set())
    scheme_args = [a for a in built.arguments if a.scheme_id and a.side == "patient"]
    assert scheme_args, "the schemes should still instantiate with no evidence"
    unsatisfied = [a for a in scheme_args if a.unsatisfied_evidence()]
    assert unsatisfied, "with no evidence, premises should read as unsatisfied"


def test_evidence_on_file_satisfies_the_matching_premises() -> None:
    built = build_framework(facts(), evidence_on_file={"plan_clinical_policy"})
    argument = next(a for a in built.arguments if a.id == "mn.plan_own_criteria")
    satisfied = {p.evidence_key for p in argument.premises if p.satisfied}
    assert "plan_clinical_policy" in satisfied
    assert "medical_records" not in satisfied


def test_multiple_denial_reasons_produce_multiple_insurer_arguments() -> None:
    built = build_framework(
        facts(denial_reasons=[DenialReason.NOT_MEDICALLY_NECESSARY, DenialReason.OUT_OF_NETWORK])
    )
    insurer_ids = {
        a.id for a in built.arguments if a.side == "insurer" and ".rebuttal." not in a.id
    }
    assert insurer_ids == {"insurer.not_medically_necessary", "insurer.out_of_network"}


def test_a_scheme_only_attacks_the_reason_actually_stated() -> None:
    """A counter-argument for a reason the insurer did not give would be noise."""
    built = build_framework(facts(denial_reasons=[DenialReason.CODING_ERROR]))
    targets = {a.target_id for a in built.attacks if a.target_id.startswith("insurer.")}
    assert targets == {"insurer.coding_error"}


def test_the_claim_template_is_filled_in() -> None:
    built = build_framework(
        facts(insurer_name="Anthem Blue Cross"),
        service="the infusion",
        condition="Crohn disease",
    )
    claims = " ".join(a.claim for a in built.arguments)
    assert "Anthem Blue Cross" in claims
    assert "the infusion" in claims
    assert "{" not in claims, "an unfilled placeholder would reach the user"


@pytest.mark.parametrize("reason", MVP_REASONS, ids=lambda r: r.value)
def test_every_mvp_reason_builds_a_solvable_framework(reason: DenialReason) -> None:
    graph = build_graph(build_framework(facts(denial_reasons=[reason])))
    assert graph.arguments
    assert graph.grounded_extension or graph.worth_adding, (
        f"{reason.value} produced no acceptable argument at all"
    )


# ===========================================================================
# The tiers, and how evidence moves an argument between them
# ===========================================================================


def test_with_no_evidence_nothing_is_solid_ground() -> None:
    """Honest: before you have the documents, nothing holds unconditionally."""
    graph = build_graph(build_framework(facts(), evidence_on_file=set()))
    assert graph.grounded_extension == []
    assert graph.worth_adding, "the arguments are contestable, not dead"


def test_attaching_the_answering_evidence_moves_an_argument_to_solid_ground() -> None:
    """The product's core mechanism, end to end.

    Attaching the page that shows which policy version was in force on the
    service date answers the insurer's known rebuttal, and the solver -- not the
    application -- is what notices.
    """
    before = build_graph(build_framework(facts(), evidence_on_file=set()))
    assert "mn.plan_own_criteria" in before.worth_adding
    assert "mn.plan_own_criteria" not in before.grounded_extension

    after = build_graph(
        build_framework(
            facts(),
            evidence_on_file={
                "plan_clinical_policy",
                "medical_records",
                "policy_version_in_effect_on_service_date",
            },
        )
    )
    assert "mn.plan_own_criteria" in after.grounded_extension
    assert "mn.plan_own_criteria" not in after.worth_adding


def test_an_argument_whose_rebuttal_is_unanswered_stays_worth_adding() -> None:
    graph = build_graph(
        build_framework(
            facts(),
            evidence_on_file={"plan_clinical_policy", "medical_records"},
        )
    )
    # The version rebuttal is unanswered, so this one is contestable.
    assert "mn.plan_own_criteria" in graph.worth_adding


def test_the_tiers_never_overlap() -> None:
    graph = build_graph(build_framework(facts(), evidence_on_file={"plan_clinical_policy"}))
    solid = set(graph.grounded_extension)
    adding = set(graph.worth_adding)
    out = set(graph.defeated)
    assert not (solid & adding) and not (solid & out) and not (adding & out)


def test_the_insurers_own_reason_is_in_no_tier() -> None:
    """It is the thing being attacked, not one of the user's options."""
    graph = build_graph(build_framework(facts()))
    assert graph.tier_of("insurer.not_medically_necessary") is None
    assert "insurer.not_medically_necessary" not in graph.grounded_extension


def test_grounded_is_a_subset_of_every_preferred_extension() -> None:
    """Dung's theorem, checked on a real product framework rather than a fixture."""
    graph = build_graph(
        build_framework(facts(), evidence_on_file={"plan_clinical_policy", "medical_records"})
    )
    for extension in graph.preferred_extensions:
        assert set(graph.grounded_extension) <= set(extension)


def test_tier_copy_is_the_fixed_design_strings() -> None:
    assert TIER_EXPLANATIONS[TIER_SOLID_GROUND].startswith("These stand up to whatever")
    assert "fair answer" in TIER_EXPLANATIONS[TIER_WORTH_ADDING]
    assert "stays visible" in TIER_EXPLANATIONS["Left out"]


# ===========================================================================
# The output contract
# ===========================================================================


def test_every_tiered_argument_has_a_trace_node() -> None:
    graph = build_graph(build_framework(facts(), evidence_on_file={"plan_clinical_policy"}))
    tiered = set(graph.grounded_extension) | set(graph.worth_adding) | set(graph.defeated)
    traced = {node.conclusion.split(": ", 1)[1] for node in graph.trace}
    assert tiered == traced


def test_the_trace_names_the_semantics_that_decided_the_tier() -> None:
    graph = build_graph(build_framework(facts(), evidence_on_file={"plan_clinical_policy"}))
    rule_ids = {node.rule_id for node in graph.trace}
    assert rule_ids <= {"af.grounded", "af.preferred_not_grounded", "af.defeated"}
    assert all(node.explanation for node in graph.trace)


def test_argument_detail_gives_the_verdict_as_a_sentence() -> None:
    """Never an icon. "Does not defeat it" is something a person can act on."""
    evidence = {
        "plan_clinical_policy",
        "medical_records",
        "policy_version_in_effect_on_service_date",
    }
    graph = build_graph(build_framework(facts(), evidence_on_file=evidence))
    detail = argument_detail(graph, "mn.plan_own_criteria", evidence_on_file=evidence)

    assert detail["tier"] == TIER_SOLID_GROUND
    assert detail["verdict"] == "Does not defeat it"
    assert detail["holds_now"] is True
    assert detail["insurer_replies"], "the panel must show what they would say back"
    assert all(isinstance(r["verdict"], str) for r in detail["insurer_replies"])


def test_argument_detail_lists_what_is_still_missing() -> None:
    graph = build_graph(build_framework(facts(), evidence_on_file=set()))
    detail = argument_detail(graph, "mn.step_therapy_completed", evidence_on_file=set())
    assert detail["missing_evidence"]
    assert detail["holds_now"] is False


def test_argument_detail_refuses_an_unknown_id() -> None:
    graph = build_graph(build_framework(facts()))
    with pytest.raises(KeyError):
        argument_detail(graph, "no.such.argument")


def test_the_evidence_checklist_is_deduped_and_links_back() -> None:
    """Spec 8: deduped across arguments, each item naming the nodes that need it,
    so "why am I being asked for this?" always has an answer on screen."""
    graph = build_graph(build_framework(facts(), evidence_on_file=set()))
    checklist = evidence_checklist(graph, evidence_on_file=set())

    keys = [item["key"] for item in checklist]
    assert len(keys) == len(set(keys)), "the checklist should be deduped"
    assert checklist
    for item in checklist:
        assert item["supports"], f"{item['key']} links back to no argument"


def test_the_checklist_puts_what_is_still_missing_first() -> None:
    graph = build_graph(build_framework(facts(), evidence_on_file={"plan_clinical_policy"}))
    checklist = evidence_checklist(graph, evidence_on_file={"plan_clinical_policy"})
    statuses = [item["status"] for item in checklist]
    assert statuses == sorted(statuses, key=lambda s: s == "have"), (
        "a tired person should not have to scroll past what they already have"
    )


def test_schemes_version_is_recorded_on_the_graph() -> None:
    """So any graph the product has shown can be reproduced."""
    graph = build_graph(build_framework(facts()))
    assert graph.schemes_version
