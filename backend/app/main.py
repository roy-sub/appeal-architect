"""Appeal Architect API (scaffold).

Serves the triage check and the demo case the frontend renders.
Not yet wired to the frontend, which still reads lib/case-data.ts.
"""
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import data, rules

app = FastAPI(title="Appeal Architect API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TriageRequest(BaseModel):
    source: Literal["employer", "marketplace", "medicare", "medicaid", "unsure"]
    letter_date: date | None = None


@app.get("/api/health")
def health():
    return {"ok": True, "rules_version": rules.RULES_VERSION}


@app.post("/api/triage")
def triage(req: TriageRequest):
    return rules.determine(req.source, req.letter_date, date.today())


@app.get("/api/cases")
def list_cases():
    # Sorted by how soon each case needs the user, not by when it was added.
    return sorted(data.CASES, key=lambda c: c["days"])


@app.get("/api/cases/{claim}")
def get_case(claim: str):
    case = next((c for c in data.CASES if c["claim"] == claim), None)
    if case is None:
        raise HTTPException(404, "Case not found")
    if claim != data.DEMO_CLAIM:
        return {"case": case}
    return {
        "case": case,
        "facts": data.FACTS,
        "roadmap": data.ROAD_STEPS,
        "claim": data.CLAIM,
        "arguments": data.ARGS,
        "evidence": data.EVIDENCE,
        "letter": data.LETTER_PARAS,
    }
