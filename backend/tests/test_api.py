from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["ok"] is True


def test_triage_employer_deadline_is_180_days_from_letter():
    r = client.post("/api/triage", json={"source": "employer", "letter_date": "2026-09-14"}).json()
    assert r["deadline"] == "2027-03-13"
    assert r["rule"].startswith("29 C.F.R.")


def test_triage_unknown_plan_does_not_guess():
    r = client.post("/api/triage", json={"source": "unsure"}).json()
    assert r["track"] is None and r["deadline"] is None


def test_cases_sorted_by_urgency():
    days = [c["days"] for c in client.get("/api/cases").json()]
    assert days == sorted(days)


def test_demo_case_has_all_tiers():
    tiers = {a["tier"] for a in client.get("/api/cases/CLM-4471902").json()["arguments"]}
    assert tiers == {"solid", "add", "out"}
