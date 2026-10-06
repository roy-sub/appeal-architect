"""/healthz, and the problem+json contract."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.problem import CONTENT_TYPE, ErrorCode


def test_healthz_is_ok_with_nothing_configured(client: TestClient) -> None:
    """A fresh clone with no .env still answers.

    Someone who has just cloned the repo should get a running app and a clear
    account of what is missing, not a stack trace on startup.
    """
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["rulebase_version"]
    assert body["services"] == {
        "supabase": False,
        "anthropic": False,
        "email": False,
        "stripe": False,
        "reminders": False,
    }


def test_healthz_reports_configured_services(configured_client: TestClient) -> None:
    body = configured_client.get("/healthz").json()
    assert body["services"]["supabase"] is True
    assert body["services"]["anthropic"] is False


def test_healthz_leaks_no_secret_values(configured_client: TestClient) -> None:
    """The status map carries booleans only -- never a key, never a URL."""
    raw = configured_client.get("/healthz").text
    assert "service-role-key" not in raw
    assert "test-secret-not-a-real-one" not in raw


def test_unknown_route_is_problem_json(client: TestClient) -> None:
    r = client.get("/no-such-thing")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith(CONTENT_TYPE)
    body = r.json()
    assert body["code"] == ErrorCode.NOT_FOUND.value
    assert body["status"] == 404
    assert body["title"] and body["detail"]


def test_docs_are_served_in_development(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
