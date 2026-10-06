# PLAN.md

Phase 1 plan, open decisions, and the things I think are wrong or underspecified.

**Status: nothing built yet.** This document is the deliverable of step 2 of the working
agreement. I have read the build spec and the whole design bundle. I have written no code.
Section 6 lists what I need from you before Phase 1 starts.

Authority, as agreed: **`Appeal Build Spec.md` wins** on architecture, data, API and
correctness. **`/design` wins** on appearance, copy, spacing and motion. Conflicts are
flagged in sections 3 and 4 rather than silently resolved.

---

## 1. What I read

| Source | Role |
|---|---|
| `Appeal Build Spec.md` | engineering contract |
| `design/project/Appeal Architect.dc.html` (2262 lines) | the approved prototype — visual source of truth |
| `design/chats/chat1.md` (593 lines) | where your decisions actually live |
| `design/project/uploads/Appeal Design Brief.md` | product, voice, fixed strings, media plan |
| `design/project/{tokens.css,tailwind.theme.ts}` | the palette, verbatim |
| `design/project/{components.md,motion.md,media-manifest.md,design-plan.md}` | component, motion and asset specs |
| `frontend/` (9 screens built), `frontend/CLAUDE.md` | the existing implementation and its known-issues list |
| `backend/` (FastAPI scaffold, 485 lines) | triage rules + demo case API |

Two findings from the design bundle that change the spec's reading, both in section 3.

---

## 2. The repo is not greenfield — this changes the phase order

The build spec's phases assume an empty repo. It isn't. What exists:

**Frontend — roughly Phase 5 complete, against demo data.** All nine prototype screens are
built at 390 and 1440, pixel-matched to the prototype, with the per-screen motion moments,
the tokens copied in verbatim, print styles, and reduced motion. It reads
`frontend/lib/case-data.ts`, a hand-written demo case. Nothing calls the backend.

**Backend — a scaffold the spec's architecture replaces.** `app/rules.py` is a Python dict
of four appeal tracks with hardcoded day counts and a regulation string each. There is no
clingo, no trace, no `because/3`, no citation table, no deadline module. `app/data.py` is
generated *from the frontend*. `app/main.py` serves `/api/*`, not `/api/v1/*`.

So Phase 1 is not "stand up a shell". It is **align the repo to the spec's shape, replace
the scaffold's architecture, and add the auth and data spine the real screens need** — while
not regressing a frontend that is already further along than the phase order implies.

I am keeping the spec's phase *order* for the engine work (2, 3) because the whole point of
the invariant is that the engine exists and is tested before anything can call it. What I am
changing is Phase 5: it becomes *re-point the built screens at the API*, not *build the
screens*. Say if you would rather I follow the phases literally.

One consequence worth stating plainly: **the built screens' numbers are demo fiction.**
Phase 5 will replace them with engine output, and some of that output will be less
confident than the prototype's copy (see 3.2). The screens will read as more hedged than
the prototype does. That is the spec's hard rule 3 working as intended.

---

## 3. Build spec vs `/design` — conflicts I am flagging, not resolving alone

### 3.1 Phase 1 asks for a theme switch; you removed dark mode

Spec §13 Phase 1: "Next.js static-export shell with tokens and **theme switch**". Brief §8:
"Light is primary, dark is derived; both complete; theme via `data-theme`". But in
`design/chats/chat1.md` you said, in your own words: *"I also want you to remove the dark
mode, I only need light mode for our site"* — and the designer removed it from the toggle,
the token block and the theme plumbing. `design/project/tokens.css` ships light only.

Appearance is design's authority, and this is your explicit instruction, so: **no theme
switch, light only.** I will not build a dark palette. Flagging because it contradicts the
spec's Phase 1 DoD text and because re-deriving a dark palette later is a real cost.

### 3.2 The prototype's headline deadline is wrong, in the dangerous direction

