# Appeal Architect

**A neurosymbolic decision-support system for health-insurance appeals.**

Live application: **[appeal-architect.com](https://appeal-architect.com/)**

Appeal Architect takes a health-insurance denial letter and returns three things that a person in that situation cannot otherwise obtain without a lawyer: the appeal procedure that legally applies to them, the deadlines that govern it, and a formally constructed argument against the insurer's stated reason for denial. Every conclusion the system produces is computed by a symbolic reasoner and carries a machine-generated justification trace linking it back to the regulation or rule that produced it.

This repository unifies two previously separate codebases into a single project. The `frontend/` and `backend/` directories each retain their own detailed technical README and documentation; this root document covers the system as a whole: why it exists, how it is designed, and which engineering and research decisions shaped it.

---

## Table of contents

1. [Problem](#1-problem)
2. [What the system does](#2-what-the-system-does)
3. [Why this is a reasoning problem, not a generation problem](#3-why-this-is-a-reasoning-problem-not-a-generation-problem)
4. [System architecture](#4-system-architecture)
5. [The symbolic core](#5-the-symbolic-core)
6. [The AI layer and its enforced boundary](#6-the-ai-layer-and-its-enforced-boundary)
7. [Engineering decisions and trade-offs](#7-engineering-decisions-and-trade-offs)
8. [Correctness, testing and safety-critical paths](#8-correctness-testing-and-safety-critical-paths)
9. [Data model and privacy posture](#9-data-model-and-privacy-posture)
10. [Deployment](#10-deployment)
11. [Repository layout and component documentation](#11-repository-layout-and-component-documentation)
12. [Running the project locally](#12-running-the-project-locally)
13. [Academic context](#13-academic-context)
14. [Current state and roadmap](#14-current-state-and-roadmap)
15. [Complete codebase structure](#15-complete-codebase-structure)
16. [Disclaimer](#16-disclaimer)

---

## 1. Problem

Health insurers in the United States deny a substantial share of submitted claims. Fewer than two people in a thousand appeal a denial. Of those who do appeal, roughly half have the decision reversed.

The gap between those two numbers is not explained by the merits of the claims. It is explained by procedural opacity. Which appeal rights a person holds depends on the legal character of their plan: an ACA marketplace plan, a fully insured employer plan, a self-funded ERISA plan, Medicare Advantage and Medicaid each sit on a different track, with different filing windows, different review bodies, different response obligations on the insurer, and different state-level overrides layered on top of a federal baseline. A missed window is not recoverable. Most people never learn which track they are on until the window has closed.

Existing consumer tools in this space are letter generators. They produce persuasive prose. They do not model the procedure, they do not compute deadlines from the governing regulation, and they cannot say why they concluded anything. In a domain where a wrong date forfeits a legal right, unexplained output is not a usable product.

## 2. What the system does

A user uploads a denial letter, as a PDF or a phone photograph. The system then:

1. **Extracts** the reason codes, claim identifiers, dates, plan identifiers and cited policy language, preserving the exact character offsets of each extraction in the source document.
2. **Presents every extracted fact beside the sentence it came from** for explicit confirmation, editing or rejection. Nothing proceeds to the reasoner until the required facts are confirmed by the user.
3. **Determines the appeal route**: plan-type classification, review levels, who may file, required elements per level, insurer response windows, and every deadline with its trigger date and governing citation.
4. **Constructs the argument**: the insurer's stated reason is treated as an argument in a formal argumentation framework. Counter-arguments are instantiated from a curated scheme library, the insurer's likely rebuttals are encoded as counter-attacks, and an ASP solver computes which counter-arguments are acceptable. Arguments in the grounded extension are presented as "solid ground"; arguments that appear only in some preferred extension are presented as "worth adding" and are labelled as such rather than overstated.
5. **Derives the evidence checklist** from the premises of the accepted arguments, including the specific points a supporting physician letter must make for this particular case.
6. **Generates the appeal letter** from the accepted argument nodes only, with each paragraph carrying a backlink to the node that produced it, exportable to PDF and DOCX with correct print geometry.
7. **Tracks the case** through internal appeal, insurer response, external review and escalation, with reminder emails at fixed intervals before each deadline.

A free triage tool runs the route determination without an account and reports honestly when no appeal route remains.

## 3. Why this is a reasoning problem, not a generation problem

The central design claim of this project is that a large language model is the wrong instrument for the decisions this product makes, and the right instrument for everything surrounding them.

Deadline arithmetic, appeal-track classification and argument acceptability are all problems with correct answers that are determined by published rules. They require defeasible reasoning: a federal baseline that state statutes override, exceptions that defeat defaults, and conclusions that must be withdrawn when a new fact arrives. They also require that the reason for each conclusion be recoverable and inspectable, because the user is going to act on the conclusion in a legal proceeding.

A language model can produce fluent output for all of these and can be wrong in ways that are indistinguishable from being right. A symbolic reasoner either derives a conclusion from the encoded rules or it does not, and when it does, the derivation is the artifact.

The architecture therefore splits strictly along a perception/decision boundary:

| Responsibility | Component | Rationale |
| --- | --- | --- |
| Reading documents, extracting candidate facts | PDF text layer, then the model transcribing what has none | Unstructured input, tolerant of error because the user confirms every fact |
| Classifying plan type, deriving route, computing deadlines | Answer Set Programming (clingo) | Non-monotonic, override-heavy, requires justification |
| Determining which arguments hold | Abstract argumentation solved in ASP | Formal semantics, well-studied, verifiable |
| Writing the appeal letter prose | LLM, constrained to accepted argument nodes | Natural language rendering of an already-decided structure |

This boundary is not a stylistic preference stated in documentation. It is enforced in code and verified by a test, as described in section 6.

## 4. System architecture

```
                    Browser (Next.js, static export, Cloudflare Pages)
                                      |
                              HTTPS, bearer JWT
                                      |
                FastAPI application (native Python, Render)
                                      |
        +-----------------+-----------+-----------+------------------+
        |                 |                       |                  |
   ingestion          rules engine         argumentation         letters
   text layer         clingo / ASP         clingo / ASP          LLM, constrained
   + LLM extraction   route, deadlines     Dung semantics        to accepted nodes
        |                 |                       |                  |
        +-----------------+-----------+-----------+------------------+
                                      |
                    Supabase: Postgres with row-level security,
                    Auth, private object storage, scheduled jobs
```

**Backend.** Python 3.12, FastAPI, Pydantic v2. The codebase is organised so that the reasoning packages are architecturally isolated: `app/rules/` and `app/argumentation/` are pure, with no database access, no network access and no model access. They take validated domain objects in and return determinations with traces out. Everything stateful lives in `app/services/`, everything transport-related in `app/api/v1/`.

**Frontend.** Next.js 15 with the App Router, compiled to a static export. All application state is served by the backend API, which removes any need for server-side rendering and allows the entire frontend to be deployed as static assets on a CDN. TypeScript throughout, with the entire API surface declared in a single typed client module so that the contract between the two codebases is one file to review rather than a pattern to police.

**Database.** Supabase Postgres with row-level security enforced at the database layer on every table, scoped through case ownership. The backend holds a service-role key and derives user identity exclusively from the verified JWT, never from request bodies.

**Scheduled work.** Deadline reminders run through a single idempotent endpoint invoked by a daily scheduled job. The system deliberately carries no message broker and no long-running worker process.

## 5. The symbolic core

### 5.1 Appeal-route rulebase

The route determination is an Answer Set Program. Knowledge is encoded across modular logic programs: plan-type classification, review-level structure per track, deadline rules, required-element rules, expedited-track conditions, and per-state override modules.

The federal baseline and state exceptions are modelled as a default-override pattern, which is precisely the non-monotonic structure the formalism exists to express:

```prolog
deadline(internal_appeal, Days, calendar, "federal") :-
    federal_default(internal_appeal, Days),
    not state_override(internal_appeal, _).

deadline(internal_appeal, Days, calendar, State) :-
    state_override(internal_appeal, Days),
    state(State).
```

Two properties are maintained throughout the rulebase:

**Every derived atom carries its own justification.** Each rule that concludes `X` also derives `because(X, RuleId, Premises)` in the same rule body. An integrity constraint renders any answer set containing an unjustified conclusion unsatisfiable, so a conclusion without a trace is not a degraded result, it is an unsatisfiable program. The trace formatter reads only these justification atoms, which means the explanation shown to the user is generated from the same derivation that produced the answer rather than reconstructed after the fact.

**Regulatory values are transcribed, never inferred.** Every deadline, response window and required element originates in a versioned CSV transcribed from its published source, carrying the citation and an explicit verification flag. A build step compiles these tables into logic-program facts and refuses malformed rows. Any value not yet verified against its source is surfaced as a warning on the determination and as a visible banner in the interface. In a compliance product, a confidently fabricated deadline is a worse failure than a missing one.

Determinations are pinned to a rulebase version and are idempotent with respect to the hash of their input facts, which makes every historical conclusion reproducible even after the rules change.

### 5.2 Argumentation engine

The case construction uses abstract argumentation frameworks in the sense of Dung (1995): a set of arguments together with a binary attack relation, over which acceptability semantics are computed. A structured layer above it instantiates arguments from premises and rules, with attacks typed as rebutting, undermining and undercutting in the ASPIC+ style.

The semantics themselves are computed by Answer Set Programming encodings of grounded, preferred and stable extensions. This is a deliberate reuse of an established result: the correspondence between answer sets and argumentation semantics is well studied, the encodings are compact, and using one solver for both the procedural rulebase and the argumentation layer keeps the trust surface of the system small.

The argument scheme library is curated and versioned: twenty-one schemes, four or five for each of the five most common denial reasons — medical necessity, missing prior authorisation, out-of-network treatment, experimental or investigational exclusion, and coding error. Each scheme declares its required premises, the evidence type each premise needs, and the rebuttals the insurer is known to raise. Those rebuttals are instantiated as counter-attacking arguments inside the framework, so the system genuinely computes defeat rather than asserting it.

The user-facing distinction between "solid ground" and "worth adding" maps directly onto the sceptical/credulous distinction in the semantics: the grounded extension is what holds under every reasonable reading, and arguments appearing only in some preferred extension are presented as conditional. Surfacing this distinction honestly, rather than presenting every available argument as strong, is both the more defensible engineering choice and the more useful product behaviour.

## 6. The AI layer and its enforced boundary

The language model has exactly three jobs, and the system is built so that it cannot acquire a fourth.

**Document extraction.** The ingestion pipeline attempts the PDF text layer first and falls back to model transcription for scanned documents and phone photographs, preserving per-character offsets so that every extracted fact can be highlighted against its origin in the viewer. The model is then invoked with a strict tool-use schema at temperature zero and returns `ExtractedFact` objects: field, value, confidence, source document, source span, and a status that begins as `pending`.

**Letter prose.** The generator receives only the accepted argument nodes, their premises, their citations and the user's confirmed facts. It is prohibited from introducing any factual claim not present in that input, and a post-generation check verifies that every paragraph carries an argument-node identifier.

**Plain-language explanation.** On request, it explains a single trace node or argument in non-technical language, grounded in the retrieved source text.

Three mechanisms enforce the boundary:

1. **Import isolation.** The reasoning packages may import only the standard library, the solver bindings, Pydantic and the domain models. They may not import the model SDK, any HTTP client, the LLM service module, or the database layer.
2. **A test that enforces it.** A boundary test walks the abstract syntax tree of every file in the reasoning packages and fails on any forbidden import. It additionally asserts that the LLM service module never imports a reasoner and never writes to the determination or argument-graph tables. The architectural claim is therefore continuously verified rather than documented and eroded.
3. **A data-flow gate.** The route service reads only facts whose status is `confirmed` or `edited`, both of which require an explicit user action through a dedicated endpoint. There is no code path from a `pending` extraction to a conclusion, which means a model hallucination cannot silently become a legal deadline.

This is the architectural idea the project exists to demonstrate: a language model is used where its failure mode is recoverable and visible to the user, and excluded from every position where its failure mode would be silent.

## 7. Engineering decisions and trade-offs

**Answer Set Programming rather than a general-purpose rule engine.** The domain is saturated with defaults and exceptions. Encoding "federal rule unless the state says otherwise, unless the plan is self-funded, unless the request is urgent" in imperative code produces a conditional thicket that cannot explain itself. ASP expresses this natively and yields the derivation as a first-class object. The cost is a solver dependency and a smaller pool of developers who can maintain the rulebase; the mitigation is that the rules are modular, versioned, and generated from transcribed tables rather than hand-written per value.

**One solver for two reasoning tasks.** Argumentation semantics could have been computed with a dedicated library. Encoding them in the same solver keeps a single reasoning runtime, a single trace format and a single set of correctness tests, and makes the two layers composable.

**Static export rather than server-rendered frontend.** Because all state is behind the API, the frontend has no server-side data requirements. Compiling to static assets removes an entire class of runtime failure, puts the marketing site and the application shell on a CDN edge, and makes the frontend deployment independent of backend availability.

**A single hand-written API client rather than generated bindings.** Every endpoint the frontend can reach is declared in one TypeScript module, with the request and response types written next to the call. Generating the client from the OpenAPI schema was the obvious alternative and was rejected for two reasons: the generated surface is larger than the surface actually used, and the hand-written one carries behaviour the schema cannot express — the shared problem+json error shape, bearer-token attachment, and the cold-start detection that turns a sleeping backend into an explicit warming state rather than a network error. The trade-off accepted is that a backend change must be mirrored by hand; the mitigation is that there is exactly one file to mirror it in, and the type checker fails loudly when a response stops matching.

**Deliberate infrastructure minimalism.** The system runs with no message broker, no worker fleet and no cache tier. Background work uses request-scoped background tasks; scheduled work uses a single idempotent endpoint invoked by a daily job. This was a constraint at the outset (the entire production deployment runs within free infrastructure tiers) and became a design asset: fewer moving parts, a smaller failure surface, and an operational footprint one person can reason about completely.

**Conservative resolution of regulatory ambiguity.** Where a regulation leaves the trigger date for a deadline genuinely ambiguous, for example the date of denial against the date of receipt, the engine computes the earlier and therefore more conservative date, flags the determination as ambiguous, and requires the interface to display the ambiguity note. The system is explicit about the limits of its own knowledge rather than resolving uncertainty silently in the user's disfavour.

## 8. Correctness, testing and safety-critical paths

Not every part of this system carries the same consequence of failure, and the testing strategy reflects that rather than pursuing uniform coverage.

**Deadline arithmetic is treated as safety-critical.** A wrong date can forfeit a legal right that cannot be recovered. The ASP layer emits a count, a unit and a trigger; pure Python functions resolve that to a date. Calendar-day and business-day semantics are explicit per item and never inferred. The test table covers leap years, year boundaries, federal-holiday-adjacent triggers and the conservative-ambiguity path.

**Golden cases for the rulebase.** Worked examples pin expected plan-type classification, track, review levels and deadlines, each recorded against the rulebase version it was verified under. Rulebase changes do not land with a failing golden case.

**Argumentation fixtures with known extensions.** Hand-built frameworks with analytically known grounded, preferred and stable extensions, including the cases that separate the semantics: even and odd attack cycles, self-attacking arguments and floating defeat. Solver output must match exactly. These tests validate the semantics implementation independently of the domain, so a scheme-library change cannot mask a solver regression.

**Determinism as an assertion.** The route determination runs the solver constrained to a single model. More than one answer set indicates an under-constrained rulebase, which is a defect, and the test suite asserts against it rather than silently accepting the first result.

**The architectural boundary test** described in section 6, which converts a design principle into a continuously enforced invariant.

## 9. Data model and privacy posture

The schema is organised around a case: documents, extracted facts with their source spans, route determinations with their traces, argument graphs with their computed extensions, evidence items, deadlines, reminders sent, letter versions and a case event log. Determinations and argument graphs store the rulebase and scheme versions that produced them, so a conclusion reached in October remains explainable in March after the rules have moved.

The system handles protected health information and is designed to that standard irrespective of whether it is formally obligated to:

- Row-level security on every table, enforced in the database rather than only in application code.
- Private object storage with short-lived signed URLs; no document is ever served from a public path.
- No protected health information in application logs, and none in model-call metadata, which records a prompt hash and token counts only.
- User-initiated deletion that performs a hard delete of rows and storage objects, with a test that verifies nothing survives.
- No use of user data for model training.

## 10. Deployment

| Component | Platform | Notes |
| --- | --- | --- |
| Backend | Render, native Python web service | No container image; `pip install -e .` and uvicorn. PDF rendering and the PDF text layer are Python libraries, not system binaries |
| Frontend | Cloudflare Pages | Static export served from the edge |
| Database, auth, storage | Supabase | Postgres with row-level security |
| Scheduled reminders | Render cron job | A thin client calling one idempotent endpoint; Supabase `pg_cron` works equally well |
| Transactional email | Resend | Magic links, deadline reminders, generation notifications |
| Payments | Stripe | One-time case package and recurring subscription, entitlement gating via webhook |

The production deployment is live at **[appeal-architect.com](https://appeal-architect.com/)**, serving the marketing site, the free triage tool and the authenticated case workspace. The rules version currently in force is displayed in the application footer and on every determination, which makes the system's own knowledge boundary visible to the user rather than implicit.

Operational decisions worth noting: the backend tier sleeps when idle, so the frontend renders an explicit warming state on first contact rather than surfacing an error; the reminder job is part of the deployment checklist rather than a footnote, because a silently unscheduled reminder job is a feature that fails without any error ever being raised.

## 11. Repository layout and component documentation

```
appeal-architect/
├── backend/        FastAPI service, reasoning engines, rulebase, scheme library
├── frontend/       Next.js application, static export
├── design/         Design system, tokens, reference screens
├── docs/           Architecture, rulebase, schemes, privacy and deployment notes
├── .env.example    Every environment variable, both halves, annotated
└── README.md       This document
```

Each half of the system carries its own full technical documentation, written for a reader who intends to build, modify or extend that component:

- **[`backend/README.md`](./backend/README.md)** covers the service layout, the rules and argumentation packages, the rulebase compilation pipeline, the scheme library format, the API surface and the test suite. Component-specific technical notes live alongside it inside the `backend/` directory.
- **[`frontend/README.md`](./frontend/README.md)** covers the application structure, the typed API client, the document viewer and source-span highlighting, the argument-graph rendering on desktop and mobile, the design-token system and the static-export build. Further frontend-specific technical documentation is kept within the `frontend/` directory.
- **[`docs/`](./docs/)** holds the cross-cutting documents: the architecture record, the rulebase and scheme governance notes, the privacy data-flow description and the deployment runbook.

A complete file-by-file map of the repository is in [section 15](#15-complete-codebase-structure).

## 12. Running the project locally

Prerequisites: Python 3.12, Node.js 20 or later, and a Supabase project. No container runtime is required.

```bash
# Backend
cd backend
cp ../.env.example .env          # fill in Supabase, Anthropic, Stripe, Resend keys
pip install -e ".[dev]"
uvicorn app.main:app --reload    # http://localhost:8000, interactive docs at /docs

# The route engine, standalone — no web stack, no database, no model
python -m app.rules.cli --plan aca_marketplace --state CA \
    --denial-date 2026-09-14 --timing post \
    --reason not_medically_necessary --trace

# Frontend
cd ../frontend
cp ../.env.example .env.local    # fill in the four NEXT_PUBLIC_ values
npm install
npm run dev                      # http://localhost:3000
```

The route engine runs standalone from the command line without the web stack, which keeps the rulebase developable and testable in isolation from the application; the argumentation engine is exercised the same way through its framework fixtures in `backend/tests/af/`. The application starts with nothing configured — `GET /healthz` reports which services are wired, and a screen whose backend is missing says so rather than breaking. Component-specific setup, migration and environment details are documented in the two subdirectory READMEs linked above.

## 13. Academic context

This project was built as an applied demonstration of symbolic and knowledge-representation techniques in a setting where their advantages over purely statistical methods are not rhetorical but operational.

The formal content it exercises:

- **Abstract and structured argumentation.** Dung-style argumentation frameworks with an ASPIC+-flavoured instantiation layer, with grounded, preferred and stable semantics computed through Answer Set Programming encodings, and the sceptical/credulous distinction surfaced directly as a product affordance.
- **Non-monotonic and defeasible reasoning.** Federal defaults defeated by state overrides, exceptions defeating general rules, and conclusions that retract correctly when a fact is withdrawn.
- **Rules as code with proof traces.** A regulatory corpus encoded as a versioned, source-linked logic program in which justification is a derived object rather than a reconstruction, and every determination is reproducible against the rulebase version that produced it.
- **Verifiable neurosymbolic separation.** A language model confined to perception and language, a symbolic reasoner holding every decision, and an architectural invariant enforced by a test rather than asserted in prose.

These areas correspond closely to the research profile of TU Wien's Faculty of Informatics, in particular the work of the Databases and Artificial Intelligence group on argumentation semantics and ASP, and the Logic and Computation programme's treatment of knowledge representation and non-monotonic reasoning. The intention here was to take that formal apparatus out of the exercise sheet and into a deployed system with real users, real regulatory text and real consequences for being wrong, and to find out which parts of the theory survive that transition. The trace-carrying rulebase pattern and the enforced boundary test are both answers to problems that only appeared once the system had to be trusted by someone who would act on its output.

The argumentation semantics encodings and the architecture write-up are intended for separate publication as an open artifact.

## 14. Current state and roadmap

**Live and in production:** ACA marketplace and fully insured employer plans on the federal baseline; document ingestion with confirmation; route determination with cited deadlines; argument construction across the five most common denial reasons; evidence checklist; letter generation and export; deadline reminders; free triage; payments.

**Two limits the system states rather than hides.** Every regulatory value in the rulebase is currently marked unverified — transcribed from its source but not yet read back against it by a person — and the determination carries that as a warning and the interface as a banner. The California, New York and Texas override modules are wired and their tables are deliberately empty: with no override row the federal baseline governs, which is correct and honest, and the override mechanism is proven end to end by a synthetic test state rather than by an invented statutory value. A plausible-looking fabricated state deadline, shown to a user with a citation beside it as the date their rights expire, is the single most harmful artifact this codebase could contain.

**Next:** verification of the federal baseline against its sources and the first real state overrides; ERISA self-funded and Medicare Advantage tracks, each of which needs its own route shape read out of its own regulation rather than a flag, since neither terminates in ACA external review; outcome telemetry feeding scheme-strength revision (a belief-revision problem over the scheme library rather than a statistical one); a physician-letter collaboration flow; and multi-case dashboards for professional patient advocates.

## 15. Complete codebase structure

Every tracked source file, with four groups collapsed for readability: the
twenty-one scheme files are shown by prefix with their counts, the twelve media
assets and the design reference images are summarised, and build artifacts,
lockfiles, virtual environments and tool caches are omitted.

```
appeal-architect/
├── backend/                                  Python 3.12 · FastAPI · clingo · Pydantic v2
│   ├── app/
│   │   ├── api/v1/                           Transport only: no reasoning, no SQL
│   │   │   ├── arguments.py                  Build and read the argument graph
│   │   │   ├── billing.py                    Stripe checkout, webhook, entitlement gate
│   │   │   ├── cases.py                      Case CRUD
│   │   │   ├── documents.py                  Upload, signed URL, extracted text
│   │   │   ├── facts.py                      Confirm · edit · reject an extracted fact
│   │   │   ├── health.py                     /healthz: which services are wired
│   │   │   ├── internal.py                   Job-secret guarded reminder run
│   │   │   ├── letters.py                    Generate, revise, export PDF/DOCX
│   │   │   ├── me.py                         Account, and the hard delete
│   │   │   ├── public.py                     Free triage, unauthenticated
│   │   │   └── route.py                      Compute and read the route determination
│   │   ├── argumentation/                    PURE — no network, no LLM, no database
│   │   │   ├── schemes/                      21 YAML schemes, versioned
│   │   │   │   ├── VERSION
│   │   │   │   ├── README.md                 The scheme file format
│   │   │   │   ├── code_*.yaml               Coding error            (4)
│   │   │   │   ├── exp_*.yaml                Experimental exclusion  (4)
│   │   │   │   ├── mn_*.yaml                 Medical necessity       (5)
│   │   │   │   ├── oon_*.yaml                Out of network          (4)
│   │   │   │   └── pa_*.yaml                 Prior authorisation     (4)
│   │   │   ├── builder.py                    Schemes + facts -> arguments and attacks
│   │   │   ├── explain.py                    Why an argument held, or did not
│   │   │   ├── semantics.lp                  Grounded · preferred · stable, in ASP
│   │   │   └── solver.py                     clingo driver for the above
│   │   ├── rules/                            PURE — no network, no LLM, no database
│   │   │   ├── rulebase/
│   │   │   │   ├── tables/                   Transcribed legal values, each with a citation
│   │   │   │   │   ├── citations.csv         Source, locator, quote
│   │   │   │   │   ├── deadlines.csv         Counts, units, triggers, verified flags
│   │   │   │   │   ├── required_elements.csv What a filing must contain, per level
│   │   │   │   │   ├── state_ca.csv          Headers only, deliberately empty
│   │   │   │   │   ├── state_ny.csv          Headers only, deliberately empty
│   │   │   │   │   ├── state_tx.csv          Headers only, deliberately empty
│   │   │   │   │   └── state_xx.csv          Synthetic state, proves the override path
│   │   │   │   ├── 00_core.lp                Integrity constraints, justification rules
│   │   │   │   ├── 10_plan_type.lp           Which plans the rulebase will route
│   │   │   │   ├── 20_track.lp               Review levels, who files, who decides
│   │   │   │   ├── 30_deadlines.lp           Counts and triggers per item
│   │   │   │   ├── 40_required.lp            Required elements per level
│   │   │   │   ├── 50_expedited.lp           Urgent-track conditions
│   │   │   │   ├── 90_state_ca.lp            Default-override modules, one per state
│   │   │   │   ├── 90_state_ny.lp
│   │   │   │   ├── 90_state_tx.lp
│   │   │   │   ├── VERSION                   Pinned onto every determination
│   │   │   │   └── CHANGELOG.md              What changed, and what awaits a source
│   │   │   ├── calendar.py                   US federal holidays, behind an adapter
│   │   │   ├── cli.py                        Run the engine with no web stack
│   │   │   ├── deadlines.py                  Count + unit + trigger -> a date
│   │   │   ├── facts.py                      CaseFacts -> logic-program facts
│   │   │   ├── generate.py                   CSV -> .lp, refusing malformed rows
│   │   │   ├── runner.py                     clingo driver; refuses a non-unique model
│   │   │   └── trace.py                      because/3 atoms -> a readable trace
│   │   ├── domain/                           The shared vocabulary. Pure Pydantic
│   │   │   ├── argument.py                   Argument, Attack, ArgumentGraph
│   │   │   ├── case.py                       PlanType, DenialReason, CaseFacts, ExtractedFact
│   │   │   ├── route.py                      DeadlineItem, RouteStep, RouteDetermination
│   │   │   └── trace.py                      Citation, TraceNode
│   │   ├── services/                         Everything stateful
│   │   │   ├── arguments.py                  Graph computation and evidence sync
│   │   │   ├── facts.py                      The confirmation gate
│   │   │   ├── ingestion.py                  Text layer, then model transcription
│   │   │   ├── letters.py                    Assembly, PDF and DOCX rendering
│   │   │   ├── llm.py                        The ONLY module that imports anthropic
│   │   │   ├── reminders.py                  Idempotent reminder run
│   │   │   ├── route.py                      Persist and reuse determinations
│   │   │   └── storage.py                    Private buckets, short-lived signed URLs
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   │   ├── 001_init.sql              14 tables, RLS on every one, 2 buckets
│   │   │   │   ├── 002_case_fields.sql
│   │   │   │   ├── 003_billing_and_profiles.sql
│   │   │   │   └── README.md
│   │   │   ├── client.py                     Service-role client
│   │   │   └── repo.py                       Ownership-scoped row access
│   │   ├── jobs/send_reminders.py            What the daily cron runs
│   │   ├── templates/                        Email templates
│   │   ├── config.py                         Settings, and the per-service "is it wired" gates
│   │   ├── deps.py                           JWT verification -> CurrentUser; job-secret guard
│   │   ├── main.py                           App factory, CORS, problem+json handlers
│   │   ├── problem.py                        RFC 7807 with a machine-readable code
│   │   └── site.py                           Fixed strings, including the disclaimer
│   ├── tests/
│   │   ├── af/                               Frameworks with analytically known extensions
│   │   │   ├── frameworks.json
│   │   │   └── README.md
│   │   ├── golden/                           Worked route cases, pinned to a rulebase version
│   │   │   ├── 01_aca_post_service_standard.json
│   │   │   ├── 02_aca_pre_service_standard.json
│   │   │   ├── 03_receipt_date_known.json
│   │   │   ├── 04_urgent_expedited.json
│   │   │   ├── 05_employer_fully_insured.json
│   │   │   ├── 06_external_review_dated.json
│   │   │   ├── 07_leap_year_crossing.json
│   │   │   └── 08_year_boundary.json
│   │   ├── fixtures/supabase_stub.sql
│   │   ├── conftest.py
│   │   ├── test_argumentation_schemes.py
│   │   ├── test_argumentation_semantics.py
│   │   ├── test_auth.py
│   │   ├── test_billing.py
│   │   ├── test_boundary.py                  The architectural invariant, enforced
│   │   ├── test_calendar.py
│   │   ├── test_deadlines.py                 Safety-critical arithmetic
│   │   ├── test_domain.py
│   │   ├── test_health.py
│   │   ├── test_ingestion.py
│   │   ├── test_letters.py
│   │   ├── test_migration_rls.py             Needs a throwaway Postgres
│   │   ├── test_problem.py
│   │   ├── test_public_triage.py
│   │   ├── test_reminders.py
│   │   ├── test_rulebase_tables.py
│   │   ├── test_rules_cli.py
│   │   └── test_rules_engine.py
│   ├── main.py                               Entry shim, so Render can run `uvicorn main:app`
│   ├── pyproject.toml
│   ├── render.yaml                           Web service + daily reminder cron
│   └── README.md
│
├── frontend/                                 Next.js 15 · static export · Tailwind v4 · Motion
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── auth/callback/page.tsx        Where the magic link lands
│   │   │   └── signin/                       page.tsx + layout.tsx (its own metadata)
│   │   ├── (workspace)/                      Everything behind AuthGate
│   │   │   ├── case/
│   │   │   │   ├── arguments/page.tsx        The argument graph — the centrepiece
│   │   │   │   ├── documents/page.tsx        Upload and camera capture
│   │   │   │   ├── evidence/page.tsx         Checklist and physician-letter points
│   │   │   │   ├── facts/page.tsx            Confirm each fact beside its source span
│   │   │   │   ├── letter/page.tsx           Paragraph -> argument backlinks, print styles
│   │   │   │   ├── roadmap/page.tsx          Steps, deadlines, the rule behind each
│   │   │   │   └── timeline/page.tsx         The record, and escalation
│   │   │   ├── cases/page.tsx                Case list and empty state
│   │   │   ├── settings/page.tsx             Account, entitlement, the real hard delete
│   │   │   └── layout.tsx                    Authenticated shell
│   │   ├── triage/                           page.tsx + layout.tsx (its own metadata)
│   │   ├── legal/page.tsx                    Terms, privacy in plain language, rules changelog
│   │   ├── pricing/page.tsx
│   │   ├── page.tsx                          Landing
│   │   ├── layout.tsx                        Fonts, metadata, the share card
│   │   ├── providers.tsx                     TanStack Query + AuthProvider
│   │   ├── not-found.tsx                     404
│   │   ├── globals.css                       Tokens, @theme mapping, print, reduced motion
│   │   ├── robots.ts                         Keeps the signed-in screens out of the index
│   │   ├── sitemap.ts                        The five public pages
│   │   ├── icon.png · apple-icon.png · favicon.ico
│   ├── components/
│   │   ├── domain/
│   │   │   ├── argument-graph.tsx            React Flow + dagre, lazy-loaded, desktop only
│   │   │   └── argument-node.tsx             The card in all four tiers
│   │   ├── landing/                          hero.tsx · sections.tsx · faq.tsx
│   │   ├── ui/                               button · accordion · sheet (Radix)
│   │   ├── workspace/
│   │   │   ├── auth-gate.tsx                 Client guard; a static export has no middleware
│   │   │   ├── buy-button.tsx                The one path to Stripe Checkout
│   │   │   ├── case-context.tsx              Active case, shared across the workspace
│   │   │   ├── not-configured.tsx            Shown when the backend is not wired up
│   │   │   ├── shell.tsx                     AppShell, PageHead, shared class atoms
│   │   │   └── states.tsx                    Loading · empty · error · stages · banners
│   │   ├── deadline-ring.tsx
│   │   ├── media-slot.tsx                    Renders a shipped asset, or its placeholder
│   │   ├── motion-provider.tsx
│   │   ├── reveal.tsx                        The one animation wrapper
│   │   └── status-pill.tsx
│   ├── lib/
│   │   ├── api.ts                            The whole API surface: types, problem+json, warming
│   │   ├── auth.tsx                          Session context, magic-link sign-in
│   │   ├── hooks.ts                          One hook per endpoint
│   │   ├── landing-content.ts                Landing copy
│   │   ├── media.ts                          Which assets have shipped, and their real sizes
│   │   ├── motion.ts                         Easings, durations, named gestures
│   │   ├── query-keys.ts                     One key factory, so invalidation is not guesswork
│   │   ├── site-url.ts                       Where this build will live
│   │   ├── site.ts                           Disclaimer, rules stamp
│   │   ├── supabase.ts                       Browser auth client
│   │   ├── time.ts                           Deadline tone thresholds
│   │   └── utils.ts
│   ├── public/
│   │   ├── media/                            12 slot assets + the 1200x630 share card
│   │   └── _headers                          Security headers and cache lifetimes for Pages
│   ├── scripts/check-tokens.mjs              Fails if the palette has drifted from /design
│   ├── components.json · eslint.config.mjs · next.config.ts
│   ├── postcss.config.mjs · tsconfig.json · package.json · .nvmrc
│   ├── CLAUDE.md                             Conventions and the hard product rules
│   └── README.md
│
├── design/                                   READ-ONLY. The original Claude Design export
│   ├── project/
│   │   ├── uploads/                          The design brief and reference images
│   │   ├── Appeal Architect.dc.html          The final prototype — the visual authority
│   │   ├── MediaSlot.dc.html
│   │   ├── components.md · motion.md         Behaviour specs
│   │   ├── media-manifest.md                 Slot ids, ratios, intrinsic sizes
│   │   ├── design-plan.md                    Principles (its palette section predates forest/clay)
│   │   ├── tokens.css · tailwind.theme.ts    What check-tokens.mjs validates against
│   │   └── support.js
│   ├── chats/chat1.md                        Where the design decisions were actually made
│   └── README.md
│
├── docs/
│   ├── ARCHITECTURE.md                       The boundary, and how it is enforced
│   ├── RULEBASE.md                           What the rules may say, and what is missing
│   ├── SCHEMES.md                            The scheme library and its governance
│   ├── PRIVACY.md                            The data flow, and what is not yet built
│   └── DEPLOY.md                             Supabase, Render, Cloudflare, the reminder cron
│
├── .env.example                              Every variable, both halves, annotated
├── .gitignore
└── README.md                                 This document
```

## 16. Disclaimer

Appeal Architect prepares documents and explains procedure. It is not legal or medical advice, and it does not represent its users. Users review and file everything themselves. The system makes no claim about the outcome of any appeal, and the application states this wherever it could otherwise be inferred.
