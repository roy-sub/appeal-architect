"""Framework + extensions → the structure the user reads.

PURE: no network, no LLM, no database.

Produces the three tiers the design names — Solid ground, Worth adding, Left out
— plus, for each argument, the evidence it still needs, what the insurer would
likely say back, and whether that answer defeats it.

The verdict is always a sentence, never an icon. "Does not defeat it" is a
statement someone can act on; a green tick is not.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.argumentation.builder import BuiltGraph
from app.argumentation.solver import Extensions, Framework, solve_framework
from app.domain.argument import (
    TIER_LEFT_OUT,
    TIER_SOLID_GROUND,
    TIER_WORTH_ADDING,
    Argument,
    ArgumentGraph,
)
from app.domain.trace import TraceNode

#: Fixed copy for each tier, from the design. These exact sentences.
TIER_EXPLANATIONS: dict[str, str] = {
    TIER_SOLID_GROUND: (
        "These stand up to whatever the insurer answers. Your letter leads with them."
    ),
    TIER_WORTH_ADDING: (
        "The insurer has a fair answer to each of these. Useful as extra weight, "
        "not as your main point."
    ),
    TIER_LEFT_OUT: (
        "We checked this one and it does not hold. It stays visible so you know it was considered."
    ),
}

#: The verdict sentence for each tier.
VERDICTS: dict[str, str] = {
    TIER_SOLID_GROUND: "Does not defeat it",
    TIER_WORTH_ADDING: "They can knock this one back",
    TIER_LEFT_OUT: "Left out",
}


def _is_internal(argument_id: str) -> bool:
    """Scaffolding arguments: the rebuttals and the evidence that answers them.

    They are real nodes in the framework -- the solver needs them to compute
    defeat -- but the user sees them as "what they would say back" on the
    argument they attack, not as separate cards. Showing them as peers would
    turn a six-node graph into a twenty-node one for no gain in understanding.
    """
    return ".rebuttal." in argument_id or argument_id.endswith(".answered")


def build_graph(
    built: BuiltGraph,
    *,
    case_id: object = None,
) -> ArgumentGraph:
    """Solve the framework and assemble the user-facing graph."""
    framework = Framework.of(
        [a.id for a in built.arguments],
        [(a.source_id, a.target_id) for a in built.attacks],
    )
    extensions = solve_framework(framework)

    all_ids = framework.arguments
    grounded = extensions.grounded
    worth_adding = extensions.worth_adding
    defeated = extensions.defeated(all_ids)

    # Only the user's own arguments are tiered. The insurer's stated reason is
    # the thing being attacked, and the scaffolding nodes belong to the argument
    # they attach to.
    def visible(argument: Argument) -> bool:
        return argument.side == "patient" and not _is_internal(argument.id)

    trace = _build_trace(built, extensions)

    return ArgumentGraph(
        schemes_version=built.schemes_version,
        arguments=built.arguments,
        attacks=built.attacks,
        grounded_extension=sorted(a.id for a in built.arguments if visible(a) and a.id in grounded),
        preferred_extensions=[sorted(extension) for extension in extensions.preferred],
        stable_extensions=[sorted(extension) for extension in extensions.stable],
        worth_adding=sorted(a.id for a in built.arguments if visible(a) and a.id in worth_adding),
        defeated=sorted(a.id for a in built.arguments if visible(a) and a.id in defeated),
        trace=trace,
        computed_at=datetime.now(tz=UTC),
    )


def _build_trace(built: BuiltGraph, extensions: Extensions) -> list[TraceNode]:
    """One trace node per tiered argument, naming the semantics that decided it.

    The trace says *why the solver put this argument where it did*, which is the
    only honest explanation available: the tier is a computed property of the
    whole framework, not a label attached to one argument.
    """
    all_ids = frozenset(a.id for a in built.arguments)
    grounded = extensions.grounded
    worth_adding = extensions.worth_adding
    defeated = extensions.defeated(all_ids)

    nodes: list[TraceNode] = []
    for argument in built.arguments:
        if argument.side != "patient" or _is_internal(argument.id):
            continue

        attackers = [a.source_id for a in built.attacks if a.target_id == argument.id]

        if argument.id in grounded:
            tier, rule = TIER_SOLID_GROUND, "af.grounded"
            explanation = (
                "In the grounded extension: every attack on it is itself defeated by "
                "something you have, so it holds on any reading."
            )
        elif argument.id in worth_adding:
            tier, rule = TIER_WORTH_ADDING, "af.preferred_not_grounded"
            explanation = (
                "In some preferred extension but not the grounded one: it holds on "
                "some readings and not others, because the insurer has an answer you "
                "have not yet closed off."
            )
        elif argument.id in defeated:
            tier, rule = TIER_LEFT_OUT, "af.defeated"
            explanation = (
                "In no preferred extension: there is no reading of this framework on "
                "which it survives."
            )
        else:  # pragma: no cover -- the three tiers are exhaustive
            continue

        nodes.append(
            TraceNode(
                conclusion=f"{tier}: {argument.id}",
                rule_id=rule,
                premises=sorted(attackers),
                citation=argument.citations[0] if argument.citations else None,
                explanation=explanation,
            )
        )

    return sorted(nodes, key=lambda n: (n.rule_id, n.conclusion))


# ---------------------------------------------------------------------------
# Per-argument detail for the UI
# ---------------------------------------------------------------------------


def argument_detail(
    graph: ArgumentGraph, argument_id: str, *, evidence_on_file: set[str] | None = None
) -> dict[str, object]:
    """Everything the argument detail panel shows for one node.

    Includes what the insurer would likely say back and whether it defeats the
    argument -- which is exactly the pair of facts a person needs to decide
    whether to lead with it.
    """
    on_file = evidence_on_file or set()
    argument = graph.by_id(argument_id)
    if argument is None:
        raise KeyError(argument_id)

    tier = graph.tier_of(argument_id)

    # The rebuttals attacking this argument, and whether each is answered.
    replies: list[dict[str, object]] = []
    for attack in graph.attacks:
        if attack.target_id != argument_id:
            continue
        rebuttal = graph.by_id(attack.source_id)
        if rebuttal is None or ".rebuttal." not in attack.source_id:
            continue
        answered = any(
            a.target_id == attack.source_id and a.source_id.endswith(".answered")
            for a in graph.attacks
        )
        replies.append(
            {
                "id": attack.source_id,
                "text": rebuttal.claim,
                "kind": attack.kind,
                "answered": answered,
                "verdict": (
                    "Does not defeat it"
                    if answered
                    else "They can knock this one back until you close it off"
                ),
            }
        )

    missing = [key for key in argument.required_evidence if key not in on_file]

    return {
        "id": argument.id,
        "tier": tier,
        "tier_explanation": TIER_EXPLANATIONS.get(tier or "", ""),
        "claim": argument.claim,
        "strength": argument.strength,
        "premises": [p.model_dump() for p in argument.premises],
        "required_evidence": argument.required_evidence,
        "missing_evidence": missing,
        "holds_now": not missing and tier == TIER_SOLID_GROUND,
        "verdict": VERDICTS.get(tier or "", ""),
        "insurer_replies": replies,
        "citations": [c.model_dump() for c in argument.citations],
    }


def evidence_checklist(
    graph: ArgumentGraph, *, evidence_on_file: set[str] | None = None
) -> list[dict[str, object]]:
    """The evidence checklist, derived from the accepted arguments.

    Deduped across arguments, and each item links back to the argument nodes that
    need it -- so "why am I being asked for this?" always has an answer on screen.

    Ordered by how much it would change: an item that would move an argument from
    Worth adding to Solid ground is worth more than one that merely supports an
    argument already holding.
    """
    on_file = evidence_on_file or set()
    accepted = set(graph.grounded_extension) | set(graph.worth_adding)

    needed: dict[str, set[str]] = {}
    for argument in graph.arguments:
        if argument.id not in accepted:
            continue
        for key in argument.required_evidence:
            needed.setdefault(key, set()).add(argument.id)

    # An evidence key that answers a rebuttal unlocks a tier change.
    unlocking: set[str] = set()
    for argument in graph.arguments:
        if argument.id.endswith(".answered"):
            unlocking.update(argument.required_evidence)
    for attack in graph.attacks:
        if ".rebuttal." in attack.source_id and attack.target_id in graph.worth_adding:
            rebuttal = graph.by_id(attack.source_id)
            if rebuttal is not None:
                unlocking.update(rebuttal.required_evidence)

    items: list[dict[str, object]] = [
        {
            "key": key,
            "label": key.replace("_", " ").capitalize(),
            "supports": sorted(argument_ids),
            "status": "have" if key in on_file else "missing",
            "unlocks_a_tier_change": key in unlocking,
        }
        for key, argument_ids in needed.items()
    ]

    def rank(item: dict[str, object]) -> tuple[bool, bool, int, str]:
        supports = item["supports"]
        return (
            item["status"] == "have",
            not item["unlocks_a_tier_change"],
            -len(supports) if isinstance(supports, list) else 0,
            str(item["key"]),
        )

    return sorted(items, key=rank)
