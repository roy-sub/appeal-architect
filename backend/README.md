# Appeal Architect — backend

FastAPI. A symbolic rules engine (clingo) determines the appeal route, the review
levels, the deadlines and the required elements. An argumentation solver computes
which counter-arguments are acceptable. A language model reads documents and
writes prose, and does nothing else.

That last sentence is enforced by the code rather than by convention — see
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) and `tests/test_boundary.py`.

---

## Contents

1. [Run it](#run-it)
2. [Test it](#test-it)
3. [Layout](#layout)
4. [The two rules for working here](#the-two-rules-for-working-here)
5. [The rules engine](#the-rules-engine)
6. [The argumentation engine](#the-argumentation-engine)
7. [The service layer](#the-service-layer)
8. [API surface](#api-surface)
9. [Errors](#errors)
10. [Database and migrations](#database-and-migrations)
11. [Configuration](#configuration)
12. [The test suite](#the-test-suite)
13. [Deployment](#deployment)
14. [Known limits](#known-limits)

---

## Run it

Python 3.12 or later. No container runtime.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env        # then fill in the backend block
uvicorn app.main:app --reload  # interactive docs at http://localhost:8000/docs
```

It starts with nothing configured. `GET /healthz` reports which services are
wired, and an endpoint whose service is missing returns a 503 naming the
environment variables to set — not a stack trace.

The route engine also runs on its own, with no web stack, no database and no
model:

```bash
python -m app.rules.cli --plan aca_marketplace --state CA \
    --denial-date 2026-09-14 --timing post \
    --reason not_medically_necessary --trace

python -m app.rules.cli --help     # every flag
python -m app.rules.cli ... --json # the full determination, including the trace
```

This exists because the engine is pure: anyone can audit a route determination
without running the application, and the answer they get is the answer a user
would get.

## Test it

```bash
pytest                                    # 441 tests, no database needed
ruff check . && ruff format --check .
mypy app                                  # clean, strict

# Migration and RLS tests need a throwaway Postgres.
# DESTRUCTIVE: the test drops and recreates the public, auth and storage schemas.
createdb aa_test
TEST_DATABASE_URL=postgresql://localhost/aa_test pytest tests/test_migration_rls.py
```

`tests/test_boundary.py` is the one you never let go red: it walks the import
closure of `app/rules/**` and `app/argumentation/**` and fails if either can
reach the Anthropic SDK, the network, or the database.

## Layout

```
app/
  main.py            app factory, CORS, problem+json handlers, lifespan checks
  config.py          settings; per-service "is this configured" gates
  deps.py            JWT verification -> CurrentUser; the job-secret guard
  problem.py         RFC 7807 problem+json with a machine-readable code
  site.py            fixed strings, including the disclaimer

  domain/            the shared vocabulary (PURE)
    case.py            PlanType, DenialReason, CaseFacts, ExtractedFact
    route.py           DeadlineItem, RouteStep, RouteDetermination
    argument.py        Argument, Attack, ArgumentGraph
    trace.py           Citation, TraceNode

  rules/             the rules engine (PURE — no network, no LLM, no DB)
    runner.py          clingo driver; refuses a non-unique or unjustified model
    facts.py           CaseFacts -> logic-program facts
    deadlines.py       count + unit + trigger -> a date
    calendar.py        US federal holidays, behind an adapter
    trace.py           because/3 atoms -> a readable trace
    generate.py        CSV -> .lp, refusing malformed rows
    cli.py             the standalone engine
    rulebase/
      *.lp               the rules, in load order
      VERSION            pinned onto every determination
      CHANGELOG.md       what changed, and which files await a source
      tables/*.csv       transcribed legal values, each verified=true|false

  argumentation/     the argumentation engine (PURE)
    builder.py         schemes + facts -> arguments and attacks
    solver.py          clingo driver for the semantics
    semantics.lp       grounded, preferred, stable
    explain.py         why an argument held, or did not
    schemes/*.yaml     the versioned scheme library

  services/          orchestration. May import the engine; the engine never
                     imports services
  api/v1/            the versioned HTTP surface. Transport only
  jobs/              what the daily cron runs
  db/
    client.py          Supabase service-role client
    repo.py            ownership-scoped row access
    migrations/        numbered, forward-only SQL

tests/
  test_boundary.py       the neurosymbolic boundary, with negative controls
  test_migration_rls.py  migrations + RLS isolation against real Postgres
  golden/                route and deadline worked examples
  af/                    argumentation fixtures with known extensions
```

## The two rules for working here

**1. The engine stays pure.** If you need a new import under `app/rules/**` or
`app/argumentation/**`, read `../docs/ARCHITECTURE.md` first. The allow-list in
`tests/test_boundary.py` is the boundary, and widening it is an architectural
decision, not a convenience.

**2. Never write a legal value you have not read in its source.** Keep the seed,
leave `verified=false`, and add the file to
`app/rules/rulebase/CHANGELOG.md`. An invented deadline shown with a citation
beside it can cost someone their appeal rights.

## The rules engine

### How a determination is computed

```
CaseFacts (confirmed only)
    -> facts.py          emits plan_type/1, state/1, denial_date/3, …
    -> runner.py         loads *.lp in name order, solves with clingo
    -> one answer set    more than one is a defect, and raises
    -> deadlines.py      count + unit + trigger -> real dates
    -> trace.py          because/3 atoms -> TraceNode tree
    -> RouteDetermination
```

`runner.py` enforces two invariants and raises rather than degrading:

- `RulebaseNondeterministic` — more than one answer set means the rulebase is
  under-constrained. The first model is not silently accepted.
- `RulebaseUnsatisfiable` — an integrity constraint in `00_core.lp` makes any
  model containing an unjustified conclusion unsatisfiable, so a conclusion
  without a trace is not a degraded result, it is a failed solve.

### The rulebase files, in load order

| File | What it decides |
|---|---|
| `00_core.lp` | Justification rules and the integrity constraints |
| `10_plan_type.lp` | Which plan types the rulebase will route at all |
| `20_track.lp` | Review levels, order, who files, who decides |
| `30_deadlines.lp` | Which deadlines apply, with count, unit and trigger |
| `40_required.lp` | Required elements per level |
| `50_expedited.lp` | Urgent-track conditions |
| `90_state_*.lp` | Per-state default-override modules |

### Tables, not hand-written facts

Nothing in `*.lp` carries a number read off a regulation. Every legal value lives
in `rulebase/tables/*.csv` with its source, locator, verification flag and
effective date, and `generate.py` compiles those into facts. A malformed row is
refused rather than skipped.

To change a legal value: edit the CSV, set `verified=true` only if you have read
it in the source, note it in `CHANGELOG.md`, bump `VERSION` if the meaning
changed, and re-run the golden cases.

### Deadlines are safety-critical

The ASP layer never computes a date. It emits a count, a unit
(`calendar | business | months | hours`) and a trigger; `deadlines.py` resolves
that to a date against `calendar.py`. Business-day counting skips weekends and US
federal holidays, tested against 5 U.S.C. § 6103.

Where the regulation leaves the trigger genuinely ambiguous — the date printed on
the letter versus the date it was received — the engine takes the **earlier, more
conservative** date, sets `ambiguous=True` and attaches an explanation. Both the
Pydantic model and a database constraint refuse an ambiguous deadline that has no
note, so it cannot reach a user without the caveat.

When a trigger date is not yet known (an external-review deadline before the
internal appeal has been answered), `TriggerUnavailable` is raised and the step
is returned with `deadline=None` and a `pending_reason`. It is never given a
placeholder date.

## The argumentation engine

### Pipeline

```
CaseFacts + DenialReason
    -> builder.py     selects schemes, instantiates arguments and attacks
    -> solver.py      clingo over semantics.lp
    -> grounded       "solid ground"   — holds under every reading
       preferred      "worth adding"   — holds under some reading
    -> ArgumentGraph
```

Known insurer rebuttals are not annotations. Each becomes an argument in
**mutual** attack with the scheme it answers, so the solver computes defeat
rather than being told the outcome.

### The semantics encoding

`semantics.lp` computes the grounded extension as monotone positive recursion
with no negation:

```prolog
attacker_total(X, N)      :- arg(X), N = #count{ Y : attacks(Y, X) }.
defeated_attackers(X, N)  :- arg(X), N = #count{ Y : attacks(Y, X), defeated(Y) }.
defeated(X)               :- in(Y), attacks(Y, X).
defends(X)                :- attacker_total(X, N), defeated_attackers(X, N).
in(X)                     :- arg(X), defends(X), semantics = grounded.
```

An earlier version used negation-as-failure through the attack cycle, which is
unstratified and returned several answer sets where the grounded extension is
unique by definition. The fixtures in `tests/af/` caught it: five of nine
frameworks disagreed. Preferred and stable use the Egly–Gaggl–Woltran style
encodings.

### Scheme files

Twenty-one YAML schemes in `app/argumentation/schemes/`, named
`<reason-prefix>_<claim>.yaml`:

| Prefix | Denial reason | Count |
|---|---|---|
| `mn_` | Medical necessity | 5 |
| `pa_` | Prior authorisation missing | 4 |
| `oon_` | Out of network | 4 |
| `exp_` | Experimental or investigational | 4 |
| `code_` | Coding or billing error | 4 |

Each declares its premises, the evidence type each premise needs, the citation it
rests on, and the rebuttals the insurer is known to raise. The format is
documented in `app/argumentation/schemes/README.md`; governance is in
[`../docs/SCHEMES.md`](../docs/SCHEMES.md).

## The service layer

| Module | Responsibility |
|---|---|
| `ingestion.py` | PDF text layer via pypdfium2; model transcription for scans and photographs. Keeps real character offsets, and returns `None` rather than guessing when a span cannot be located |
| `facts.py` | The confirmation gate. `ExtractedFact.effective_value()` raises on an unconfirmed fact rather than returning `None` |
| `route.py` | Persists determinations, keyed on `(case_id, facts_hash, rulebase_version)` so the same facts never recompute |
| `arguments.py` | Builds the graph, and syncs the evidence checklist from accepted premises |
| `letters.py` | Assembles from accepted nodes only; renders PDF (WeasyPrint) and DOCX (python-docx) |
| `llm.py` | **The only module that imports `anthropic`.** Logs a prompt hash and token counts, never content |
| `reminders.py` | Idempotent: a unique constraint on `(deadline_id, days_before)` means a double-fired cron cannot email twice |
| `storage.py` | Private buckets, short-lived signed URLs, and the per-case object delete |

## API surface

All application routes are under `/api/v1`. `GET /healthz` is not versioned.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/healthz` | Liveness, engine versions, which services are wired |
| `POST` | `/api/v1/public/triage` | The rules engine, no account needed |
| `GET` | `/api/v1/public/triage/options` | Enum values, so the UI cannot drift from what the API accepts |
| `GET` | `/api/v1/me` | The signed-in user, from the verified token only |
| `DELETE` | `/api/v1/me/data` | Hard delete, with a receipt of what went |
| `GET POST` | `/api/v1/cases` | List, open |
| `GET PATCH DELETE` | `/api/v1/cases/{id}` | Read, update, remove |
| `GET POST` | `/api/v1/cases/{id}/documents` | List, upload (multipart) |
| `GET` | `/api/v1/cases/{id}/documents/{doc}/text` | Extracted text, for span highlighting |
| `GET` | `/api/v1/cases/{id}/documents/{doc}/url` | Short-lived signed URL |
| `GET` | `/api/v1/cases/{id}/facts` | Proposed and confirmed facts |
| `POST` | `/api/v1/cases/{id}/facts/{fact}/confirm` · `/edit` · `/reject` | The gate; nothing reaches the engine without one of these |
| `GET POST` | `/api/v1/cases/{id}/route` | Read, compute |
| `GET POST` | `/api/v1/cases/{id}/arguments` | Read, compute |
| `GET` | `/api/v1/cases/{id}/arguments/{arg}` | One argument, with its explanation |
| `GET` | `/api/v1/cases/{id}/evidence` | The checklist |
| `POST` | `/api/v1/cases/{id}/evidence/{key}/attach` | Attach a document to an item |
| `POST` | `/api/v1/cases/{id}/letter` | Generate |
| `GET` | `/api/v1/cases/{id}/letters` | Versions |
| `PATCH` | `/api/v1/cases/{id}/letters/{letter}` | Revise a paragraph |
| `GET` | `/api/v1/cases/{id}/letters/{letter}/export` | `?format=pdf\|docx`, returns a signed URL |
| `GET` | `/api/v1/cases/{id}/timeline` | The case event log |
| `POST` | `/api/v1/cases/{id}/escalate` | Record the final adverse determination |
| `POST` | `/api/v1/billing/checkout` | Stripe Checkout session |
| `POST` | `/api/v1/billing/webhook` | Signature verified before the body is read |
| `GET` | `/api/v1/billing/entitlement` | Tier, and what stays free at every tier |
| `POST` | `/api/v1/internal/run-reminders` | Guarded by `X-Internal-Job-Secret` |

### What is gated and what is not

Never gated: the free triage, opening a case, uploading a letter, confirming
facts, and **seeing the route with its real deadlines and citations**. Somebody
who finds out from us that they have fourteen days left is told that whether or
not they can pay.

Gated: generating and exporting the letter, and the full argument-graph detail.
That is the work product.

## Errors

Every error leaves as `application/problem+json` (RFC 7807) with a
machine-readable `code`, so the frontend has one shape to parse:

```json
{
  "type": "https://appealarchitect.app/problems/facts_not_confirmed",
  "title": "Some facts still need checking",
  "status": 409,
  "detail": "Confirm the denial date and the plan type first.",
  "code": "facts_not_confirmed",
  "pending": ["denial_date", "plan_type"]
}
```

The handler is registered on **Starlette's** `HTTPException`, not FastAPI's, so
an unmatched route renders as problem+json like everything else. A catch-all
handler covers anything unhandled: the traceback is logged, the response says
only that it failed, because an exception message can carry a row and the rows
here are health records.

## Database and migrations

Supabase Postgres. Row-level security on every table, scoped through case
ownership, enforced in the database rather than only in application code. The
backend holds the service-role key — which bypasses RLS — and derives user
identity exclusively from the verified JWT, never from a request body.

Migrations are numbered and forward-only. Apply all three, in order:

```
app/db/migrations/001_init.sql                  14 tables, RLS, 2 private buckets
app/db/migrations/002_case_fields.sql           case fields added in phase 4
app/db/migrations/003_billing_and_profiles.sql  profiles and plan tier
```

Skipping 002 or 003 does not fail loudly. It fails later, as database errors on
upload and on billing.

## Configuration

Every variable is documented in [`../.env.example`](../.env.example). The backend
reads `backend/.env`, relative to the process working directory — a `.env` at the
repository root is read by nothing.

Nothing has a secret default. Each half of the app checks its own gate and
degrades with a message rather than failing at import time, which is why
`/healthz` reports five booleans rather than simply refusing to start. In
production a missing value is logged loudly on every boot; the service still
starts, because a backend that refuses to boot takes the whole site down while a
backend that cannot send reminders is worse in a quieter way.

## The test suite

441 tests, no database required for all but one file.

| File | What it protects |
|---|---|
| `test_boundary.py` | The architectural invariant. AST walk over the import closure, plus negative controls proving it still catches a real violation |
| `test_deadlines.py` | Safety-critical arithmetic: leap years, year boundaries, holiday-adjacent triggers, the conservative-ambiguity path |
| `test_rules_engine.py` | The golden cases in `tests/golden/`, each pinned to a rulebase version |
| `test_argumentation_semantics.py` | The nine frameworks in `tests/af/` with analytically known extensions: even and odd cycles, self-attack, floating defeat |
| `test_argumentation_schemes.py` | Every scheme file parses, cites, and declares its evidence types |
| `test_rulebase_tables.py` | Malformed CSV rows are refused, not skipped |
| `test_migration_rls.py` | Migrations apply in order to fresh Postgres; a second user sees zero rows of the first |
| `test_letters.py` | Every paragraph carries an argument node or is tagged procedural; PDF and DOCX really render |
| `test_problem.py` | Including that an unmatched route is problem+json |

## Deployment

Render, native Python. There is no Dockerfile and none is needed.

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `pip install -e .` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/healthz` |

`backend/main.py` exists only so that start command works; it re-exports the app
from `app/main.py`. `render.yaml` describes the web service and the daily
reminder cron together — Render reads a blueprint from the repository root, so
copy it there if you want it picked up automatically.

The full runbook, including Supabase setup and the reminder cron, is in
[`../docs/DEPLOY.md`](../docs/DEPLOY.md).

## Known limits

**Every legal value in `rules/rulebase/tables/` is UNVERIFIED.** `verified=false`
means nobody has checked that value against the source it cites. Unverified
values are surfaced to the user as a warning on the determination and as a banner
in the UI. They are not hidden, and they are not quietly treated as correct.
`rules/rulebase/CHANGELOG.md` lists the files awaiting a verified source.

**The three state tables are deliberately empty.** `state_ca.csv`,
`state_ny.csv` and `state_tx.csv` have headers and zero rows. With no override
row the federal baseline governs, which is correct and honest. The override
*mechanism* is proven end to end by the synthetic state `XX` in the golden tests,
so the path is exercised without any real value being invented.

**Four of six plan types have no route.** `10_plan_type.lp` admits
`aca_marketplace` and `employer_fully_insured`. The rest produce no track, no
deadlines and a warning saying so. Their filing windows are transcribed in
`deadlines.csv` with `active=false`, but flipping that flag is not enough and the
flag is not the hard part: Medicare Advantage and Medicaid do not terminate in
ACA external review, so routing them through `20_track.lp` as it stands would
produce a confidently wrong track. Each needs its own route shape read out of its
own regulation. See [`../docs/RULEBASE.md`](../docs/RULEBASE.md).

**PDF export depends on system libraries.** WeasyPrint needs Pango and Cairo.
Where they are absent the export returns a 503 naming DOCX as the alternative
rather than a bare 500 — the same letter, and it needs nothing from the operating
system.
