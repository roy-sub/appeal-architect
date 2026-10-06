# Appeal Architect

A consumer web app that turns a health-insurance denial into a formally
structured, evidence-backed appeal.

## Read these first

- **`PLAN.md`** — the build plan, the decisions taken, the conflicts flagged, and
  which phase is current.
- **`docs/ARCHITECTURE.md`** — the invariant below, and how it is enforced.
- **`frontend/CLAUDE.md`** — frontend conventions and the hard product rules.
  Read it before any frontend change.
- **`backend/README.md`** — backend layout and the two rules for working there.

## Two authorities, and they are different ones

| | Wins on |
|---|---|
| `Appeal Build Spec.md` (attached to the build session) | architecture, data, API, correctness |
| `design/` (read-only) | appearance, copy, spacing, motion |

Where they conflict, flag it rather than resolving it quietly. `PLAN.md` §3
records the conflicts found so far and which authority won each.

## The invariant

**The LLM never decides anything.** The appeal route, the review levels, the
deadlines, the required elements and which arguments are acceptable are computed
by the clingo rules engine and the argumentation solver. The model reads
documents and writes prose.

Four consequences for anyone working here:

1. **`app/rules/**` and `app/argumentation/**` stay pure.** No network, no LLM,
   no database — not directly, and not through anything they import.
   `backend/tests/test_boundary.py` walks the transitive import closure and fails
   the build otherwise. Widening its allow-list is an architectural decision, so
   read `docs/ARCHITECTURE.md` before you do.
2. **Nothing unconfirmed reaches the engine.** LLM output is an `ExtractedFact`
   with a `status`, shown to the user beside the source span it came from. There
   is no code path from `pending` to a conclusion, and
   `ExtractedFact.effective_value()` raises rather than returning `None`.
3. **Deadlines are a safety feature.** The arithmetic lives in the rules engine,
   carries a citation, is unit-tested against worked examples, and is always
   displayed with the rule it came from. Where the regulation is ambiguous the
   engine takes the earlier, more conservative date and says so — both the
   Pydantic model and a database constraint refuse an ambiguous deadline with no
   explanation.
4. **Never write a legal value you have not read in its source.** Keep the seed,
   leave `verified=false`, and add the file to
   `backend/app/rules/rulebase/CHANGELOG.md`. An invented deadline shown with a
   citation beside it can cost someone their appeal rights.

## Repo shape

```
backend/      Python 3.12, FastAPI, clingo, Pydantic v2
frontend/     Next.js 15 static export, Tailwind v4, Motion
design/       READ-ONLY. The original Claude Design export: prototype, tokens,
              component and motion specs, the design chat where the decisions live
docs/         ARCHITECTURE · RULEBASE · SCHEMES · PRIVACY · DEPLOY
PLAN.md       The build plan and the open decisions
.env.example  Every environment variable, both halves
```

Nothing else belongs at the root — the build spec fixes that list, which is why
there is no root `Makefile` or `docker-compose.yml` and "one command per side"
means a command inside each side.

## Working agreement

Build in the build spec's phases. At the end of each one: stop, run the
Definition of Done, show the result, wait for a go-ahead. Do not run ahead, and
do not stub something and call it done.

## Health data

Encryption at rest and in transit, no PHI in logs, no PHI in LLM call metadata,
a hard delete that actually deletes, no training on user data. The data flow is
documented in `docs/PRIVACY.md`, and that document says plainly which parts are
implemented and which are not yet.
