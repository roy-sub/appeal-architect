# Appeal Architect — web

Implementation of `project/Appeal Architect.dc.html` (Claude Design handoff).
Next.js 15 App Router, static export · Tailwind v4 · shadcn-style primitives (Radix) · Motion.

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # static site in out/
npm run lint && npm run typecheck
npm run export:data  # regenerate backend/app/data.py from lib/case-data.ts
```

Conventions, product rules, status and known issues: **`CLAUDE.md`**.

| Route | Screen |
|---|---|
| `/` | Landing |
| `/triage/` | Free triage (4 questions → track, deadline, honest verdict) |
| `/cases/` | Case list (+ empty state toggle) |
| `/case/documents/` | Upload wizard |
| `/case/facts/` | Extraction review (+ "working" stages) |
| `/case/roadmap/` | Procedural roadmap + deadline drawer |
| `/case/arguments/` | Argument graph (lanes on desktop, inline expansion on mobile) |
| `/case/evidence/` | Evidence checklist + physician-letter points |
| `/case/letter/` | Letter with paragraph → argument backlinks; prints on US Letter |

- Tokens: `app/globals.css` (`:root` values mirror `project/tokens.css`; `@theme inline` exposes them to Tailwind).
- Motion: one gesture per landing section in `lib/motion.ts`, played by `components/reveal.tsx`; reduced motion shows content instantly.
- Media: `components/media-slot.tsx` reserves every slot from `project/media-manifest.md`; slot ids show in dev only (or `NEXT_PUBLIC_SHOW_SLOTS=1`).
- Demo case data: `lib/case-data.ts`, landing copy: `lib/landing-content.ts`.
