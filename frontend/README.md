# Appeal Architect — web

Implementation of `../design/project/Appeal Architect.dc.html` (Claude Design
handoff). Next.js 15 App Router, static export · Tailwind v4 · shadcn-style
primitives (Radix) · Motion.

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # static site in out/
npm run lint && npm run typecheck
npm run check:tokens # fails if the palette has drifted from /design
```

Conventions, product rules, status and known issues: **`CLAUDE.md`**.
The architecture and the LLM boundary: **`../docs/ARCHITECTURE.md`**.

| Route | Screen | Data |
|---|---|---|
| `/` | Landing | static copy |
| `/triage/` | Free triage (4 questions → track, deadline, honest verdict) | static — wires up in phase 7 |
| `/signin/` | Magic link; says what happens to their documents | Supabase Auth |
| `/auth/callback/` | Where the magic link lands | Supabase Auth |
| `/cases/` | Case list + empty state | `GET /api/v1/cases` |
| `/case/documents/` | Upload wizard | demo |
| `/case/facts/` | Extraction review (+ "working" stages) | demo |
| `/case/roadmap/` | Procedural roadmap + deadline drawer | demo |
| `/case/arguments/` | Argument graph (lanes on desktop, inline expansion on mobile) | demo |
| `/case/evidence/` | Evidence checklist + physician-letter points | demo |
| `/case/letter/` | Letter with paragraph → argument backlinks; prints on US Letter | demo |

"demo" means the screen still reads `lib/case-data.ts`. Phase 5 replaces those
reads with engine output through `lib/api.ts`. No screen reads both — demo data
is not a fallback for a failed request.

- **Tokens:** `app/globals.css`. The `:root` values mirror
  `../design/project/tokens.css`, and `@theme inline` exposes them to Tailwind.
  Tailwind v4 is CSS-first, so there is no `tailwind.config.ts`;
  `npm run check:tokens` is what stops the two drifting apart.
- **Motion:** one gesture per landing section in `lib/motion.ts`, played by
  `components/reveal.tsx`. Reduced motion shows content instantly.
- **Media:** `components/media-slot.tsx` reserves every slot from
  `../design/project/media-manifest.md`. Slot ids show in dev only, or with
  `NEXT_PUBLIC_SHOW_SLOTS=1`.
- **Data:** `lib/api.ts` (typed client, bearer token, problem+json, cold-start
  warming state), `lib/auth.tsx` (session), `lib/query-keys.ts` (cache keys).
  Landing copy is in `lib/landing-content.ts`.

Environment: copy `../.env.example` to `.env.local` and fill the frontend block.
Without it the app still runs — the data screens show an explicit notice instead
of breaking. The four values and where to find them are in `../docs/DEPLOY.md`.
