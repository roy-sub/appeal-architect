"""Authentication and user scoping.

The identity rule: ``user_id`` comes from the verified JWT and nowhere else.
Everything in this file is a test of that rule's edges.
"""

from __future__ import annotations

import datetime

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from app.problem import ErrorCode


def test_me_requires_a_token(configured_client: TestClient) -> None:
    r = configured_client.get("/api/v1/me")
    assert r.status_code == 401
    assert r.json()["code"] == ErrorCode.UNAUTHENTICATED.value


def test_me_returns_the_token_subject(configured_client: TestClient, bearer) -> None:
    uid = "22222222-2222-2222-2222-222222222222"
    r = configured_client.get("/api/v1/me", headers={"Authorization": f"Bearer {bearer(uid)}"})
    assert r.status_code == 200
    assert r.json() == {"id": uid, "email": "person@example.com"}


@pytest.mark.parametrize(
    "header",
    ["", "Bearer", "Basic abc", "token abc", "Bearer "],
)
def test_malformed_authorization_header_is_401(configured_client: TestClient, header: str) -> None:
    r = configured_client.get("/api/v1/me", headers={"Authorization": header})
    assert r.status_code == 401


def test_token_signed_with_the_wrong_secret_is_rejected(
    configured_client: TestClient,
) -> None:
    """The signature is actually checked. Without this the whole model is theatre."""
    now = datetime.datetime.now(tz=datetime.UTC)
    forged = pyjwt.encode(
        {
            "sub": "33333333-3333-3333-3333-333333333333",
            "aud": "authenticated",
            "iat": now,
            "exp": now + datetime.timedelta(hours=1),
        },
        "not-the-right-secret",
        algorithm="HS256",
    )
    r = configured_client.get("/api/v1/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_expired_token_is_rejected(configured_client: TestClient, bearer) -> None:
    past = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=2)
    token = bearer(exp=past, iat=past - datetime.timedelta(hours=1))
    r = configured_client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_with_wrong_audience_is_rejected(configured_client: TestClient, bearer) -> None:
    token = bearer(aud="anon")
    r = configured_client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_without_a_subject_is_rejected(
    configured_client: TestClient, jwt_secret: str
) -> None:
    now = datetime.datetime.now(tz=datetime.UTC)
    token = pyjwt.encode(
        {"aud": "authenticated", "iat": now, "exp": now + datetime.timedelta(hours=1)},
        jwt_secret,
        algorithm="HS256",
    )
    r = configured_client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_rejection_does_not_say_which_check_failed(configured_client: TestClient, bearer) -> None:
    """Expired and forged tokens get the same message.

    Telling an attacker that a token merely expired is free information.
    """
    past = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=2)
    expired = configured_client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {bearer(exp=past, iat=past)}"},
    ).json()
    forged = configured_client.get(
        "/api/v1/me", headers={"Authorization": "Bearer " + bearer(aud="anon")}
    ).json()
    assert expired["detail"] == forged["detail"]


def test_unconfigured_supabase_is_503_not_500(client: TestClient, bearer) -> None:
    """A fresh clone gets an actionable message naming the variables to set."""
    r = client.get("/api/v1/me", headers={"Authorization": "Bearer anything"})
    assert r.status_code == 503
    body = r.json()
    assert body["code"] == ErrorCode.SERVICE_NOT_CONFIGURED.value
    assert "SUPABASE_URL" in body["detail"]


def test_none_algorithm_token_is_rejected(configured_client: TestClient) -> None:
    """The classic JWT attack: alg=none with no signature.

    pyjwt is told HS256 only, so this must fail. Worth pinning explicitly.
    """
    now = datetime.datetime.now(tz=datetime.UTC)
    unsigned = pyjwt.encode(
        {"sub": "x", "aud": "authenticated", "iat": now, "exp": now + datetime.timedelta(hours=1)},
        key="",
        algorithm="none",
    )
    r = configured_client.get("/api/v1/me", headers={"Authorization": f"Bearer {unsigned}"})
    assert r.status_code == 401
