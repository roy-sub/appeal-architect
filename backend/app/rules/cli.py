"""Command-line rules engine. No web, no database, no LLM.

    python -m app.rules.cli --plan aca_marketplace --state CA \
        --denial-date 2026-09-14 --timing post --reason not_medically_necessary

Exists so the engine can be exercised and audited on its own, which is the point
of keeping it pure: anyone can check a route determination without running the
app, and the answer they get is the answer a user would get.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from app.domain.case import CaseFacts, DenialReason, PlanType, ServiceTiming
from app.rules.runner import determine_route


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.rules.cli",
        description="Work out an appeal route from confirmed facts. Pure engine, no network.",
    )
    parser.add_argument("--plan", required=True, choices=[p.value for p in PlanType])
    parser.add_argument("--state", required=True, help="Two-letter state code")
    parser.add_argument("--denial-date", required=True, help="YYYY-MM-DD, as printed on the letter")
    parser.add_argument("--received-date", help="YYYY-MM-DD, when it reached the member")
    parser.add_argument("--service-date", help="YYYY-MM-DD")
    parser.add_argument("--final-adverse-date", help="YYYY-MM-DD, the final internal denial")
    parser.add_argument("--timing", required=True, choices=[t.value for t in ServiceTiming])
    parser.add_argument(
        "--reason",
        action="append",
        required=True,
        choices=[r.value for r in DenialReason],
        help="Repeat for more than one stated reason",
    )
    parser.add_argument(
        "--filer", default="member", choices=["member", "authorized_rep", "provider"]
    )
    parser.add_argument("--urgent", action="store_true", help="Member declares medical urgency")
    parser.add_argument("--insurer", default="(not given)")
    parser.add_argument("--json", action="store_true", help="Emit the full determination as JSON")
    parser.add_argument(
        "--trace", action="store_true", help="Print the justification for every conclusion"
    )
    return parser


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    facts = CaseFacts(
        plan_type=PlanType(args.plan),
        state=args.state,
        insurer_name=args.insurer,
        member_id_present=True,
        denial_date=date.fromisoformat(args.denial_date),
        denial_received_date=_date(args.received_date),
        service_date=_date(args.service_date),
        service_timing=ServiceTiming(args.timing),
        denial_reasons=[DenialReason(r) for r in args.reason],
        is_urgent_medical=args.urgent,
        filer=args.filer,
    )

    route = determine_route(facts, final_adverse_date=_date(args.final_adverse_date))

    if args.json:
        print(route.model_dump_json(indent=2))
        return 0

    print(
        f"Rulebase {route.rulebase_version}   plan: {route.plan_type.value}   state: {facts.state}"
    )
    print(f"Facts hash {route.facts_hash[:16]}")
    print()

    if route.warnings:
        print("READ THIS FIRST")
        for warning in route.warnings:
            print(f"  * {warning}")
        print()

    if not route.steps:
        print("No route. See the warnings above -- we do not guess a track.")
        return 0

    print("YOUR ROUTE")
    for step in route.steps:
        print(f"  {step.order}. {step.label}   ({step.who_files})")
        print(f"     Decided by: {step.review_body}")
        if step.deadline is not None:
            due = step.deadline.due_date
            print(f"     Due: {due:%-d %B %Y}   ({step.deadline.trigger_description})")
            print(f"     Rule: {step.deadline.rule_id}   {step.deadline.citation.label()}")
            if step.deadline.ambiguous and step.deadline.ambiguity_note:
                print(f"     NOTE: {step.deadline.ambiguity_note}")
        else:
            print(f"     No date yet. Starts after step {step.starts_after}.")
            print(f"     {step.pending_reason}")
        if step.required_elements:
            print("     This filing must include:")
            for element in step.required_elements:
                mark = " " if element.mandatory else "?"
                print(f"       [{mark}] {element.label}   ({element.citation.label()})")
        print()

    print("ALL DEADLINES")
    for deadline in route.deadlines:
        flag = "  (ambiguous)" if deadline.ambiguous else ""
        print(f"  {deadline.due_date}  {deadline.label}{flag}")
    print()

    if args.trace:
        print("WHY — every conclusion and the rule behind it")
        for node in route.trace:
            print(f"  {node.rule_id}")
            print(f"    concludes: {node.conclusion}")
            if node.premises:
                print(f"    from:      {', '.join(node.premises)}")
            if node.citation:
                print(
                    f"    cites:     {node.citation.label()}"
                    f"{'' if node.citation.verified else '  [UNVERIFIED]'}"
                )
            if node.explanation:
                print(f"    plainly:   {node.explanation}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
