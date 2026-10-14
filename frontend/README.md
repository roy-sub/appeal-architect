# Appeal Architect — frontend

Next.js 15 App Router, compiled to a **static export**. Every screen's data comes
from the backend API, so there is no SSR, no server actions and no Node process
in production — the whole application is a folder of files on a CDN.

Implementation of `../design/project/Appeal Architect.dc.html`, the Claude Design
handoff, which is the visual authority for this half of the system.

---

## Contents

1. [Commands](#commands)
2. [Environment](#environment)
3. [Stack](#stack)
4. [Layout](#layout)
5. [Routes, and what each one reads](#routes-and-what-each-one-reads)
6. [The API client](#the-api-client)
7. [Authentication](#authentication)
8. [Design tokens](#design-tokens)
9. [Motion](#motion)
10. [Media](#media)
11. [The argument graph](#the-argument-graph)
12. [Product rules that must not break](#product-rules-that-must-not-break)
13. [Build output](#build-output)
14. [Known limits](#known-limits)

---

## Commands

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # static export -> out/
npm run lint         # eslint, flat config
npm run typecheck    # tsc --noEmit
npm run check:tokens # fails if the palette has drifted from /design
npm start            # serve the built out/ locally
```

Node 20.9 or later; `.nvmrc` pins 22.

## Environment

Three files, and each is read by something different:

| File | Read by | Purpose |
|---|---|---|
| `.env.local` | `npm run dev` | Points at a local backend |
| `.env.production.local` | `npm run build` | Points at the deployed backend |
| `../.env` (repo root) | **nothing** | The master copy of every value, both halves |

Next loads `.env.production.local` **ahead of** `.env.local`, so the production
file wins for a build while `.env.local` still drives the dev server. You cannot
accidentally ship a localhost build. The build prints which files it used:

```
- Environments: .env.production.local, .env.local
```

Four variables, all compiled into the bundle at build time:

| Variable | What breaks without it |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Sign-in says the app is not set up on this copy |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Same |
| `NEXT_PUBLIC_API_URL` | Every screen says it cannot reach the server — it would be calling `localhost:8000` from the visitor's machine |
| `NEXT_PUBLIC_SITE_URL` | **Silent.** The share card, the canonical link and the sitemap all point at localhost, so posted links preview blank |

`NEXT_PUBLIC_*` is compiled in and is public by definition. The Supabase `anon`
key belongs here and is safe — row-level security is what protects the data. The
`service_role` key must never appear in one.

Changing any of these requires a **rebuild**. Editing a dashboard variable and
reloading the page does nothing.

## Stack

Tailwind CSS v4 (CSS-first config in `app/globals.css`; there is no
`tailwind.config.ts`), shadcn-style primitives on Radix in `components/ui/`,
Motion (`motion/react`) for every animation, TanStack Query for server state, and
`next/font` for IBM Plex Sans, IBM Plex Mono and Newsreader.

## Layout

```
app/
  page.tsx                      Landing (sections in components/landing/)
  layout.tsx                    Fonts, metadata, the share card, metadataBase
  providers.tsx                 TanStack Query + AuthProvider
  globals.css                   Tokens (:root) + @theme mapping + print + reduced motion
  robots.ts  sitemap.ts         Generated as static files at build time
  triage/                       Free triage: 4 questions -> track, deadline, verdict
  (auth)/signin/                Magic link; says what happens to their documents
  (auth)/auth/callback/         Where the magic link lands (client-side, no server)
  (workspace)/layout.tsx        Authenticated shell + AuthGate
  (workspace)/cases/            Case list + empty state
  (workspace)/case/documents/   Upload and camera capture
  (workspace)/case/facts/       Extraction review, each fact beside its source span
  (workspace)/case/roadmap/     Procedural roadmap + the rule drawer
  (workspace)/case/arguments/   The argument graph
  (workspace)/case/evidence/    Evidence checklist + physician-letter points
  (workspace)/case/letter/      Letter with paragraph -> argument backlinks
  (workspace)/case/timeline/    The record, plus escalation
  (workspace)/settings/         Account, entitlement, the real hard delete
  legal/  pricing/              Terms, privacy in plain language, rules changelog
  not-found.tsx                 404

components/
  ui/                           button (cva variants), accordion, sheet
  landing/                      hero.tsx (nav, hero, marquee), sections.tsx, faq.tsx
  workspace/shell.tsx           AppShell, CaseHeader, PageHead, shared class atoms
  workspace/auth-gate.tsx       Client-side guard; a static export has no middleware
  workspace/case-context.tsx    Active case, shared across workspace screens
  workspace/states.tsx          Loading, empty, error, named stages, warning banners
  workspace/buy-button.tsx      The one path to Stripe Checkout
  workspace/not-configured.tsx  Shown when the backend is not wired up
  domain/argument-node.tsx      The argument card in all four tiers
  domain/argument-graph.tsx     React Flow + dagre; lazy-loaded, desktop only
  media-slot.tsx                Renders a shipped asset, or its designed placeholder
  reveal.tsx                    The one animation wrapper
  deadline-ring.tsx  status-pill.tsx

lib/
  api.ts                        The whole API surface: types, problem+json, warming state
  hooks.ts                      One hook per endpoint
  query-keys.ts                 One key factory, so invalidation is not guesswork
  auth.tsx                      Session context, magic-link sign-in
  supabase.ts                   Browser auth client
  media.ts                      Which assets have shipped, and their real pixel sizes
  motion.ts                     Easings, durations, named gestures
  time.ts                       Deadline tone thresholds
  site.ts                       Fixed strings: disclaimer, rules stamp
  site-url.ts                   Where this build will live
  landing-content.ts            Landing copy
```

`CLAUDE.md` in this directory holds the same conventions in the form an agent
reads them, and goes further on the product rules.

## Routes, and what each one reads

Every screen reads the API. There is no demo data and no fallback: a screen that
cannot reach the backend says so rather than showing something plausible.

| Route | Reads |
|---|---|
| `/` | static |
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

The triage options come from the backend's own enums, so the four questions
cannot drift from what the API accepts.

## The API client

`lib/api.ts` is the entire surface: one typed wrapper per endpoint, with request
and response types written beside the call. It is hand-written rather than
generated from the OpenAPI schema, because it carries three behaviours the schema
cannot express:

- **One error shape.** Every non-2xx response becomes an `ApiError` carrying the
  parsed problem+json, including a sane fallback when the body is not JSON at
  all.
- **Bearer tokens.** Attached from the Supabase session, except where a call is
  explicitly `anonymous` (triage).
- **Cold-start detection.** The backend sleeps on its free tier. A request that
  exceeds the warming timeout aborts and surfaces `backend_warming`, so the UI
  can say "still waking up, this can take a minute" instead of showing a network
  error.

`lib/hooks.ts` wraps each of those in TanStack Query — one hook per endpoint, no
ad-hoc fetching in components — and `lib/query-keys.ts` is the single key factory,
so a mutation invalidates exactly what it could have changed.

The active case id lives in `localStorage`, because this is a static export with
no server session and the workspace routes are fixed paths rather than
`/case/[id]/…`. Switching case is explicit.

## Authentication

Magic link through Supabase Auth. `lib/auth.tsx` holds the session;
`components/workspace/auth-gate.tsx` guards the workspace on the client, because
a static export has no middleware.

The callback URL is built from `window.location.origin`, so it works on any
origin without rebuilding — but the exact URL, **with its trailing slash**, has to
be in Supabase's redirect allow-list. `next.config.ts` sets
`trailingSlash: true`, so `/auth/callback` without the slash is a 404 and the
sign-in link looks broken.

## Design tokens

Tokens live in `app/globals.css` under `:root` and are exposed to Tailwind through
`@theme inline` (`bg-ground`, `text-ink-muted`, `border-standing`, …). Never write
a raw hex value in a component.

`npm run check:tokens` compares them against `../design/project/tokens.css` and
fails on drift, with an explicit allow-list for documented omissions and
additions. Tailwind's default spacing scale is *not* overridden; design values are
arbitrary px (`text-[17px] leading-[29px]`) to stay pixel-exact with the
prototype.

Radii: marketing surfaces 2px (sharp); workspace cards 16px; buttons 10px / 8px.

Light mode only. The build spec asked for a theme switch; the design chat removed
dark mode by explicit instruction, and appearance is design's authority.

## Motion

Everything animates through `<Reveal gesture=… trigger="view"|"load">` or Motion
directly with the `ease` / `dur` values from `lib/motion.ts`. Only transform,
opacity and clip-path animate.

Each landing section owns one gesture and no gesture is reused across sections.
An element that starts fully clipped needs `wrapClassName`, because
IntersectionObserver cannot see a fully clipped element. `instant` renders the end
state. Reduced motion is honoured by rendering content with no entrance at all,
not by shortening the duration.

## Media

Every image goes through `<MediaSlot>` with its slot id, aspect ratio and
intrinsic size. A slot id listed in `lib/media.ts` renders its file; one that is
not renders the designed placeholder. Both occupy the same box, so adding or
removing a file never moves the layout.

Twelve slot assets plus the 1200×630 share card live in `public/media/`, sized to
what they actually render at. Ratios follow `lib/media.ts`, which records what was
generated, rather than `../design/project/media-manifest.md`, where the two
disagree. Slot ids show in dev only, or with `NEXT_PUBLIC_SHOW_SLOTS=1`.

Plain `<img>`, not `next/image`: the build is a static export with
`images.unoptimized`, so `next/image` would emit the same tag with extra markup
around it. Sizes come from the manifest so the box is reserved before the bytes
land.

## The argument graph

`components/domain/argument-graph.tsx` renders the solver's output with React Flow
and dagre, lazy-loaded through `next/dynamic` with `ssr: false` so its ~70 kB
never reaches a phone. Mobile renders stacked lanes instead — not a fallback, the
better reading on a small screen.

Hand-placement was tried first and only worked for one fixed set of nodes; the
solver produces varying shapes, so the layout has to be computed.

The four tiers never rely on colour alone:

| Tier | Border | Marker |
|---|---|---|
| Solid ground | solid, 3px standing edge | ● |
| Worth adding | dashed | ◇ |
| Left out | hatch, strikethrough | ✕ |

## Product rules that must not break

- **Fixed strings, verbatim.** "Appeal Architect" · "Your denial, formally
  refuted." · "Every paragraph backed by a rule." · the disclaimer in
  `lib/site.ts` (footer and every letter) · "Rules current as of {date} · version
  {v}" on every route determination · the tier labels "Solid ground" and "Worth
  adding".
- **Never imply an outcome.** No "guaranteed", "we'll win", "fight back",
  "loophole", "hack", "secret"; no war metaphors; no confetti, trophies or
  check-burst success states.
- **Copy:** grade-8 plain language, active voice, no exclamation marks, never
  apologises or gushes.
- **No red anywhere**, including errors. Errors use `--ink` plus a bar and an
  instruction.
- **Deadlines calm, never alarming.** Tone by proximity only (`lib/time.ts`; no
  hue above 60 days). Never animate a countdown or a ring after its entrance.
- **Colour never carries meaning alone.**
- **Dates.** The frontend does no date arithmetic beyond "days until". Every
  deadline is computed server-side and rendered as returned, with the rule it came
  from and its ambiguity note.
- **Accessibility floor:** AA contrast, visible focus (global `:focus-visible`,
  clay), 44px minimum touch targets, reduced motion honoured, and a disabled
  button always states its reason beside it.
- **Mobile is first-class.** Desktop switches on at `lg` (1024px). Design targets
  are 390 and 1440.

## Build output

`npm run build` writes `out/`, which is the deployable artifact in full:

```
out/
├── index.html  triage/  signin/  cases/  case/…  legal/  pricing/  404.html
├── _next/static/…        content-hashed JS, CSS and fonts
├── media/                the twelve assets and the share card
├── _headers              security headers and cache lifetimes, read by Cloudflare Pages
├── robots.txt            keeps the signed-in screens out of the index
└── sitemap.xml           the five public pages
```

`public/_headers` sets `nosniff`, `X-Frame-Options: DENY`, a permissions policy,
HSTS, and a referrer policy that drops to `no-referrer` on the case screens so a
health-related path never leaves in a `Referer` header. There is deliberately no
Content-Security-Policy: a correct one has to name the real Supabase and API
origins, and a wrong one breaks the site silently.

Verify a build before deploying it:

```bash
grep -o 'og:image" content="[^"]*"' out/index.html   # the real domain, not localhost
grep -rl 'localhost:8000' out/ || echo "api url ok"
grep -rl 'service_role' out/ || echo "clean"
```

Deployment, including the Cloudflare Pages and DNS steps, is in
[`../docs/DEPLOY.md`](../docs/DEPLOY.md).

## Known limits

- **No JavaScript means no content.** Motion renders `initial="hidden"` into the
  prerendered HTML, so a visitor with JS disabled sees an empty page. The text is
  in the DOM for crawlers, which execute JS; a progressive-enhancement pass would
  be a real change, not a tweak.
- **`feature-roadmap`** carries generic captions rather than this product's words.
  Rewriting them would put specific deadline arithmetic into a picture, which is
  the one thing the rulebase is not allowed to do casually, so it stands as
  generated.
- **`trust-strip` and `graph-legend`** from the design manifest were dropped
  deliberately. The landing page states the privacy position in words and links to
  `/legal` rather than showing a strip of security badges, and the argument graph
  carries its legend on the page itself, where it cannot be dismissed and lost.
- **Spec components not built as standalone pieces**, because the screens that
  needed them implement the behaviour inline: `Field` (the no-red error state is in
  `components/workspace/states.tsx`), `DestructiveDialog` (the type-the-phrase
  delete flow on `/settings`), toasts (mutations report inline, beside the thing
  they changed), and the `MarginNote` connector hairline.
