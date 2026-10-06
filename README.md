# Appeal Architect

*Your denial, formally refuted.* A self-help tool for appealing a health-insurance denial.

- **frontend/**: Next.js 15 + Tailwind v4 + Radix/shadcn + Motion. Landing, free triage, case workspace.
- **backend/**: FastAPI scaffold with the triage rules and a demo case API. Not yet called by the frontend.

## Getting started

```bash
cd frontend && npm install && npm run dev                                         # http://localhost:3000
cd backend  && pip install -r requirements.txt && uvicorn app.main:app --reload   # http://localhost:8000/docs
```

Working with Claude Code: start with `CLAUDE.md`, then `frontend/CLAUDE.md`.

## Folder structure

```
appeal-architect/
├── backend/                          FastAPI scaffold
│   ├── app/
│   │   ├── __init__.py
│   │   ├── data.py                   Demo case data (generated from frontend/lib/case-data.ts)
│   │   ├── main.py                   API endpoints
│   │   └── rules.py                  Appeal tracks, deadline windows, regulation citations
│   ├── tests/
│   │   └── test_api.py
│   ├── .gitignore
│   ├── pyproject.toml
│   ├── README.md
│   └── requirements.txt
├── frontend/                         Next.js 15 static site
│   ├── app/
│   │   ├── (workspace)/              Authenticated case workspace
│   │   │   ├── case/
│   │   │   │   ├── arguments/
│   │   │   │   │   └── page.tsx      Argument graph
│   │   │   │   ├── documents/
│   │   │   │   │   └── page.tsx      Upload wizard
│   │   │   │   ├── evidence/
│   │   │   │   │   └── page.tsx      Evidence checklist
│   │   │   │   ├── facts/
│   │   │   │   │   └── page.tsx      Extraction review
│   │   │   │   ├── letter/
│   │   │   │   │   └── page.tsx      Appeal letter
│   │   │   │   └── roadmap/
│   │   │   │       └── page.tsx      Procedural roadmap + deadline drawer
│   │   │   ├── cases/
│   │   │   │   └── page.tsx          Case list
│   │   │   └── layout.tsx            Workspace shell (rail / mobile bar)
│   │   ├── triage/
│   │   │   └── page.tsx              Free triage check
│   │   ├── globals.css               Design tokens, Tailwind theme, print, reduced motion
│   │   ├── layout.tsx                Root layout + fonts
│   │   └── page.tsx                  Landing page
│   ├── components/
│   │   ├── landing/
│   │   │   ├── faq.tsx
│   │   │   ├── hero.tsx              Nav, hero, marquee
│   │   │   └── sections.tsx          Stats, process, capabilities, personas, pricing, CTA, footer
│   │   ├── ui/                       shadcn-style primitives
│   │   │   ├── accordion.tsx
│   │   │   ├── button.tsx
│   │   │   └── sheet.tsx
│   │   ├── workspace/
│   │   │   ├── case-context.tsx      Shared client case state
│   │   │   └── shell.tsx             AppShell, case header, shared atoms
│   │   ├── deadline-ring.tsx
│   │   ├── media-slot.tsx            Placeholder for deferred media
│   │   ├── motion-provider.tsx
│   │   ├── reveal.tsx                Animation wrapper
│   │   └── status-pill.tsx
│   ├── design-handoff/               Original Claude Design export (reference only)
│   │   ├── chats/
│   │   │   └── chat1.md              Design conversation
│   │   ├── project/
│   │   │   ├── screenshots/
│   │   │   │   └── how-desktop.png
│   │   │   ├── uploads/              Design brief + reference images
│   │   │   │   ├── Appeal Design Brief.md
│   │   │   │   ├── Design 2.jpeg
│   │   │   │   ├── pasted-1791203869928-0.png
│   │   │   │   ├── pasted-1791205050872-0.png
│   │   │   │   ├── pasted-1791205057712-0.png
│   │   │   │   ├── pasted-1791212315972-0.png
│   │   │   │   ├── pasted-1791212368295-0.png
│   │   │   │   ├── Screenshot 2026-10-05 8.28.33 PM.png
│   │   │   │   └── Screenshot 2026-10-05 8.29.26 PM.png
│   │   │   ├── .thumbnail
│   │   │   ├── Appeal Architect.dc.html   Final prototype (visual source of truth)
│   │   │   ├── components.md         Component spec
│   │   │   ├── design-plan.md
│   │   │   ├── media-manifest.md     Every media slot: id, ratio, size
│   │   │   ├── MediaSlot.dc.html
│   │   │   ├── motion.md             Motion spec
│   │   │   ├── support.js            Prototype runtime
│   │   │   ├── tailwind.theme.ts
│   │   │   └── tokens.css
│   │   └── README.md
│   ├── lib/
│   │   ├── case-data.ts              Demo case data (single source)
│   │   ├── landing-content.ts        Landing page copy
│   │   ├── motion.ts                 Easings, durations, gestures
│   │   ├── site.ts                   Fixed strings (disclaimer, rules stamp)
│   │   ├── time.ts                   Deadline tone thresholds
│   │   └── utils.ts
│   ├── public/
│   │   └── media/
│   │       └── README.md             Where real images and video go
│   ├── scripts/
│   │   └── export-case-data.mts      Regenerates backend/app/data.py
│   ├── .gitignore
│   ├── .nvmrc
│   ├── CLAUDE.md                     Handoff guide: rules, conventions, status, next build
│   ├── components.json
│   ├── eslint.config.mjs
│   ├── next.config.ts
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.mjs
│   ├── README.md
│   └── tsconfig.json
├── .gitignore
├── CLAUDE.md
└── README.md
```
