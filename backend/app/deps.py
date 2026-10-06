"""Request dependencies: authentication and user scoping.

The only source of identity is the verified JWT. ``user_id`` is read from the
token's ``sub`` claim after signature verification -- never from a path, query or
body parameter, which is what would let one account read another's case.
"""

from __future__ import annotations

import secrets
from typing import Annotated

import jwt
from fastapi import Depends, Header
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.db.client import SUPABASE_ENV_VARS
from app.problem import service_not_configured, unauthenticated

#: Supabase signs access tokens with HS256 against the project's JWT secret.
_ALGORITHMS = ["HS256"]
_AUDIENCE = "authenticated"

SettingsDep = Annotated[Settings, Depends(get_settings)]


class CurrentUser(BaseModel):
    """An authenticated caller. ``id`` comes from the verified token only."""

    id: str
    email: str | None = None


def _bearer(authorization: str | None) -> str:
    if not authorization:
        raise unauthenticated("Sign in to continue.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthenticated("Send the access token as 'Authorization: Bearer <token>'.")
    return token


async def current_user(
    # `settings` has no default, so it comes first -- FastAPI does not care about
    # parameter order, and this keeps the signature honest rather than using an
    # `= None` placeholder that is never actually None.
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Verify the bearer token and return the caller.

    Signature, expiry and audience are all checked. A token that fails any of
    those is a 401 with the same message whichever check failed -- telling an
    attacker that a token merely expired is free information.
    """
    if not settings.supabase_configured:
        raise service_not_configured("Supabase Auth", env_vars=SUPABASE_ENV_VARS)

    token = _bearer(authorization)
    try:
        claims = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=_ALGORITHMS,
            audience=_AUDIENCE,
        )
    except jwt.PyJWTError:
        raise unauthenticated("That session is no longer valid. Sign in again.") from None

    subject = claims.get("sub")
    if not subject or not isinstance(subject, str):
        raise unauthenticated("That session is no longer valid. Sign in again.")

    email = claims.get("email")
    return CurrentUser(id=subject, email=email if isinstance(email, str) else None)


CurrentUserDep = Annotated[CurrentUser, Depends(current_user)]


async def require_job_secret(
    settings: SettingsDep,
    x_internal_job_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Guard for POST /internal/run-reminders.

    Compared with :func:`secrets.compare_digest` so the check does not leak the
    secret's prefix through response timing.
    """
    if not settings.internal_job_secret:
        raise service_not_configured("The reminder job", env_vars=["INTERNAL_JOB_SECRET"])
    if not x_internal_job_secret or not secrets.compare_digest(
        x_internal_job_secret, settings.internal_job_secret
    ):
        raise unauthenticated("Bad job secret.")
