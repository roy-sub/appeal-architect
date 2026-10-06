# Architecture

## The invariant

**The LLM never computes a route, a deadline, or whether an argument holds.**

A symbolic rules engine determines the legally applicable appeal track, the
review levels, the deadlines and the required elements. A computational
argumentation engine computes which counter-arguments are acceptable. An LLM
reads documents and writes prose, and does nothing else.

This is the product, not an implementation preference. A model that guesses a
filing deadline can cost someone their appeal rights permanently, and it will
guess fluently and with apparent confidence. So the separation is enforced by
the code and by a test, not by a convention anyone has to remember.

## How it is enforced

### 1. Import isolation

`app/rules/**` and `app/argumentation/**` may import only:

- the standard library
- `clingo`, `clorm` — the ASP solver and its ORM
- `pydantic` — the domain models
- `dateutil`, `holidays` — date arithmetic
- `yaml` — the scheme library is YAML files on disk (`safe_load` only)
- `app/domain/**` — the shared vocabulary

Every entry is a pure computation or data-parsing library: no network client, no
database driver, no model SDK, and nothing that could acquire one as a
dependency. The list is itself pinned by a test, so widening it shows up as a
deliberate change in a diff rather than slipping in alongside a feature.

They may not import `anthropic`, `httpx`, `requests`, `supabase`,
`app/services/llm.py` or `app/db/**`. Not directly, and not through anything
else they import.

### 2. A test that fails when it is violated

`backend/tests/test_boundary.py` walks the AST of every file under those two
packages, resolves the **transitive** in-package import closure, and fails on any
forbidden module anywhere in it. The transitive part matters: `app.domain` is on
the allow-list, so a direct-import check would let anything `app.domain` imports
through the boundary unchecked. `app.domain` is therefore checked for purity too.

The same test asserts that `app/services/llm.py` — the only module permitted to
import the Anthropic SDK — imports neither engine runner and never names
`route_determinations` or `argument_graphs`.

It carries two **negative controls**: one writes a module with a direct forbidden
import, one with a forbidden import reached through a permitted internal module,
and both assert the walker catches it. A boundary test that cannot fail is not a
boundary test, and a refactor that accidentally neuters the AST walk is caught
here rather than in production.

### 3. The confirmation gate

LLM output enters the system as `ExtractedFact` and nothing else:

```
field, value, confidence, source_document_id, source_span, status
status: pending | confirmed | edited | rejected
```

The route service reads a fact's value only when its status is `confirmed` or
`edited`. `ExtractedFact.effective_value()` **raises** rather than returning
`None` for anything else — a silent `None` becomes a missing premise, and a
missing premise becomes a wrong route. Confirmation is an explicit user action
through the API. There is no code path from `pending` to a conclusion.

The database enforces the same thing: a `confirmed` row without a
`confirmed_at`, or an `edited` row without an `edited_value`, violates a check
constraint.

### 4. Letter generation is constrained too

The letter LLM receives only the accepted argument nodes, their premises, their
citations, and the user's confirmed facts. Its system prompt forbids introducing
any factual claim not present in that input.

After generation, every paragraph must carry either an `argument_node_id` or the
reserved `procedural` tag. `procedural` paragraphs — the appeal-rights header,
the deadline reference, the claim identifiers — are rendered from a fixed
template, never from model prose; the design specifies that badge, and the
letter's legally necessary header comes from no argument. LLM-generated text
carrying neither tag is dropped.

## Shape

```
                        ┌──────────────────────────────┐
   denial letter ─────▶ │  services/ingestion          │
                        │  OCR: text layer, then OCR   │
                        └──────────────┬───────────────┘
                                       │ per-page text + real char offsets
                                       ▼
                        ┌──────────────────────────────┐
                        │  services/llm   ◀── the ONLY │
                        │  module importing anthropic  │
                        └──────────────┬───────────────┘
                                       │ ExtractedFact[] — all `pending`
                                       ▼
                        ┌──────────────────────────────┐
                        │  THE USER CONFIRMATION GATE  │
                        │  each proposal shown beside  │
                        │  the source span it came from│
                        └──────────────┬───────────────┘
                                       │ confirmed / edited facts only
                   ┌───────────────────┴───────────────────┐
                   ▼                                       ▼
    ┌──────────────────────────┐            ┌──────────────────────────┐
    │  rules/        PURE      │            │  argumentation/   PURE   │
    │  clingo + rulebase/*.lp  │            │  schemes + semantics.lp  │
    │  route, levels,          │            │  grounded / preferred /  │
    │  deadlines, required     │            │  stable extensions       │
    │  elements, because/3     │            │                          │
    └────────────┬─────────────┘            └────────────┬─────────────┘
                 │ RouteDetermination                    │ ArgumentGraph
                 │ + trace + citations                   │ + trace
                 └───────────────────┬───────────────────┘
                                     ▼
                        ┌──────────────────────────────┐
                        │  services/letters            │
                        │  accepted nodes ──▶ llm ──▶  │
                        │  paragraphs, each tagged     │
                        └──────────────────────────────┘

    No arrow runs from services/llm into rules/ or argumentation/.
    That absence is the architecture.
```