Every surface in the prototype says the internal-appeal deadline for a 14 Sep 2026 denial is
**22 Mar 2027, 168 days out**. 14 Sep 2026 + 180 days is **13 Mar 2027**. The prototype is 9
days late. A user who trusted it could file 9 days after their window closed. This is
exactly the harm hard rule 3 exists to prevent.

The spec wins: the engine computes the date, the copy renders what the engine returns. The
prototype's 22 Mar / 168 days is deleted from `case-data.ts`, the roadmap, the header pill,
the triage page and the letter. `frontend/CLAUDE.md` already flags this; I am recording that
the fix is mandatory and safety-related, not cosmetic.

There is a second layer the prototype hides. The seed rule is "180 days following **receipt**
of notification" (45 CFR 147.136(b)(2)); the prototype counts from the **letter date** and
its drawer copy asserts "Day one is the day after the letter date". Those are different
triggers and the regulation does not settle which. Under spec §6.4 this is precisely the
ambiguous-trigger case, so the engine will take the **earlier, more conservative** date
(from the denial date), set `ambiguous=True`, and return an `ambiguity_note` the UI must
show. The honest answer is "on or before 13 Mar 2027, and here is why that might be later",
not a single confident date. The RuleDrawer copy needs rewriting to say so.

### 3.3 React Flow vs the hand-laid-out graph

Spec §11 requires React Flow + dagre on desktop. The built graph is hand-positioned per the
prototype, and `frontend/CLAUDE.md` argues React Flow is "not needed at the current graph
size". That argument holds only while the graph is the fixed demo set of six nodes. Once the
solver produces graphs of varying shape — which is the entire product — hand-placement
breaks.

