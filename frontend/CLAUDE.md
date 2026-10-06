# Appeal Architect — frontend

Consumer web app that helps a person fight a health-insurance denial. It works out the
appeal track and deadlines, with the rule behind each. It builds the counter-arguments
against the insurer's stated reason, then writes the appeal letter from the arguments that
hold. Read `../design/project/uploads/Appeal Design Brief.md` before any product decision.

## Commands

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # static export → out/
npm run lint         # eslint (flat config)
npm run typecheck    # tsc --noEmit
npm run check:tokens # fails if the palette has drifted from /design
```

Node ≥ 20.9 (`.nvmrc` pins 22). Next.js 15 App Router with `output: "export"`: no SSR, no
server actions, no `next/image` optimisation.

## Stack

Tailwind CSS v4 (CSS-first config in `app/globals.css`), shadcn-style primitives on Radix
(`components/ui/*`, `components.json`), Motion (`motion/react`, formerly Framer Motion),
`next/font` for IBM Plex Sans / IBM Plex Mono / Newsreader.

## Layout

```
app/
  page.tsx                      Landing (sections in components/landing/)
  providers.tsx                 TanStack Query + AuthProvider
  triage/page.tsx               Free triage: 4 questions → track, deadline, honest verdict
  (auth)/signin/                Magic link; says what happens to their documents, here
  (auth)/auth/callback/         Where the magic link lands (client-side, no server)
  (workspace)/layout.tsx        Authenticated shell + AuthGate
  (workspace)/cases/            Case list + empty state
  (workspace)/case/documents/   Upload wizard
  (workspace)/case/facts/       Extraction review + named "working" stages
  (workspace)/case/roadmap/     Procedural roadmap + RuleDrawer (Radix dialog sheet)
  (workspace)/case/arguments/   Argument graph — the centrepiece
  (workspace)/case/evidence/    Evidence checklist + physician-letter points
  (workspace)/case/letter/      Letter with paragraph → argument backlinks, print styles
  (workspace)/case/timeline/    The record, plus the escalation flow
  (workspace)/settings/         Account, entitlement, and the real hard delete
  legal/, pricing/              Terms, privacy in plain language, rules changelog
  not-found.tsx                 404
  globals.css                   Tokens (:root) + @theme mapping + print + reduced motion
components/
  ui/                           button (cva variants), accordion, sheet
  landing/                      hero.tsx (nav, hero, marquee), sections.tsx, faq.tsx
  workspace/shell.tsx           AppShell, CaseHeader, PageHead, shared class atoms
  workspace/case-context.tsx    Client case state shared across workspace screens
  workspace/auth-gate.tsx       Client-side guard (static export has no middleware)
  workspace/not-configured.tsx  Notice shown when the backend is not wired up
  workspace/states.tsx          Loading, empty, error, named stages, warning banners
  domain/argument-node.tsx      The argument card in all four tiers
  domain/argument-graph.tsx     React Flow + dagre; lazy-loaded, desktop only
  reveal.tsx                    The one animation wrapper (see Motion)
  media-slot.tsx                Deferred-asset placeholder (roomy / tight / fill)
  deadline-ring.tsx, status-pill.tsx
lib/
  api.ts                        Typed backend client: bearer token, problem+json, warming state
  supabase.ts                   Browser auth client
  auth.tsx                      Session context, magic-link sign-in
  query-keys.ts                 One key factory, so invalidation is not guesswork
  hooks.ts                      One hook per endpoint; active case in localStorage
  landing-content.ts            Landing copy
  motion.ts                     Easings, durations, named gestures
  time.ts                       Deadline tone thresholds
  site.ts                       Fixed strings: disclaimer, rules stamp
(design lives at the repo root, ../design/ — original Claude Design export, read-only)
```

## Sources of truth, in priority order

1. `../design/project/Appeal Architect.dc.html`: the final prototype. Visual values
   (px sizes, spacing, colours) were taken from it exactly.
2. `../design/chats/chat1.md`: the user's decisions while iterating (light mode only,
   forest/clay palette, landing redesign, "how it works" desktop fix).
3. `../design/project/components.md`, `motion.md`, `media-manifest.md`: behaviour
   specs. Where they disagree with the prototype on visuals, the prototype wins.
4. `../design/project/design-plan.md`: its palette section is **outdated** (it predates
   the forest/clay palette). Its principles still apply.

## Rules that must not break

- **Fixed strings, verbatim.** "Appeal Architect" · "Your denial, formally refuted." ·
  "Every paragraph backed by a rule." · the disclaimer in `lib/site.ts` (footer + every
  letter) · "Rules current as of {date} · version {v}" on every route determination ·
  tier labels "Solid ground" and "Worth adding".
- **Never imply an outcome.** No "guaranteed", "we'll win", "fight back", "loophole",
  "hack", "secret"; no war metaphors; no confetti, trophies or check-burst success states.
- **Copy:** grade-8 plain language, active voice, no exclamation marks, never apologises or gushes.
- **No red anywhere**, including errors. Errors use `--ink` plus a bar and an instruction.
- **Deadlines calm, never alarming.** Tone by proximity only (`lib/time.ts`; no hue above 60
  days). Never animate a countdown, ring, or deadline after its entrance.
- **Colour never carries meaning alone.** Argument tiers: solid = solid border + 3px
  standing edge + `●`; worth adding = dashed + `◇`; left out = hatch + strikethrough + `✕`.
- **Accessibility floor:** AA contrast, visible focus (global `:focus-visible`, clay),
  44px minimum touch targets, reduced motion honoured, a disabled button always has its
  reason stated beside it.
- **Mobile is first-class.** Desktop layouts switch on at `lg` (1024px). Design targets are
  390 and 1440.

## Conventions

- **Tokens** live in `app/globals.css` `:root` and are exposed via `@theme inline`
  (`bg-ground`, `text-ink-muted`, `border-standing`, `bg-time-track`, …). Never write raw
  hex in components. Tailwind's default spacing scale is *not* overridden. Design values
  are arbitrary px (`text-[17px] leading-[29px]`) to stay pixel-exact with the prototype.
- **Radii:** marketing surfaces 2px (sharp); workspace cards 16px, buttons 10px / 8px.
- **Buttons:** use `<Button variant=…>`. `primary/ghost/small/inkSmall` for the workspace;
  `nav/clay/heroGhost/invert/clayBlock/outlineBlock` for marketing.
- **Motion:** only through `<Reveal gesture=… trigger="view"|"load">` or Motion with the
  `ease` / `dur` values from `lib/motion.ts`. Each landing section owns one gesture; don't
  reuse a gesture across landing sections. Elements that start fully clipped need
  `wrapClassName` (IntersectionObserver can't see them). `instant` renders the end state.
  Only transform/opacity/clip-path animate.
- **Media:** every image or video goes through `<MediaSlot>` with the id, ratio and intrinsic
  size from `media-manifest.md`. To ship an asset, render it inside the same box, so the
  layout is unchanged.
- **Case data** comes from the API, always. There is no demo data and no
  fallback: a screen that cannot reach the backend says so rather than showing
  something plausible.
- **Dates.** The frontend never does date arithmetic beyond "days until". Every
  deadline is computed server-side and sent as a date, with the rule it came from.

## Status

Built: all 9 prototype screens at 390 and 1440. Per-screen motion moments from `motion.md`:
- the hero line lift and plate push
- one unique gesture per landing section
- the triage verdict unfold
- the named extraction stages advancing
- roadmap steps rising
- the argument graph assembling (1.8s, with a "Show it all" skip; plays once per visit,
  Replay re-runs it)
- letter paragraphs assembling, each badge 80ms behind its sentence
- evidence → argument node pulse

Also built:
- Selecting a letter paragraph selects its argument across screens.
- Selecting a fact shows the source sentence it came from.
- The deadline "passed" state.
- Decorative fill slots are `aria-hidden`.
- The letter prints on US Letter.

### Resolved

- **The prototype's deadline was nine days late.** It showed 22 Mar 2027 / 168
  days for a 14 Sep 2026 denial; the correct date is 13 Mar 2027. Fixed by
  deletion: the demo data is gone and every date on screen is computed by the
  rules engine and rendered as returned, with its ambiguity note when the
  regulation's trigger is unclear.
- **React Flow + dagre** on desktop, stacked lanes on mobile. Hand-placement
  only worked for one fixed set of nodes, and the solver produces varying
  shapes. The graph bundle is lazy-loaded so its ~70 kB stays off phones, which
  render the list instead -- not a fallback, the better reading on a phone.
- **Media ratios** now follow `media-manifest.md` where the two disagreed. The
  remaining slots and their generation prompts are in the root `MEDIA.md`.
- **Footer legal links** point at `/legal`, which exists.
- **Triage** runs the real engine, with options served from the backend's enums
  so they cannot drift from what it accepts.
- **Export** produces real PDF and DOCX through a signed URL; print still works.
- **Upload** reads the file: PDF text layer first, model transcription for scans
  and photos, with real character offsets so a fact's highlight lands on the
  characters it actually came from.
- **The rules stamp** reads its version from `/healthz` rather than a constant,
  which would have gone on claiming currency after the rulebase moved.
- **The roadmap gate** names exactly which facts are still outstanding, because
  a disabled button always states its reason beside it.

### Still open

- `trust-strip` and `graph-legend` were dropped deliberately -- the reasons are
  in the last section of the root `MEDIA.md`.
- Spec components not built as standalone pieces, because the screens that
  needed them implement the behaviour inline: `Field` (the no-red error state
  lives in `components/workspace/states.tsx`), `DestructiveDialog` (the
  type-the-phrase delete flow on `/settings`), toasts (mutations report inline,
  beside the thing they changed), the `MarginNote` connector hairline.
- The media files themselves. Every slot has a designed placeholder, so nothing
  is broken without them.

### Everything is wired to the backend

`lib/case-data.ts` is deleted and nothing references it. One typed wrapper per
endpoint in `lib/api.ts`, one hook per endpoint in `lib/hooks.ts`.

| Screen | Reads |
|---|---|
| `/triage/` | `POST /public/triage`, `GET /public/triage/options` |
| `/signin/`, `/auth/callback/` | Supabase Auth |
| `/cases/` | `GET /cases` |
| `/case/documents/` | `GET` + `POST /cases/{id}/documents` |
| `/case/facts/` | `GET /facts`, confirm / edit / reject, `GET /documents/{id}/text` |
| `/case/roadmap/` | `GET` + `POST /cases/{id}/route` |
| `/case/arguments/` | `GET` + `POST /arguments`, `GET /arguments/{id}` |
| `/case/evidence/` | `GET /evidence`, `POST /evidence/{key}/attach` |
| `/case/letter/` | `POST /letter`, `GET /letters`, `PATCH`, export, entitlement |
| `/case/timeline/` | `GET /timeline`, `POST /escalate` |
| `/settings/` | `GET /me`, `DELETE /me/data`, `GET /billing/entitlement` |
| `/legal/`, `/pricing/` | static |

No screen reads both live data and a fallback. Where the backend is unreachable
the screen says so; where a prerequisite is missing it names which one and links
to it.

No theme switch and no dark palette. The build spec's phase 1 asks for one; the
design chat removed dark mode by explicit instruction, and appearance is
design's authority. See `PLAN.md` §3.1.

## What a next build would add

Everything in brief §6 is now built. What is left is genuinely additional:

- Dependants managed under one account, for a caregiver handling several people.
- A multi-case dashboard for professional patient advocates (brief §2, "later").
- An offline state for the workspace, beyond the per-surface error states.
- The remaining designed email templates: extraction complete, letter ready.
- An accordion height animation, and the `MarginNote` connector hairline.