## The rules engine

Answer Set Programming, via `clingo`. Facts are derived from confirmed
`CaseFacts`; the rulebase is a set of `.lp` files layered federal-default then
state-override.

**Every derived atom carries its justification.** The rulebase emits
`because(Conclusion, RuleId, Premises)` for each conclusion, and an integrity
constraint makes a model without full justification unsatisfiable — a conclusion
the engine cannot justify is not a conclusion it can reach.

The federal-default / state-override pattern, written defeasibly:

```prolog
deadline(internal_appeal, Days, calendar, "federal") :-
    federal_default(internal_appeal, Days), not state_override(internal_appeal, _).
deadline(internal_appeal, Days, calendar, State) :-
    state_override(internal_appeal, Days), state(State).
```

With no override row present, the federal baseline governs. That is why the
empty state tables are correct rather than incomplete.

**Determinism.** The route path runs with `--models=1` in production. Tests run
with `--models=2` and fail if a second answer set exists: more than one answer
set on the route path is a rulebase bug, not a choice.

### Deadline arithmetic

`app/rules/deadlines.py` holds pure date functions. The ASP layer produces
`(item, count, unit, trigger)`; Python resolves it to a date.

- Calendar days versus business days is **explicit per item**, never inferred.
- `months` and `hours` are real units, because the regulations use them: 45 CFR
  147.136(d) says "4 months", which is not 120 days, and (b)(2)(ii)(B) says "72
  hours", which is not 3 calendar days.
- Business-day arithmetic uses the US federal holidays.
- Where the regulation's trigger is ambiguous — date of denial versus date of
  receipt — the engine computes the **earlier, more conservative** date, sets
  `ambiguous=True`, and returns an `ambiguity_note` the UI must display. Both
  the Pydantic model and a database check constraint refuse an ambiguous
  deadline with no note: a conservative date presented as certain is still a
  misrepresentation.

`tests/test_deadlines.py` is the file you never let go red.

#### A note on the holiday library

The build spec names `workalendar`. It cannot be installed: its transitive
dependency `pymeeus` fails to build on Python 3.13. We use `holidays` instead,
behind a one-function adapter (`app/rules/calendar.py`) so the source stays
swappable, and the adapter is unit-tested against a table of federal holidays
transcribed from 5 U.S.C. § 6103 — so the deadline tests do not depend on any
library being correct.

## The argumentation engine

Abstract argumentation frameworks (Dung 1995): a set of arguments and a binary
attack relation, with a structured layer producing those arguments from schemes
and confirmed facts.

Semantics are computed by ASP encodings in
`app/argumentation/semantics.lp`:

- **grounded** — unique, sceptical. This is **"Solid ground"**.
- **preferred** — credulous. An argument in some preferred extension but not in
  grounded is **"Worth adding"**.
- **stable** — implemented because it is cheap and useful for testing.

Known rebuttals from the scheme library become counter-attacking arguments in the
framework, so the solver genuinely computes defeat rather than the application
asserting it. An argument is in "Solid ground" because the solver put it there,
which is what makes that label a claim we can stand behind.

An argument whose required evidence is missing is **not removed** — it stays in
the graph marked unsatisfied, and the UI shows it as "needs this to hold", so the
user can see what would make it stand.

### References

- Dung, P. M. (1995). *On the acceptability of arguments and its fundamental
  role in nonmonotonic reasoning, logic programming and n-person games.*
  Artificial Intelligence 77(2), 321–357.
- Egly, U., Gaggl, S. A., Woltran, S. (2010). *Answer-set programming encodings
  for argumentation frameworks.* Argument & Computation 1(2), 147–177.
- Modgil, S., Prakken, H. (2014). *The ASPIC+ framework for structured
  argumentation: a tutorial.* Argument & Computation 5(1), 31–62.

## Versioning and reproducibility

Every `RouteDetermination` stores the `rulebase_version` that produced it, every
`ArgumentGraph` its `schemes_version`, and every conclusion its trace and
citation. Any conclusion the product has ever shown a user can be reproduced
against the exact rules in force when it was computed. The route path is
idempotent per `(case_id, facts_hash, rulebase_version)`.

## Unverified values

A legal value we have not checked against its source is marked `verified=false`
in `app/rules/rulebase/tables/*.csv`, surfaced in
`RouteDetermination.warnings` with an `UNVERIFIED` prefix, and shown as a banner
in the UI.

It is never silently treated as correct, and it is never hidden. Telling someone
"we have not checked this against the regulation" is a worse product and a better
one than showing them a confident wrong date.

The three state override tables ship **empty on purpose**. See
`backend/app/rules/rulebase/CHANGELOG.md`.