Resolution, splitting it along the authority line: **React Flow + dagre for structure**
(spec wins — it must lay out arbitrary graphs), **the prototype's exact visual** for every
node, lane, connector and marker (design wins — dagre is tuned to reproduce the prototype's
layout on the demo graph's shape, not to impose its own look). The mobile stacked list stays
as built. Phase 5.

### 3.4 `tailwind.config.ts` does not exist and should not

Spec §3 and §11 both name `tailwind.config.ts` and say to copy `/design/tailwind.theme.ts`
in verbatim. The frontend is Tailwind **v4**, which the spec itself specifies — v4 is
CSS-first and has no config file. The tokens are already in `app/globals.css` `:root` and
exposed through `@theme inline`, and the values agree with `design/project/tokens.css`
exactly. Keeping that. `design/project/tailwind.theme.ts` stays the reference the CSS is
checked against; I will add a test that diffs the two so they cannot drift.

### 3.5 §4.4's paragraph check would delete the letter's procedural header

Spec §4.4: every paragraph must carry an `argument_node_id`; "drop or flag any paragraph
that does not". But the letter's procedural header — appeal rights, deadline reference, claim
identifiers — comes from no argument, and `design/project/components.md` already anticipates
this: the `Paragraph` component has a badge reading `procedural` "for the ones no argument
produced".

So the check as literally written drops the legally necessary header. My reading, which I
think is what §4.4 means: a paragraph is valid if it carries **either** an
`argument_node_id` **or** the reserved `procedural` tag, and `procedural` paragraphs are
rendered from a fixed template, never LLM prose. The check then becomes: LLM-generated text
with neither tag is dropped. Confirm this reading.

### 3.6 Media ratios disagree between the prototype and the manifest

`frontend/CLAUDE.md` records it: capability slots are 16/10 in the prototype vs 4/3 in
`media-manifest.md`; personas are 4/5, 4/3, 1/1 vs all 4/3. The manifest was re-synced later
in the design chat than the prototype was last touched, so the manifest is the more recent
intent. Taking the **manifest** (4/3 and 4/3) and adjusting the slots. Cheap to reverse
before real assets exist; expensive after. Say if you want the prototype's ratios.

### 3.7 Section numbering

Your instructions say "the phases in section 12". §12 is Media handling; the phases are
**§13**. I am using §13 and reading the reference as a typo.

---

## 4. Build spec vs this environment — two hard blockers and some friction

### 4.1 `workalendar` cannot be installed (blocker, and it sits under the safety-critical path)

Spec §2 requires `workalendar` for US federal holidays. It does not install: its transitive
dependency `pymeeus` fails to build its wheel on Python 3.13 (`setup.py install` deprecation
in the setuptools path). Verified in this container.

`clingo` 5.8.2, `clorm`, and `python-dateutil` all install cleanly.

Recommended substitute: **`holidays` 0.106** — installs clean, actively maintained,
`holidays.UnitedStates(observed=True)` gives the federal set with observed-date shifting,
which is the behaviour the business-day arithmetic actually needs. Verified working here.

I will put it behind a one-function adapter (`rules/calendar.py` exposing
`is_business_day(date)` / `add_business_days(date, n)`) so the holiday source is a single
swappable module, and unit-test the adapter against a hardcoded table of the 2026–2028
federal holidays transcribed from 5 U.S.C. § 6103 — so the deadline tests do not depend on
any library's correctness. This is a §2 deviation and needs your go-ahead.

### 4.2 No Supabase project, so Phase 1's DoD is not fully reachable by me

Phase 1 DoD: "I can sign up and land on an empty case list." Signing up needs a live
Supabase project. I cannot create one — it needs your account, and the keys are yours.

What I will deliver, so that the DoD closes the moment you paste keys: migration 001 with
every §9 table, RLS policy and private bucket; the JWT-verifying dependency; the browser
auth client; the magic-link sign-in and callback screens; the real empty case list; and a
`.env.example` naming every variable. Unconfigured, the app renders an explicit "backend not
configured" state rather than a crash, and `/healthz` reports which services are wired.

Your part, in `docs/DEPLOY.md` as a checklist: create the project, run the migration, paste
four values. Then I will run the DoD with you.

If you would rather not stand up Supabase yet, the alternative is a local Postgres via
`docker compose` for development only, with Supabase in Phase 8. It costs a second code path
for auth, which I would rather avoid. Question 2 in section 6.

### 4.3 `/design` does not exist at root

Spec §3 requires `/design` at the repo root, read-only. The bundle is actually at
`frontend/design-handoff/`. Your instructions say "/design in this repo", so I think you
believe it is already there. Phase 1 does `git mv frontend/design-handoff design` and
updates the references in `frontend/CLAUDE.md`, root `README.md` and root `CLAUDE.md`.

### 4.4 The strict root shape forbids the usual "one command per side" conveniences

Spec: "Root has exactly: /backend /frontend /design /docs README.md PLAN.md .env.example
.gitignore." That rules out a root `Makefile` or a root `docker-compose.yml`. So "one
command per side" becomes one documented command inside each side, no root tooling:

- backend: `pip install -e . && uvicorn app.main:app --reload`
- frontend: `npm install && npm run dev`

Single root `.env.example` covering both halves per §14; each side reads its own `.env`
copied from it. Noting this because if you want `make dev`, the root shape has to give.

### 4.5 Python 3.13 here, 3.12 in the spec

Container is 3.13.16; spec says 3.12. The Dockerfile pins 3.12 for production parity. I will
keep the code 3.12-compatible and run CI on both. Low risk; recording it because `StrEnum`
and `Decimal` behaviour is version-sensitive.

### 4.6 OCR and PDF system dependencies are not installed here

`tesseract-ocr` and the WeasyPrint native libs are absent from this container. They go in the
Dockerfile per §15, but it means Phase 4 OCR and Phase 6 PDF export can only be unit-tested
against fixtures locally; the real paths need a Docker run to verify. I will do that
verification inside the container rather than claim it from stubs.

### 4.7 `ANTHROPIC_MODEL=claude-sonnet-4-6` is valid but now the expensive choice

Checked against the current model reference rather than memory: `claude-sonnet-4-6` is real —
Claude Sonnet 4.6, 1M context, $3/$15 per MTok. The spec is not inventing a model.

But `claude-sonnet-5-5` is both newer and cheaper: $2/$10 per MTok, same 1M context. On
price alone it strictly dominates.

The catch, and it is a real one for this product: Sonnet 5.5 **rejects forced tool use**
(`tool_choice: {type: "any"}` and `{type: "tool", name}` return 400). Spec §8 wants
extraction via "tool-use, strict schema, temperature 0" — which is usually implemented by
forcing the tool. On 5.5 that becomes `tool_choice: auto` plus `strict: true` plus a prompt
instruction, or structured outputs via `output_config.format`. Both work; neither is a
drop-in. Sonnet 5.5 also rejects `temperature`, which §8 asks for.

So: Sonnet 4.6 matches the spec's described implementation exactly; Sonnet 5.5 is 33% cheaper
on input and needs the extraction call written differently. `ANTHROPIC_MODEL` stays an env
var either way, so this is one line plus the call shape. My recommendation is Sonnet 4.6 for
Phase 4 — the spec's shape, verified against the spec's model, no surprises on the
highest-stakes LLM call — and revisiting cost in Phase 8 when there is usage to measure.
Question 4.

---

## 5. Decisions I am making where the spec is silent

These are mine unless you object; I am not asking about them.

1. **Boundary test walks imports transitively, not just directly.** §4.1 forbids
   `app/rules/**` importing `anthropic`, `httpx`, `app/db/**`. A direct-import check leaks:
   `app/domain/case.py` is permitted, so anything it imports reaches the pure packages. The
   test resolves the full in-package import closure and fails on any forbidden module
   anywhere in it.
2. **Public triage rate limiting without Redis**: a Postgres table keyed by a salted hash of
   the client IP, with a fixed window and a sweep on write. Survives Render's restarts
   (an in-process bucket does not), costs nothing, and free tier is single-instance so the
   distributed-counter problem does not arise. Never stores a raw IP.
3. **Migrations are numbered plain `.sql`**, applied via the Supabase CLI or a documented
   `psql -f` loop. No Alembic — the spec does not list it and Supabase owns the schema.
4. **`DELETE /me/data` also deletes `llm_calls` rows.** They carry no PHI, but they are keyed
   to the user, and "hard delete that actually deletes" should not leave a per-user activity
   record behind. It also deletes `case_events`, which means the audit trail goes too; that
   is the correct trade when the user asks to be forgotten.
5. **`is_urgent_medical` is a user self-declaration that changes deadlines**, so it is never
   silently applied: it is a confirmed fact like any other, and when it shortens a deadline
   the route determination carries a warning saying the expedited track was applied because
   the user declared urgency.
6. **`npm run export:data` is removed.** It generates `backend/app/data.py` from
   `frontend/lib/case-data.ts`, which inverts the spec's data flow — the backend is the
   authority. The script and the generated file go in Phase 1.
7. **`frontend/lib/case-data.ts` survives Phase 1** so the built screens keep rendering while
   the API comes up, and is deleted in Phase 5 when the hooks replace it. It does not become
   a fallback: no screen reads both.
8. **A test diffs `app/globals.css` tokens against `design/project/tokens.css`** so the
   palette cannot drift from the design authority.
9. **Determinism is asserted, not assumed**: the route path runs clingo with `--models=2`
   in tests and fails if a second answer set exists, per §6.3. Production runs `--models=1`.

---

## 6. What I need from you before Phase 1

### Q1 — `workalendar` cannot install. Substitute `holidays`? (blocker)

Recommended: yes, behind the `rules/calendar.py` adapter, with the federal-holiday table
unit-tested independently of the library (4.1). The alternative is vendoring `workalendar`'s
US calendar, which means owning holiday-rule code under the safety-critical path. I would
rather not.

### Q2 — Supabase: will you create the project now, or local Postgres for development? (blocker for Phase 1 DoD)

Recommended: create the Supabase free project now and paste four values. It keeps one auth
code path and makes Phase 1's DoD real (4.2).

### Q3 — CA / NY / TX overrides: I have no statute sources, and I will not invent deadlines

This is the most important question here. Spec §13 Phase 2 requires "federal baseline +
CA/NY/TX overrides". Spec §6.1 and your hard rule 4 forbid inventing legal values and say to
keep a seed marked UNVERIFIED — but §6.2 gives seeds **only for the federal baseline**. There
are no seed values for any state, and you have given me no state sources.

I will not write numbers into `90_state_ca.lp`, `90_state_ny.lp` or `90_state_tx.lp`. A
plausible-looking invented state deadline is the single most dangerous artefact this codebase
could contain: it would be displayed to a user, with a citation, as the date their rights
expire.

So the three state files and their tables ship **structurally complete with zero override
rows**. With no override present, §6.3's defeasible pattern falls through to the federal
baseline — which is correct and honest. The override *mechanism* gets proven by a synthetic
test state (`XX`) in the golden tests, so the federal-default-vs-state-override path is fully
exercised without a single invented real value.

Your options:
- **(a)** Give me the statutes (CA Health & Safety / Insurance Code, NY Insurance Law §§ 4904–4914, TX Insurance Code ch. 4201) or let me research them for your review. Then they are transcribed with citations and marked verified only where you have confirmed them.
- **(b)** Accept wired-but-empty state tables for Phase 2, with the mechanism proven by state `XX`, and fill them later. **This is my recommendation** — it ships an honest Phase 2 and nothing false.

Either way I will hand you the exact filenames to fill.

### Q4 — `claude-sonnet-4-6` as specced, or `claude-sonnet-5-5` for 33% lower input cost?

Recommended: Sonnet 4.6 for Phase 4 (4.7). It matches the spec's described call shape
exactly; 5.5 is cheaper but rejects forced tool use and `temperature`, so the extraction call
has to be written differently on the product's highest-stakes LLM path.

### Q5 — Does my reading of §4.4 stand: `procedural` counts as a valid paragraph tag? (3.5)

Recommended: yes — the design already specifies the `procedural` badge, and the literal check
would drop the letter's legally necessary header.

### Q6 — Phase 5 becomes "re-point the built screens at the API" rather than "build the screens"? (2)

Recommended: yes. The screens exist and are pixel-matched. Rebuilding them to satisfy the
phase order would throw away work and risk the match.

---

## 7. Phase 1, file by file

Starts once sections 6's blockers are answered. Nothing here calls an LLM, and nothing here
computes a deadline.

### 7.1 Repo shape

| Action | Path |
|---|---|
| `git mv` | `frontend/design-handoff/` → `design/` |
| new | `docs/{ARCHITECTURE,RULEBASE,SCHEMES,PRIVACY,DEPLOY}.md` |
| new | `.env.example` — every §14 variable, both halves, commented |
| rewrite | `README.md` — clone → running, one command per side, the Supabase checklist |
| rewrite | `CLAUDE.md` — the new shape, the authority rule, the invariant |
| edit | `.gitignore` — `.env`, `.env.local`, `out/`, `*.egg-info/`, `.ruff_cache/` |

`docs/ARCHITECTURE.md` and `docs/PRIVACY.md` are written in full in Phase 1, not stubbed:
the first fixes the boundary the whole build depends on, the second is hard rule 5 and
governs every later phase. `RULEBASE.md` and `SCHEMES.md` are stubs filled in Phases 2 and 3.

### 7.2 Backend

**Removed** (architecture replaced; values preserved — see below):
`app/rules.py`, `app/data.py`, `tests/test_api.py`, `frontend/scripts/export-case-data.mts`.

Before deleting `app/rules.py` I transcribe its four tracks and their citations into
`app/rules/rulebase/tables/` as UNVERIFIED seed rows with an `effective_date`, so no
inherited value is lost. Phase 2 builds the engine that reads them. Note its Medicare (65
days, 42 CFR 422.582(b)) and Medicaid (60 days, 42 CFR 438.402(c)(2)(ii)) rows are for plan
types the spec defers to Phase 7 — they are transcribed and left inactive.

| Path | What |
|---|---|
| `app/config.py` | `pydantic-settings`; every §14 var; `ENV`; computed "is X configured" flags |
| `app/main.py` | app factory, CORS from env, RFC 7807 handlers, `/healthz`, v1 router |
| `app/problem.py` | RFC 7807 `problem+json` with machine-readable `code` (§10; not in §3's tree) |
| `app/deps.py` | verify Supabase JWT → `CurrentUser`; `user_id` from the token, never the body |
| `app/domain/{case,route,argument,trace}.py` | the full §5 model — the shared vocabulary everything else imports |
| `app/db/client.py` | Supabase client, service-role key, lazy; raises a typed error when unconfigured |
| `app/db/migrations/001_init.sql` | every §9 table, RLS on all of them scoped via `cases.user_id`, private `documents` and `letters` buckets |
| `app/api/v1/{health,me,cases}.py` | `/healthz`, `GET /me`, `DELETE /me/data`, `GET+POST /cases` |
| `app/rules/__init__.py`, `rulebase/{VERSION,CHANGELOG.md}`, `rulebase/tables/*.csv` | package exists, version pinned, seed tables present and UNVERIFIED |
| `app/argumentation/__init__.py`, `schemes/.gitkeep` | package exists for the boundary test to walk |
| `pyproject.toml` | real deps, ruff, pytest, mypy, `requires-python = ">=3.12"` |
| `Dockerfile` | multi-stage, `python:3.12-slim`, `tesseract-ocr-eng` only, WeasyPrint libs per §15 |
| `.dockerignore` | |

Deleting `requirements.txt` in favour of `pyproject.toml` — one dependency source.

**Tests, Phase 1:**

| Path | What |
|---|---|
| `tests/test_boundary.py` | **the invariant, from day one.** AST-walks `app/rules/**` and `app/argumentation/**`, resolves the transitive in-package closure, fails on `anthropic`/`httpx`/`requests`/`app.services.llm`/`app.db`. Asserts `app/services/llm.py` imports neither runner and writes to neither `route_determinations` nor `argument_graphs`. Includes a negative control: a temp module with a forbidden import, asserted to fail — a test that cannot fail is not a test. |
| `tests/test_domain.py` | §5 models round-trip; enums match the spec's strings exactly |
| `tests/test_health.py` | `/healthz`; RFC 7807 shape on a deliberate 404 |
| `tests/test_problem.py` | every error carries a machine-readable `code` |

Hard rule 1 says "add a test that fails if that import appears". It goes in Phase 1, before
there is anything to isolate, so the boundary is never retrofitted.

### 7.3 Frontend

Added dependencies — only what Phase 1 uses: `@supabase/supabase-js`,
`@tanstack/react-query`. React Flow, dagre, PDF.js, react-hook-form and zod arrive in the
phase that needs them.

| Path | What |
|---|---|
| `lib/supabase.ts` | browser client from `NEXT_PUBLIC_*` |
| `lib/api.ts` | typed fetch; Bearer from the session; parses RFC 7807; **the Render cold-start warming state from §15** rather than an error |
| `lib/auth.tsx` | session context, magic-link sign-in, sign-out |
| `app/providers.tsx` | `QueryClientProvider` + auth provider |
| `app/(auth)/signin/page.tsx` | magic link. Brief §6 screen 5 requires it say what happens to documents **on this screen** — it will |
| `app/(auth)/callback/page.tsx` | magic-link landing, client-side (static export has no middleware) |
| `components/workspace/auth-gate.tsx` | client-side guard; renders the shell skeleton, never a flash of someone else's data |
| `app/(workspace)/cases/page.tsx` | rewritten to read `GET /cases` via a hook; the real empty state with the `empty-cases` slot |
| `lib/query-keys.ts` | one key factory, so cache invalidation is not ad hoc |
| `CLAUDE.md`, `README.md` | updated for `design/`, the removed export script, the API data flow |

Not touched in Phase 1: the nine built screens, `globals.css`, the landing page, triage,
`components/landing/**`. They keep reading `case-data.ts` until Phase 5.

### 7.4 Phase 1 Definition of Done

Run with you, as a checklist, before Phase 2 starts.

1. `git ls-files` at root shows exactly the §3 shape.
2. Backend: `pip install -e . && uvicorn app.main:app --reload` → `/healthz` 200, reporting which services are configured.
3. Frontend: `npm install && npm run dev` → landing renders unchanged; `npm run build` static-exports; `npm run lint` and `npm run typecheck` clean.
4. `docker build backend/` succeeds; `/healthz` answers from the container.
5. `pytest` green, `test_boundary.py` included, with its negative control proving it can fail.
6. Migration 001 applies to a fresh Supabase project; RLS verified by a second user seeing zero rows.
7. Sign up by magic link → land on an empty case list → `POST /cases` → it appears. *(Needs Q2.)*
8. `.env.example` lists every §14 variable; `README.md` gets a clean clone to running.
9. No invented legal value anywhere; every seed row carries `verified: false` and a citation.
10. Tokens still match `design/project/tokens.css` (asserted by test).

Then I stop and show you.

---

## 8. Phases 2–8 — one line each, as agreed

| Phase | Shape | The thing I will flag |
|---|---|---|
| 2 Rules engine | CSV→LP generator, `00`–`50` + state `.lp`, `because/3` throughout, `deadlines.py`, CLI runner, golden + `test_deadlines.py` | Q3's answer decides whether CA/NY/TX ship with rows. I will hand you the UNVERIFIED filenames. |
| 3 Argumentation | AF builder, `semantics.lp` (grounded/preferred/stable), 3–5 schemes × 5 denial reasons with known rebuttals, `explain.py` | Scheme *content* is legal-argument shape, not law; I will mark any scheme asserting a legal standard for your review. |
| 4 Data + API + ingestion | migrations complete, case CRUD, upload, OCR with real char offsets, extraction → `ExtractedFact`, confirm/edit/reject, route + arguments wired | Real offsets through the `pypdfium2`→`pytesseract` fallback is the risk; OCR offsets are synthesised, not native. |
| 5 Core product UI | the built screens re-pointed at the API; React Flow + dagre per 3.3; span highlighting via PDF.js | Where engine output is less certain than the prototype's copy, the copy changes. |
| 6 Letters + reminders | letter generation with per-paragraph nodes, editor, PDF/DOCX, reminder job, timeline, escalation | §4.4 per Q5; idempotency proven by running the reminder endpoint twice. |
| 7 Marketing + triage + hardening | the landing already matches; public triage wired with rate limiting per 5.2, `PRIVACY.md`, hard delete proven, PHI-free logging proven | "Proven" means a test, not an assertion. |
| 8 Billing + deploy | Stripe, entitlement gating, Render + Cloudflare Pages, production smoke test | The reminder cron is in the deploy checklist, not a footnote (§15). |

---

## 9. The invariant, in one place

The LLM reads documents and writes prose. It never decides a route, a deadline, a required
element, or whether an argument holds. Enforced by `app/rules/**` and
`app/argumentation/**` having no import path to `anthropic`, by `ExtractedFact.status`
gating every conclusion behind an explicit user confirmation, and by `tests/test_boundary.py`
failing the build if either is violated.

Where the regulation is ambiguous, the engine says so and takes the conservative date.
Where a value is unverified, the user sees that it is unverified.
