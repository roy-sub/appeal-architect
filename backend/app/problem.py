"""RFC 7807 problem+json, with a machine-readable code on every error.

The frontend branches on ``code``, never on the human-readable ``detail``, so
copy can be rewritten without breaking the client. Spec 10.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Starlette's HTTPException, not FastAPI's. FastAPI's subclasses it, and an
# unmatched path raises the Starlette one directly -- registering the base class
# is what makes a 404 on a nonexistent route render as problem+json like
# everything else.
from starlette.exceptions import HTTPException

CONTENT_TYPE = "application/problem+json"


class ErrorCode(StrEnum):
    """Machine-readable error codes. Add, never repurpose."""

    VALIDATION_FAILED = "validation_failed"
    NOT_FOUND = "not_found"
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    SERVICE_NOT_CONFIGURED = "service_not_configured"
    FACTS_NOT_CONFIRMED = "facts_not_confirmed"
    UNSUPPORTED_PLAN_TYPE = "unsupported_plan_type"
    LLM_CAP_REACHED = "llm_cap_reached"
    INTERNAL_ERROR = "internal_error"


_TITLES: dict[ErrorCode, str] = {
    ErrorCode.VALIDATION_FAILED: "Some of what you sent could not be read",
    ErrorCode.NOT_FOUND: "Not found",
    ErrorCode.UNAUTHENTICATED: "Sign in to continue",
    ErrorCode.FORBIDDEN: "Not yours to open",
    ErrorCode.CONFLICT: "That cannot be done in this order",
    ErrorCode.RATE_LIMITED: "Too many requests",
    ErrorCode.SERVICE_NOT_CONFIGURED: "This part of the service is not set up yet",
    ErrorCode.FACTS_NOT_CONFIRMED: "Confirm the facts first",
    ErrorCode.UNSUPPORTED_PLAN_TYPE: "We cannot route this plan type yet",
    ErrorCode.LLM_CAP_REACHED: "Monthly document limit reached",
    ErrorCode.INTERNAL_ERROR: "Something went wrong on our side",
}


class Problem(HTTPException):
    """An error that renders as problem+json.

    ``detail`` is shown to the user, so it follows the product's voice: plain,
    specific, an instruction rather than an apology, and never red in the UI.
    """

    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        detail: str,
        *,
        title: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.title = title or _TITLES.get(code, "Error")
        self.extra = extra or {}

    def to_response(self) -> JSONResponse:
        body: dict[str, Any] = {
            "type": f"https://appealarchitect.app/problems/{self.code.value}",
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
            "code": self.code.value,
        }
        body.update(jsonable_encoder(self.extra))
        return JSONResponse(status_code=self.status_code, content=body, media_type=CONTENT_TYPE)


# ---- shorthands used across the API ----------------------------------------


def not_found(what: str) -> Problem:
    return Problem(404, ErrorCode.NOT_FOUND, f"We could not find that {what}.")


def unauthenticated(detail: str = "Sign in to continue.") -> Problem:
    return Problem(401, ErrorCode.UNAUTHENTICATED, detail)


def forbidden(detail: str = "This case belongs to another account.") -> Problem:
    return Problem(403, ErrorCode.FORBIDDEN, detail)


def service_not_configured(service: str, *, env_vars: list[str]) -> Problem:
    return Problem(
        503,
        ErrorCode.SERVICE_NOT_CONFIGURED,
        f"{service} is not configured on this server. Set {', '.join(env_vars)} and restart.",
        extra={"service": service, "missing_env": env_vars},
    )


def facts_not_confirmed(pending: list[str]) -> Problem:
    return Problem(
        409,
        ErrorCode.FACTS_NOT_CONFIRMED,
        "Confirm or correct every fact before we work out your route. "
        f"{len(pending)} still need a look.",
        extra={"pending_fields": pending},
    )


# ---- exception handlers -----------------------------------------------------


#: Framework default details, replaced with the product's own copy.
_GENERIC_DETAILS: dict[str, str] = {
    "Not Found": "There is nothing at that address.",
    "Method Not Allowed": "That address does not accept this kind of request.",
    "Internal Server Error": "Something went wrong on our side. Nothing you sent was lost.",
}


async def problem_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, Problem)
    return exc.to_response()


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Render FastAPI's own HTTPExceptions as problem+json too.

    Without this, a 404 raised by the router returns a bare {"detail": ...} and
    the frontend's error parser has two shapes to handle.
    """
    assert isinstance(exc, HTTPException)
    code = {
        401: ErrorCode.UNAUTHENTICATED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMITED,
    }.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    # Starlette's own details are framework strings ("Not Found"), which read as
    # a duplicate of the title and are not the product's voice.
    detail = _GENERIC_DETAILS.get(str(exc.detail), str(exc.detail))
    return Problem(exc.status_code, code, detail).to_response()


async def validation_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return Problem(
        422,
        ErrorCode.VALIDATION_FAILED,
        "Check the highlighted fields and try again.",
        extra={"errors": exc.errors()},
    ).to_response()
