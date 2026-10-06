# Argument schemes

A scheme is a template that turns confirmed facts into an argument: a claim, its
premises, the evidence each premise needs, what it attacks, and the rebuttals the
insurer is known to raise against it.

Versioned as `schemes_version`, recorded on every argument graph.

## Two rules for anyone adding a scheme

1. **Known rebuttals become real arguments.** Each entry in `known_rebuttals` is
   instantiated as a counter-attacking argument in the framework, so the solver
   computes defeat. The application never asserts that an argument is defeated —
   that is the difference between a computed result and a hard-coded claim
   dressed up as one.

2. **Missing evidence does not delete an argument.** It marks the premise
   unsatisfied, and the UI shows the argument as "needs this to hold". A user is
   better served by seeing what would make an argument stand than by it silently
   vanishing.

## A standing caution

A scheme encodes the *shape* of a legal argument, not a legal standard. Where a
`claim_template` asserts what a regulation or a plan document requires, that
assertion needs the same treatment as a deadline: a transcribed source, a
citation, and a `verified` flag. `strength: strong` is a claim about how the
argument fares against its own known rebuttals, not a prediction about any
case.

## Fields

| Field | Meaning |
|---|---|
| `id` | Stable identifier. Appears in letters as a paragraph's `argument_node_id`. |
| `denial_reason` | The `DenialReason` this scheme answers. |
| `side` | `patient` for a counter-argument; the insurer's own reason is generated, not written here. |
| `claim_template` | The assertion, with `{service}`, `{insurer}`, `{condition}`, `{state}` placeholders. |
| `premises` | Each with `id`, `text`, and the `evidence` key that establishes it. |
| `attacks` | What this argument attacks, and how: `rebut`, `undermine` or `undercut`. |
| `known_rebuttals` | What the insurer says back. Each becomes a counter-attacking argument. `defeated_by_evidence` names what knocks the rebuttal down. |
| `strength` | `strong` or `conditional`. Advisory only — the solver decides acceptability. |
| `requires_facts` | Facts that must be confirmed before the scheme instantiates at all. |
