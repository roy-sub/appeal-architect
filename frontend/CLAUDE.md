# Appeal Architect — frontend

Consumer web app that helps a person fight a health-insurance denial. It works out the
appeal track and deadlines, with the rule behind each. It builds the counter-arguments
against the insurer's stated reason, then writes the appeal letter from the arguments that
hold. Read `design-handoff/project/uploads/Appeal Design Brief.md` before any product decision.

## Commands

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # static export → out/
npm run lint         # eslint (flat config)
npm run typecheck    # tsc --noEmit
npm run export:data  # regenerate backend/app/data.py from lib/case-data.ts
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
  triage/page.tsx               Free triage: 4 questions → track, deadline, honest verdict
  (workspace)/layout.tsx        Authenticated shell: rail (desktop) / bottom bar (mobile)
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
  reveal.tsx                    The one animation wrapper (see Motion)
  media-slot.tsx                Deferred-asset placeholder (roomy / tight / fill)
  deadline-ring.tsx, status-pill.tsx
lib/
  case-data.ts                  Demo case (single source; backend copy is generated)
  landing-content.ts            Landing copy
  motion.ts                     Easings, durations, named gestures
  time.ts                       Deadline tone thresholds
  site.ts                       Fixed strings: disclaimer, rules stamp
design-handoff/                 Original Claude Design export. Reference only, not built.
```

## Sources of truth, in priority order

1. `design-handoff/project/Appeal Architect.dc.html`: the final prototype. Visual values
   (px sizes, spacing, colours) were taken from it exactly.
2. `design-handoff/chats/chat1.md`: the user's decisions while iterating (light mode only,
   forest/clay palette, landing redesign, "how it works" desktop fix).
3. `design-handoff/project/components.md`, `motion.md`, `media-manifest.md`: behaviour
   specs. Where they disagree with the prototype on visuals, the prototype wins.
4. `design-handoff/project/design-plan.md`: its palette section is **outdated** (it predates
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
- **Case data** is demo data in `lib/case-data.ts`. After editing it, run `npm run export:data`.

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

- **Deadline arithmetic in the copy is wrong.** 180 days after 14 Sep 2026 is **13 Mar
  2027**, not "22 Mar 2027 / 168 days" as the prototype shows everywhere (header pill,
  roadmap, triage, letter, `case-data.ts`). The backend computes 13 Mar. Fix the copy and
  data together.
- The stats band shows units ("%", "days") that the prototype omitted ("0.2 of denied claims").
- Triage page got the prototype's standard margins (its style key was undefined there).
- "Build my roadmap" is gated until every fact is resolved (the brief requires it; the
  prototype did not).
- Media ratios follow the prototype, which differs from `media-manifest.md` (features 16/10
  vs 4/3; personas 4/5, 4/3, 1/1 vs all 4/3). Pick one when real assets arrive.
- Triage verdict is static copy whatever the answers; wire to `POST /api/triage`.
- Export DOCX and Download template are inert; Export PDF uses `window.print()`.
- Upload inputs open the picker or camera but process nothing.
- The argument graph is hand-laid-out per the prototype. The brief mentions React Flow;
  not needed at the current graph size.
- Footer legal links (`#terms`, `#privacy`, `#rules`) point nowhere yet.
- Not yet placed: `trust-strip`, `graph-legend`, `letter-preview`, `og-card` slots.
- Spec components not yet built: `Field` (no-red error state), `DestructiveDialog`, toasts,
  `MarginNote` connector hairline, accordion height animation.

## Next build (brief §6, deferred by the user's scope answer)

Pricing page · Legal (terms, plain-language privacy, full disclaimer, rules changelog) ·
Sign in / sign up (email magic link; say what happens to documents) · Case timeline ·
Escalation (external review flow) · Settings (profile, dependants, notifications, billing,
**delete my data**) · loading / empty / error / offline states for every data surface ·
toasts, modals, destructive confirmation · email templates (magic link; deadline reminders
at 30/14/7/3/1 days; extraction complete; letter ready) · 404 and 500.

Then: replace `lib/case-data.ts` reads with calls to `../backend` (see `backend/README.md`).
