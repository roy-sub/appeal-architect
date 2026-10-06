# Argument schemes

> **Phase 3 deliverable.** This file is a stub. The scheme library does not exist
> yet.

## What a scheme is

A template that turns confirmed facts into an argument: a claim, its premises,
the evidence each premise needs, what it attacks, and the rebuttals the insurer
is known to raise against it.

`backend/app/argumentation/schemes/*.yaml`, versioned as `schemes_version`, which
is recorded on every argument graph.

## Planned coverage

Three to five schemes for each of the five MVP denial reasons:

- `not_medically_necessary`
- `prior_auth_missing`
- `out_of_network`
- `experimental_investigational`
- `coding_error`

## Two rules for scheme authors

1. **Known rebuttals become real arguments.** A scheme's `known_rebuttals`
   are instantiated as counter-attacking arguments in the framework, so the
   solver computes defeat. The application never asserts that an argument is
   defeated — that is the difference between a computed result and a hard-coded
   claim dressed up as one.
2. **Missing evidence does not delete an argument.** It marks
   `required_evidence` unsatisfied, and the UI shows the argument as "needs this
   to hold". A user is better served by seeing what would make an argument stand
   than by it silently vanishing.

## A standing caution

A scheme encodes the *shape* of a legal argument, not a legal standard. Where a
scheme's claim template asserts what a regulation or a plan document requires,
that assertion needs the same treatment as a deadline: a transcribed source, a
citation, and a `verified` flag. Any scheme making such an assertion is flagged
for review rather than shipped as settled.
