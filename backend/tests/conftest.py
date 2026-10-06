"""Shared fixtures.

The app is built with no services configured, which is the state a developer who
has just cloned the repo is in. Tests that need a configured service say so.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# Clear inherited configuration before app import so a developer's own .env
# cannot change what the tests assert.
for _var in (
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "ANTHROPIC_API_KEY",
    "RESEND_API_KEY",
    "FROM_EMAIL",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "INTERNAL_JOB_SECRET",
):
    os.environ.pop(_var, None)
os.environ["ENV"] = "development"


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def jwt_secret() -> str:
    # 32+ bytes: pyjwt warns below that for HS256, and a warning in every test run
    # trains people to ignore warnings.
    return "test-secret-not-a-real-one-0123456789abcdef"


@pytest.fixture
def configured_client(monkeypatch: pytest.MonkeyPatch, jwt_secret: str) -> Iterator[TestClient]:
    """An app with Supabase settings present (but no live Supabase behind them)."""
    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", jwt_secret)
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()


@pytest.fixture
def bearer(jwt_secret: str):
    """Mint a valid Supabase-shaped access token for a given user id."""
    import datetime

    import jwt as pyjwt

    def _make(user_id: str = "11111111-1111-1111-1111-111111111111", **overrides) -> str:
        now = datetime.datetime.now(tz=datetime.UTC)
        claims = {
            "sub": user_id,
            "aud": "authenticated",
            "role": "authenticated",
            "email": "person@example.com",
            "iat": now,
            "exp": now + datetime.timedelta(hours=1),
        }
        claims.update(overrides)
        return pyjwt.encode(claims, jwt_secret, algorithm="HS256")

    return _make
