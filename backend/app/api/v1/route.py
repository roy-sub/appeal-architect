"""The appeal route: computed by the rules engine, never by a model."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUserDep
from app.domain.route import RouteDetermination
from app.problem import not_found
from app.services import route as route_service

router = APIRouter(prefix="/cases/{case_id}", tags=["route"])


@router.post("/route", response_model=RouteDetermination)
async def compute_route(case_id: str, user: CurrentUserDep) -> RouteDetermination:
    """Work out the route from confirmed facts.

    409 with the pending field names when any required fact is unconfirmed.
    Idempotent: identical facts under an identical rulebase return the stored
    determination rather than recomputing it.
    """
    return route_service.compute_route(case_id, user.id)


@router.get("/route", response_model=RouteDetermination)
async def get_route(case_id: str, user: CurrentUserDep) -> RouteDetermination:
    stored = route_service.get_stored(case_id, user.id)
    if stored is None:
        raise not_found("route determination")
    return route_service._from_row(stored)
