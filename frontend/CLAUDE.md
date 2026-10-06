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
  globals.css                   Tokens (:root) + @theme mapping + print + reduced motion
components/
  ui/                           button (cva variants), accordion, sheet
  landing/                      hero.tsx (nav, hero, marquee), sections.tsx, faq.tsx
  workspace/shell.tsx           AppShell, CaseHeader, PageHead, shared class atoms
  workspace/case-context.tsx    Client case state shared across workspace screens
  workspace/auth-gate.tsx       Client-side guard (static export has no middleware)
  workspace/not-configured.tsx  Notice shown when the backend is not wired up
  reveal.tsx                    The one animation wrapper (see Motion)
  media-slot.tsx                Deferred-asset placeholder (roomy / tight / fill)
  deadline-ring.tsx, status-pill.tsx
lib/
  api.ts                        Typed backend client: bearer token, problem+json, warming state
  supabase.ts                   Browser auth client
  auth.tsx                      Session context, magic-link sign-in
  query-keys.ts                 One key factory, so invalidation is not guesswork
  case-data.ts                  Demo case. Still read by the screens that are not
                                yet wired to the API; deleted in phase 5.
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
- **Case data.** The case list reads the API through `lib/api.ts`. The other eight
  screens still read demo data from `lib/case-data.ts`; phase 5 replaces those reads.
  No screen reads both — demo data is not a fallback for a failed request.
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

### Known issues and decisions to confirm

- **Deadline arithmetic in the copy is wrong — and it is the dangerous direction.**
  The prototype says 22 Mar 2027 / 168 days everywhere (header pill, roadmap, triage,
  letter, `case-data.ts`). 180 days after 14 Sep 2026 is **13 Mar 2027**. The copy is
  9 days late, so someone trusting it could file after their window closed.
  Resolved in `PLAN.md` §3.2: the engine computes the date and the copy renders what
  it returns. There is a second layer — the rule counts from *receipt*, the prototype
  counts from the letter date, and the regulation does not settle which — so the real
  answer is a conservative date plus an ambiguity note, not a confident single date.
  The RuleDrawer copy needs rewriting to say so. Phase 5.
- The stats band shows units ("%", "days") that the prototype omitted ("0.2 of denied claims").
- Triage page got the prototype's standard margins (its style key was undefined there).
- "Build my roadmap" is gated until every fact is resolved (the brief requires it; the
  prototype did not).
- Media ratios follow the prototype, which differs from `media-manifest.md` (features 16/10
  vs 4/3; personas 4/5, 4/3, 1/1 vs all 4/3). Resolved in `PLAN.md` §3.6: take the
  manifest, which was re-synced later in the design chat than the prototype was last
  touched. Not yet applied to the slots.
- Triage verdict is static copy whatever the answers; wire to `POST /api/v1/public/triage` (phase 7).
- Export DOCX and Download template are inert; Export PDF uses `window.print()`.
- Upload inputs open the picker or camera but process nothing.
- The argument graph is hand-laid-out per the prototype. Resolved in `PLAN.md` §3.3:
  React Flow + dagre for structure (it must lay out arbitrary solver output, not a fixed
  set of six nodes), the prototype's exact visual for every node, lane and connector.
  Phase 5.
- Footer legal links (`#terms`, `#privacy`, `#rules`) point nowhere yet.
- Not yet placed: `trust-strip`, `graph-legend`, `letter-preview`, `og-card` slots.
- Spec components not yet built: `Field` (no-red error state), `DestructiveDialog`, toasts,
  `MarginNote` connector hairline, accordion height animation.

### Wired to the backend so far

- **Sign in / sign up** (`/signin/`) and the magic-link callback.
- **The case list** reads `GET /api/v1/cases`, with a real empty state, a loading
  skeleton, and a warming state for the free-tier backend's cold start.
- `AuthGate` guards the workspace. With no Supabase keys configured the screens
  still render and show an explicit notice, so the design work stays inspectable
  without a backend.
- No theme switch, and no dark palette. The build spec's phase 1 asks for one;
  the design chat removed dark mode by explicit instruction, and appearance is
  design's authority. See `PLAN.md` §3.1.

## Next build (brief §6, deferred by the user's scope answer)

Pricing page · Legal (terms, plain-language privacy, full disclaimer, rules changelog) ·
Sign in / sign up (email magic link; say what happens to documents) · Case timeline ·
Escalation (external review flow) · Settings (profile, dependants, notifications, billing,
**delete my data**) · loading / empty / error / offline states for every data surface ·
toasts, modals, destructive confirmation · email templates (magic link; deadline reminders
at 30/14/7/3/1 days; extraction complete; letter ready) · 404 and 500.

Then phase 5: replace the remaining `lib/case-data.ts` reads with API calls through
`lib/api.ts`, and delete the demo data.
