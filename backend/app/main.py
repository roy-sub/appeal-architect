"""Appeal Architect API.

A symbolic rules engine determines the appeal route, the review levels, the
deadlines and the required elements. An argumentation solver computes which
counter-arguments are acceptable. An LLM reads documents and writes prose, and
does nothing else.

That separation is the product, so it is enforced structurally rather than by
convention: ``app/rules/**`` and ``app/argumentation/**`` have no import path to
the Anthropic SDK, and ``tests/test_boundary.py`` fails the build if one appears.
See docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from app.api.v1 import router as v1_router
from app.api.v1.health import router as health_router
from app.config import get_settings
from app.problem import (
    Problem,
    http_exception_handler,
    problem_handler,
    validation_handler,
)

logger = logging.getLogger("appeal_architect")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.is_production:
        missing = settings.missing_for_production()
        if missing:
            # Loud, not fatal: a backend that refuses to boot takes the whole
            # site down, but a backend that silently cannot send deadline
            # reminders is worse than one that complains on every line of the log.
            logger.error("Production start with missing configuration: %s", "; ".join(missing))
    else:
        logger.info("Service status: %s", settings.service_status())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Appeal Architect API",
        version="0.1.0",
        description=__doc__,
        lifespan=lifespan,
        # Interactive docs are a development affordance, not a production surface.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Internal-Job-Secret"],
    )

    # Every error leaves as problem+json with a machine-readable code, so the
    # frontend has exactly one error shape to parse.
    app.add_exception_handler(Problem, problem_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)

    app.include_router(health_router)
    app.include_router(v1_router)
    return app


app = create_app()
