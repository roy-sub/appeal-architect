# Appeal Architect — backend

FastAPI. A symbolic rules engine (clingo) determines the appeal route, the review
levels, the deadlines and the required elements. An argumentation solver computes
which counter-arguments are acceptable. An LLM reads documents and writes prose,
and does nothing else.

That last sentence is enforced by the code, not by convention — see
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) and `tests/test_boundary.py`.

## Run it

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env        # then fill in the backend block
uvicorn app.main:app --reload  # docs at http://localhost:8000/docs
```

It starts with nothing configured. `GET /healthz` reports which services are
wired, and an endpoint whose service is missing returns a 503 naming the
environment variables to set — not a stack trace.

## Test it

```bash
pytest                                    # unit tests, no database needed
ruff check . && ruff format --check .
mypy app

# Migration and RLS tests need a throwaway Postgres. DESTRUCTIVE: the test
# drops and recreates the public, auth and storage schemas.
createdb aa_test
TEST_DATABASE_URL=postgresql://localhost/aa_test pytest tests/test_migration_rls.py
```

`tests/test_boundary.py` is the one you never let go red: it walks the import
closure of `app/rules/**` and `app/argumentation/**` and fails if either can
reach the Anthropic SDK, the network, or the database.

## Layout

```
app/
  main.py            app factory, CORS, problem+json handlers, /healthz
  config.py          settings; per-service "is this configured" gates
  deps.py            JWT verification -> CurrentUser; the job-secret guard
  problem.py         RFC 7807 problem+json with a machine-readable code
  domain/            the shared vocabulary (PURE)
    case.py            PlanType, DenialReason, CaseFacts, ExtractedFact
    route.py           DeadlineItem, RouteStep, RouteDetermination
    argument.py        Argument, Attack, ArgumentGraph
    trace.py           Citation, TraceNode
  rules/             the rules engine (PURE -- no network, no LLM, no DB)
    rulebase/
      VERSION          pinned on every determination
      CHANGELOG.md     what changed, and which files still need a source
      tables/*.csv     transcribed legal values, each with verified=true|false
  argumentation/     the argumentation engine (PURE)
    schemes/           YAML scheme library
  services/          orchestration. May import the engine; the engine never
                     imports services.
  api/v1/            the versioned HTTP surface
  db/
    client.py          Supabase service-role client
    migrations/        numbered forward-only SQL
tests/
  test_boundary.py       the neurosymbolic boundary, with negative controls
  test_migration_rls.py  migration 001 + RLS isolation against real Postgres
  golden/                route and deadline worked examples (phase 2)
  af/                    argumentation fixtures with known extensions (phase 3)
```

## Status

**Phase 1 complete.** Skeleton, domain model, auth, migration 001 with RLS, the
boundary test, Docker build.

Phase 2 builds the rules engine. Until then there are no `.lp` files and nothing
computes a deadline.

### Every legal value in `rules/rulebase/tables/` is UNVERIFIED

`verified=false` means nobody has checked that value against the source it cites.
Unverified values are surfaced to the user as a warning on the route
determination and as a banner in the UI. They are not hidden, and they are not
quietly treated as correct.

`rules/rulebase/CHANGELOG.md` lists the files awaiting a verified source. The
three state tables (`state_ca.csv`, `state_ny.csv`, `state_tx.csv`) are
deliberately **empty** — with no override row the federal baseline governs, which
is honest. A plausible-looking invented state deadline, shown to a user with a
citation beside it, is the most harmful thing this codebase could contain.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | liveness, engine versions, which services are configured |
| `GET /api/v1/me` | the signed-in user, from the verified token |
| `DELETE /api/v1/me/data` | hard delete — phase 7 |
| `GET /api/v1/cases` | this user's cases, soonest deadline first |
| `POST /api/v1/cases` | open a case |

The rest of the surface in the build spec (documents, facts, route, arguments,
evidence, letters, triage, reminders, billing) arrives in phases 4 through 8.

## Two rules for anyone working here

1. **The engine stays pure.** If you need a new import under `app/rules/**` or
   `app/argumentation/**`, read `docs/ARCHITECTURE.md` first. The allow-list in
   `tests/test_boundary.py` is the boundary, and widening it is an architectural
   decision.
2. **Never write a legal value you have not read in its source.** Keep the seed,
   leave `verified=false`, and add the file to the changelog's list.
