"""Every error leaves as problem+json with a machine-readable code.

The frontend branches on ``code``, so the codes are a contract: copy in
``detail`` can be rewritten freely, ``code`` cannot.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.problem import (
    CONTENT_TYPE,
    ErrorCode,
    Problem,
    facts_not_confirmed,
    service_not_configured,
)


def test_problem_renders_rfc7807_shape() -> None:
    p = Problem(404, ErrorCode.NOT_FOUND, "We could not find that case.")
    body = p.to_response().body.decode()
    assert '"code":"not_found"' in body
    assert '"status":404' in body
    assert '"type":"https://appealarchitect.app/problems/not_found"' in body


def test_every_error_code_has_a_title() -> None:
    """A code with no title would render 'Error' at the user. Catch it here."""
    from app.problem import _TITLES

    missing = [c.value for c in ErrorCode if c not in _TITLES]
    assert not missing, f"ErrorCode members without a title: {missing}"


def test_service_not_configured_names_the_env_vars() -> None:
    """The error has to be actionable: it says which variables to set."""
    p = service_not_configured("Supabase", env_vars=["SUPABASE_URL"])
    assert p.status_code == 503
    assert "SUPABASE_URL" in p.detail
    assert p.extra["missing_env"] == ["SUPABASE_URL"]


def test_facts_not_confirmed_is_409_and_lists_what_is_pending() -> None:
    """Spec 10: POST /cases/{id}/route is a 409 when facts are unconfirmed.

    The pending field names come back so the UI can send the user to them
    instead of making them hunt.
    """
    p = facts_not_confirmed(["denial_date", "plan_type"])
    assert p.status_code == 409
    assert p.code is ErrorCode.FACTS_NOT_CONFIRMED
    assert p.extra["pending_fields"] == ["denial_date", "plan_type"]


def test_no_error_copy_uses_an_exclamation_mark() -> None:
    """House voice: the app never gushes and never apologises at volume."""
    from app.problem import _TITLES

    for code, title in _TITLES.items():
        assert "!" not in title, f"{code.value} title uses an exclamation mark"


@pytest.mark.parametrize("status", [401, 403, 404, 409, 429])
def test_framework_http_errors_are_also_problem_json(client: TestClient, status: int) -> None:
    """FastAPI's own HTTPExceptions are converted too.

    Without the handler, a router-raised 404 returns a bare {"detail": ...} and
    the frontend has two error shapes to parse.
    """
    from fastapi import HTTPException

    app = client.app

    @app.get(f"/_test/raise/{status}")
    async def _raise() -> None:  # pragma: no cover -- exercised via the request
        raise HTTPException(status_code=status, detail="deliberate")

    r = client.get(f"/_test/raise/{status}")
    assert r.status_code == status
    assert r.headers["content-type"].startswith(CONTENT_TYPE)
    assert "code" in r.json()
