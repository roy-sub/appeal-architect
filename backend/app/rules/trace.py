"""because/3 atoms → TraceNode.

The rulebase emits ``because(Conclusion, RuleId, Premises)`` for every derived
atom, and an integrity constraint makes an unjustified model unsatisfiable. This
turns those atoms into the structure the UI renders, attaching the citation for
each rule id.

Plain-language explanations live here too, keyed by rule id. They are written
rather than generated: an LLM gloss of a legal conclusion is exactly the thing
this architecture exists to prevent.
"""

from __future__ import annotations

import clingo

from app.domain.trace import Citation, TraceNode

#: Grade-8 plain language for each rule, shown in the deadline drawer and the
#: trace view. A rule id with no entry here renders without a gloss rather than
#: with a guessed one.
EXPLANATIONS: dict[str, str] = {
    "fed.internal_appeal.window": (
        "Federal rules give you at least 180 days from when you got the denial to "
        "ask the insurer to look at it again."
    ),
    "fed.insurer_response.pre_service": (
        "Because the treatment has not happened yet, the insurer has 30 days to answer."
    ),
    "fed.insurer_response.post_service": (
        "Because the treatment has already happened, the insurer has 60 days to answer."
    ),
    "fed.insurer_response.concurrent": (
        "Because this is treatment you are in the middle of, the insurer has 30 days to answer."
    ),
    "fed.insurer_response.urgent": (
        "Because you said delay would harm your health, the insurer has to answer as "
        "soon as possible and no later than 72 hours."
    ),
    "fed.external_review.window": (
        "If the insurer says no again, you have four months from that final answer to "
        "take it to an outside reviewer."
    ),
    "fed.external_review.decision": (
        "The outside reviewer has 45 days to decide. Their decision binds the insurer."
    ),
    "fed.external_review.decision_expedited": (
        "For an urgent case the outside reviewer has 72 hours to decide."
    ),
    "fed.track.standard": "You are on the standard timeline.",
    "fed.track.expedited": (
        "You are on the urgent timeline because you told us delay would harm your health."
    ),
    "fed.level.internal_1": (
        "The first step is an appeal to the insurer itself. You cannot skip it."
    ),
    "fed.level.external": (
        "If they refuse again, an independent organisation reviews it. That decision "
        "binds the insurer."
    ),
    "fed.level.expedited_external": (
        "An urgent case can go to the outside reviewer on a 72-hour clock."
    ),
    "fed.step.internal_first": "The insurer gets the first look. This is step one.",
    "fed.step.external_after_internal": (
        "Outside review comes after the insurer has given its final answer."
    ),
    "fed.step.expedited_external_available": (
        "For an urgent case, outside review can run at the same time as the insurer's "
        "own review rather than after it."
    ),
    "fed.who_files.internal": "You, or the person you have authorised, sends this in.",
    "fed.who_files.external": "You ask for the outside review yourself.",
    "fed.who_files.expedited_external": "You ask for the urgent outside review yourself.",
    "fed.review_body.internal": "Someone at the insurer who was not part of the first decision.",
    "fed.review_body.external": "An independent review organisation, not the insurer.",
    "fed.review_body.expedited_external": "An independent review organisation, on a 72-hour clock.",
}

#: Warnings the rulebase can raise, in the product's own voice. A warning code
#: with no entry is a rulebase bug, asserted in the tests.
WARNINGS: dict[str, str] = {
    "plan_type_unsupported": (
        "We cannot work out the appeal route for this kind of plan yet, so we have not "
        "guessed one. What we can tell you is on the roadmap; the rest needs a person."
    ),
    "plan_type_unknown": (
        "We do not know what kind of insurance this is, and the rules depend on it. "
        "Tell us and we will work out your route."
    ),
    "employer_plan_may_have_second_internal_level": (
        "Employer plans sometimes have two rounds of internal appeal rather than one. "
        "We have shown one. Check your plan document, because if there is a second "
        "round you have to go through it before outside review."
    ),
    "filing_window_counted_from_letter_date": (
        "The rule counts your filing window from the day the letter reached you, and "
        "we do not know that date. We counted from the date printed on the letter, "
        "which gives you the earlier deadline of the two."
    ),
    "expedited_internal_and_external_may_run_together": (
        "Because this is urgent, you can ask for the outside review at the same time "
        "as the insurer's own review instead of waiting for them to finish."
    ),
    "expedited_track_from_your_own_urgency_statement": (
        "This timeline rests on your statement that delay would harm your health. Have "
        "your doctor put that in writing — a reviewer will look for it."
    ),
}


def symbol_to_text(symbol: clingo.Symbol) -> str:
    """Render a clingo symbol the way the trace view shows it."""
    if symbol.type is clingo.SymbolType.Function and not symbol.name:
        # An unnamed function is a tuple, which is how premises are carried.
        return ", ".join(symbol_to_text(a) for a in symbol.arguments)
    return str(symbol)


def build_trace(
    because_atoms: list[clingo.Symbol],
    citations: dict[str, Citation],
) -> list[TraceNode]:
    """Turn every ``because/3`` atom into a :class:`TraceNode`.

    Sorted by rule id so the trace reads the same way twice — a trace whose order
    wobbles between runs is not a record anyone can check.
    """
    nodes: list[TraceNode] = []
    for atom in because_atoms:
        conclusion, rule_id_symbol, premises = atom.arguments
        rule_id = rule_id_symbol.string
        premise_list = (
            [symbol_to_text(p) for p in premises.arguments]
            if premises.type is clingo.SymbolType.Function and not premises.name
            else [symbol_to_text(premises)]
        )
        nodes.append(
            TraceNode(
                conclusion=symbol_to_text(conclusion),
                rule_id=rule_id,
                premises=[p for p in premise_list if p],
                citation=citations.get(rule_id),
                explanation=EXPLANATIONS.get(rule_id),
            )
        )
    return sorted(nodes, key=lambda n: (n.rule_id, n.conclusion))


def warning_text(code: str) -> str:
    """Plain-language text for a warning code, or the code itself if unknown."""
    return WARNINGS.get(code, code)
