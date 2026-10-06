"""Versioned API surface. Spec 10."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    arguments,
    billing,
    cases,
    documents,
    facts,
    internal,
    letters,
    me,
    public,
    route,
)

#: Routes under /api/v1. /healthz is mounted at the root instead, so an uptime
#: monitor and a load balancer do not have to know the API version.
router = APIRouter(prefix="/api/v1")
router.include_router(me.router)
router.include_router(cases.router)
router.include_router(documents.router)
router.include_router(facts.router)
router.include_router(route.router)
router.include_router(arguments.router)
router.include_router(letters.router)
router.include_router(public.router)
router.include_router(billing.router)
router.include_router(internal.router)
