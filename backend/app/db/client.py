"""Supabase access, server side.

The backend uses the service-role key, which bypasses RLS. That is deliberate --
the API is the enforcement point and derives ``user_id`` from the verified JWT,
never from the request body -- but it means every query here must scope by user
explicitly. RLS stays on as the second line of defence for anything that reaches
Postgres by another path.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.config import get_settings
from app.problem import service_not_configured

if TYPE_CHECKING:  # pragma: no cover
    from supabase import Client

SUPABASE_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
]


@lru_cache
def get_client() -> Client:
    """The service-role client. Raises a 503 Problem when unconfigured."""
    settings = get_settings()
    if not settings.supabase_configured:
        raise service_not_configured("Supabase", env_vars=SUPABASE_ENV_VARS)

    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_role_key)
