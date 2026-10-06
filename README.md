# Appeal Architect

*Your denial, formally refuted.*

Your health insurer refused to pay. The letter cites a policy section you have
never read and a reason code that means nothing to you. Under 0.2% of people
appeal — and roughly half of those who do, win.

Appeal Architect does two things. It works out which appeal track you are legally
on, what your deadlines are, and what each step requires, showing the rule behind
every conclusion. Then it treats the insurer's stated reason as an argument,
builds the counter-arguments that attack it, computes which of them survive the
insurer's likely responses, and writes the appeal letter from the ones that hold.

**The LLM never decides anything.** The appeal route, the review levels, the
deadlines, the required elements and which arguments are acceptable are computed
by a symbolic rules engine and an argumentation solver. The model reads documents
and writes prose. That separation is enforced by the code and by a test, not by
convention — see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Get it running

Node ≥ 20.9 (`.nvmrc` pins 22) and Python ≥ 3.12.

```bash
git clone <this repo> && cd appeal-architect
cp .env.example backend/.env         # fill in the backend block
cp .env.example frontend/.env.local  # fill in the frontend block
```

One command per side:

```bash
# backend  →  http://localhost:8000  (docs at /docs)
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload

# frontend  →  http://localhost:3000
cd frontend && npm install && npm run dev
```

It runs with nothing configured: `GET /healthz` reports which services are wired,
and a screen whose backend is missing says so rather than breaking. To sign in
and keep a case you need a Supabase project — four values, and the steps are in
[`docs/DEPLOY.md`](docs/DEPLOY.md).

## Check it

```bash
cd backend
pytest                       # unit tests, no database needed
ruff check . && mypy app

# Migration and RLS tests need a throwaway Postgres. DESTRUCTIVE — it drops and
# recreates the public, auth and storage schemas.
createdb aa_test
TEST_DATABASE_URL=postgresql://localhost/aa_test pytest tests/test_migration_rls.py

cd ../frontend
npm run typecheck && npm run lint
npm run check:tokens         # fails if the palette has drifted from /design
npm run build                # static export → out/
```

Two tests you never let go red:

- `backend/tests/test_boundary.py` — walks the import closure of the rules and
  argumentation packages and fails if either can reach the Anthropic SDK, the
  network or the database. It carries negative controls, so it cannot silently
  stop working.
- `backend/tests/test_deadlines.py` — the deadline arithmetic (phase 2). A wrong
  deadline can cost someone their appeal rights.

## Layout

```
backend/     Python 3.12, FastAPI, clingo. See backend/README.md
frontend/    Next.js 15 static export, Tailwind v4. See frontend/CLAUDE.md
design/      The approved design system and screens. READ-ONLY — the visual authority
docs/        ARCHITECTURE · RULEBASE · SCHEMES · PRIVACY · DEPLOY
PLAN.md      The build plan, the decisions taken, and the conflicts flagged
MEDIA.md     The 13 assets to generate: path and prompt for each
THIRD_PARTY.md  The accounts and keys you need, and how to get them
.env.example Every environment variable, both halves
```

Two authorities, and they are different ones. `Appeal Build Spec.md` wins on
architecture, data, API and correctness. `design/` wins on appearance, copy,
spacing and motion. Where they conflict, `PLAN.md` §3 records which won and why.

## Where the build is

**All eight phases complete.** The backend serves 28 endpoints; all nine designed
screens plus legal, pricing, settings, timeline and 404 run on live data.

| Phase | | What |
|---|---|---|
| 1 | ✅ | Skeleton, auth, migrations with RLS, the boundary test |
| 2 | ✅ | Rules engine: route, deadlines, required elements, `because/3` traces |
| 3 | ✅ | Argumentation: grounded / preferred / stable, 21 schemes |
| 4 | ✅ | Data, API and ingestion: upload, transcription, the confirmation gate |
| 5 | ✅ | All nine screens wired to the engine; demo data deleted |
| 6 | ✅ | Letters with per-paragraph argument backlinks, PDF/DOCX, reminders |
| 7 | ✅ | Legal, pricing, settings with a real hard delete, timeline, escalation |
| 8 | ✅ | Stripe with entitlement gating, Render and Cloudflare deploy |

Roughly 1,100 tests and checks pass. `PLAN.md` §7b records the eight decisions
taken where the build spec and reality diverged, and why.

### To get it running yourself

Two documents, written for exactly this:

- **[`THIRD_PARTY.md`](THIRD_PARTY.md)** — the five accounts you need, what each
  costs, every key and where it goes, and a pre-launch checklist.
- **[`MEDIA.md`](MEDIA.md)** — the thirteen images and videos, where to save
  each one, and a generation prompt for each. Nothing here blocks launch: every
  slot has a designed placeholder and the layout is already correct without them.

### Two things that are deliberately unfinished, and they are not code

**Every legal value in the rulebase is marked UNVERIFIED.** Nobody has yet
checked those deadlines against the regulations they cite. The product shows
users that they are unverified — in the determination's warnings and as a banner
— rather than letting them assume otherwise.
[`docs/RULEBASE.md`](docs/RULEBASE.md) lists the files awaiting a source.

**The CA, NY and TX override tables are empty on purpose.** With no override
row, the federal baseline governs, which is correct and honest. They are empty
because we have no state statute source, and a plausible-looking invented state
deadline — shown to someone with a citation beside it as the date their rights
expire — is the most harmful thing this codebase could contain.

Both need a person with the sources in front of them. Everything around them is
built and tested.

## What this is not

A self-help document-preparation and information tool. Not legal advice, not
medical advice, not representation. You review and file everything yourself.

> Appeal Architect prepares documents and explains procedure. It is not legal or
> medical advice, and it does not represent you. You review and file everything
> yourself.
