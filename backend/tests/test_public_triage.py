"""The free triage tool.

It calls the same rules engine as the paid route. There is no looser code path
for the free tool: a deadline shown to someone who has not signed up is as
consequential as one shown to someone who has.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


def _triage(client: TestClient, **overrides):
    payload = {
        "plan_type": "aca_marketplace",
        "state": "CA",
        "denial_date": "2026-09-14",
        "service_timing": "post",
        "denial_reason": "not_medically_necessary",
    }
    payload.update(overrides)
    return client.post("/api/v1/public/triage", json=payload)


def test_triage_needs_no_account(client: TestClient) -> None:
    assert _triage(client).status_code == 200


def test_triage_gives_the_real_deadline_with_its_rule(client: TestClient) -> None:
    body = _triage(client).json()
    deadline = body["deadline"]
    assert deadline["due_date"] == "2027-03-13"
    assert deadline["rule_id"] == "fed.internal_appeal.window"
    assert "45 CFR 147.136" in deadline["citation"]


def test_triage_discloses_the_ambiguous_trigger(client: TestClient) -> None:
    """The free tool is as honest as the paid one about what it does not know."""
    deadline = _triage(client).json()["deadline"]
    assert deadline["ambiguous"] is True
    assert deadline["ambiguity_note"]
    assert "earlier" in deadline["ambiguity_note"]


def test_triage_names_the_review_levels(client: TestClient) -> None:
    body = _triage(client).json()
    assert body["levels"] == ["Internal appeal", "Independent external review"]
    assert body["track"] and "external review" in body["track"]


def test_triage_refuses_to_guess_an_unsupported_plan(client: TestClient) -> None:
    """A guessed track sends someone to the wrong reviewer with the wrong form."""
    body = _triage(client, plan_type="medicaid").json()
    assert body["track"] is None
    assert body["levels"] == []
    assert body["warnings"]


def test_triage_without_a_letter_date_gives_no_date(client: TestClient) -> None:
    body = _triage(client, denial_date=None).json()
    assert body["deadline"] is None
    assert any("date on your letter" in w for w in body["warnings"])
    # Everything else still applies, and the tool says so.
    assert body["levels"]


def test_the_worth_it_answer_is_general_and_says_so(client: TestClient) -> None:
    """ "Half of appeals succeed" is a fact about appeals, not a prediction. The
    copy has to make that distinction, because the alternative is a promise."""
    body = _triage(client).json()
    worth = body["worth_appealing"]
    assert "not a prediction" in worth
    assert "nobody can give you one" in worth.lower()
    for banned in ("guaranteed", "you will win", "we'll win", "likely to win"):
        assert banned not in worth.lower()


def test_triage_reports_the_rulebase_version(client: TestClient) -> None:
    """So a user can tell which rules produced the answer they were given."""
    assert _triage(client).json()["rulebase_version"]


def test_urgency_shortens_the_insurers_clock_not_the_filing_window(
    client: TestClient,
) -> None:
    standard = _triage(client).json()
    urgent = _triage(client, is_urgent_medical=True).json()
    assert urgent["deadline"]["due_date"] == standard["deadline"]["due_date"]
    assert "Urgent external review" in urgent["levels"]


def test_a_future_denial_date_still_computes(client: TestClient) -> None:
    """Someone mistyping the year should get an answer, not a crash."""
    future = (date.today() + timedelta(days=30)).isoformat()
    response = _triage(client, denial_date=future)
    assert response.status_code == 200
    assert response.json()["deadline"]["days_remaining"] > 180


def test_options_drive_the_question_screens(client: TestClient) -> None:
    """Served from the enums, so the options cannot drift from what the engine
    accepts."""
    body = client.get("/api/v1/public/triage/options").json()
    assert {o["value"] for o in body["plan_types"]} == {
        "aca_marketplace",
        "employer_fully_insured",
        "employer_self_funded",
        "medicare_advantage",
        "medicaid",
        "unknown",
    }
    assert {o["value"] for o in body["service_timings"]} == {"pre", "post", "concurrent"}
    assert len(body["denial_reasons"]) == 7
    for group in ("plan_types", "service_timings", "denial_reasons"):
        for option in body[group]:
            assert option["label"] and "!" not in option["label"]


def test_a_bad_state_code_is_a_422(client: TestClient) -> None:
    assert _triage(client, state="California").status_code == 422


def test_rate_limiting_is_skipped_when_unconfigured(client: TestClient) -> None:
    """With no database there is nowhere to count, and the free tool still works
    locally. In production Supabase is always configured."""
    for _ in range(3):
        assert _triage(client).status_code == 200
