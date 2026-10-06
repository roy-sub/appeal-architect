"""Liveness, and an honest account of what is configured."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


class Health(BaseModel):
    ok: bool
    env: str
    rulebase_version: str
    schemes_version: str
    services: dict[str, bool]


@router.get("/healthz", response_model=Health)
async def healthz(settings: Annotated[Settings, Depends(get_settings)]) -> Health:
    """Always 200 while the process is up.

    ``services`` reports which halves are wired, by name, with no values -- it is
    how you tell "the backend is asleep" from "the backend has no Supabase keys",
    and the frontend's warming state depends on being able to reach it.
    """
    return Health(
        ok=True,
        env=settings.env,
        rulebase_version=settings.rulebase_version,
        schemes_version=settings.schemes_version,
        services=settings.service_status(),
    )
