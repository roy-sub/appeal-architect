# Appeal Architect — backend

FastAPI scaffold. Serves the free triage check and the demo case the frontend renders.
**Not yet wired to the frontend**, which still reads `frontend/lib/case-data.ts`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # docs at http://localhost:8000/docs
pytest
```

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Liveness + rules version |
| `POST /api/triage` | `{source, letter_date?}` → track, deadline, rule citation |
| `GET /api/cases` | Cases sorted by days remaining |
| `GET /api/cases/{claim}` | Full case: facts, roadmap, arguments, evidence, letter |

- `app/rules.py` — appeal tracks, windows and the regulation behind each.
- `app/data.py` — demo data generated from `frontend/lib/case-data.ts` (`cd frontend && npm run export:data`); do not edit by hand.

Note: the triage endpoint computes deadlines correctly (14 Sep 2026 + 180 days = 13 Mar 2027); the frontend demo copy still says 22 Mar 2027 — see `frontend/CLAUDE.md`.

Not built yet: auth, document upload and extraction, the argument engine, letter generation, persistence, reminder emails.
