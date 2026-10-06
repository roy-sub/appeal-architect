"""The confirmation gate.

Proposals in, confirmed facts out — and nothing crosses without an explicit
user action. This module is where "nothing unconfirmed reaches the engine"
becomes a function someone can read.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.db import repo
from app.domain.case import (
    ENGINE_READABLE_STATUSES,
    CaseFacts,
    DenialReason,
    FactStatus,
    PlanType,
    ServiceTiming,
)
from app.problem import ErrorCode, Problem, facts_not_confirmed

#: Facts the rules engine cannot run without. The route endpoint is a 409 until
#: every one of these is confirmed or supplied on the case itself.
REQUIRED_FIELDS = ("plan_type", "state", "denial_date", "service_timing", "denial_reasons")

#: Fields stored on the case row rather than as extracted facts, because the
#: user sets them directly.
CASE_FIELDS = {
    "insurer_name",
    "claim_number",
    "plan_type",
    "state",
    "denial_date",
    "denial_received_date",
    "service_date",
    "service_timing",
    "claim_amount_usd",
    "is_urgent_medical",
}


def list_facts(case_id: str, user_id: str) -> list[dict[str, Any]]:
    return repo.list_for_case("extracted_facts", case_id, user_id, order="created_at")


def _confirmed_at() -> str:
    return datetime.now(tz=UTC).isoformat()


def confirm(case_id: str, fact_id: str, user_id: str) -> dict[str, Any]:
    """Accept the proposal as it stands."""
    fact = repo.get_child("extracted_facts", fact_id, case_id, user_id)
    updated = repo.update_child(
        "extracted_facts",
        fact_id,
        case_id,
        user_id,
        {"status": FactStatus.CONFIRMED.value, "confirmed_at": _confirmed_at()},
    )
    repo.log_event(case_id, "fact_confirmed", {"field": fact["field"]})
    _sync_to_case(case_id, user_id, fact["field"], fact["value"])
    return updated


def edit(case_id: str, fact_id: str, user_id: str, new_value: Any) -> dict[str, Any]:
    """Correct the proposal.

    Extraction will be wrong sometimes and that has to feel normal rather than
    like a failure, so an edit is an ordinary first-class action, not an
    exception path.
    """
    fact = repo.get_child("extracted_facts", fact_id, case_id, user_id)
    updated = repo.update_child(
        "extracted_facts",
        fact_id,
        case_id,
        user_id,
        {
            "status": FactStatus.EDITED.value,
            "edited_value": new_value,
            "confirmed_at": _confirmed_at(),
        },
    )
    repo.log_event(case_id, "fact_edited", {"field": fact["field"]})
    _sync_to_case(case_id, user_id, fact["field"], new_value)
    return updated


def reject(case_id: str, fact_id: str, user_id: str) -> dict[str, Any]:
    """Discard the proposal. It stays visible, marked rejected."""
    fact = repo.get_child("extracted_facts", fact_id, case_id, user_id)
    updated = repo.update_child(
        "extracted_facts",
        fact_id,
        case_id,
        user_id,
        {"status": FactStatus.REJECTED.value},
    )
    repo.log_event(case_id, "fact_rejected", {"field": fact["field"]})
    return updated


def _sync_to_case(case_id: str, user_id: str, field: str, value: Any) -> None:
    """Mirror a confirmed fact onto the case row where the field lives there.

    The case row is what the route service reads, so a confirmation that did not
    reach it would leave the engine working from stale values.
    """
    if field not in CASE_FIELDS:
        return
    coerced = _coerce(field, value)
    if coerced is None:
        return
    with contextlib.suppress(Problem):
        # The case was read a line ago, so this cannot realistically fail. If it
        # does, the fact is still recorded as confirmed and the user is asked for
        # the value directly rather than losing their confirmation.
        repo.update_case(case_id, user_id, {field: coerced})


def _coerce(field: str, value: Any) -> Any:
    """Turn an extracted string into the column's type, or None if it will not go.

    Returning None rather than raising keeps a single malformed proposal from
    blocking the others; the field simply stays unset and the user is asked for
    it directly.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    if field in {"denial_date", "denial_received_date", "service_date"}:
        from datetime import date

        try:
            return date.fromisoformat(text[:10]).isoformat()
        except ValueError:
            return None

    if field == "plan_type":
        try:
            return PlanType(text).value
        except ValueError:
            return None

    if field == "service_timing":
        try:
            return ServiceTiming(text).value
        except ValueError:
            return None

    if field == "state":
        letters = text.upper()[:2]
        return letters if len(letters) == 2 and letters.isalpha() else None

    if field == "claim_amount_usd":
        cleaned = text.replace("$", "").replace(",", "")
        try:
            return str(Decimal(cleaned))
        except InvalidOperation:
            return None

    if field == "is_urgent_medical":
        return text.lower() in {"true", "yes", "1"}

    return text


def confirmed_values(case_id: str, user_id: str) -> dict[str, Any]:
    """Every field the user has confirmed or corrected, as effective values."""
    out: dict[str, Any] = {}
    for row in list_facts(case_id, user_id):
        status = FactStatus(row["status"])
        if status not in ENGINE_READABLE_STATUSES:
            continue
        value = row["edited_value"] if status is FactStatus.EDITED else row["value"]
        out[row["field"]] = value
    return out


def pending_required_fields(case_id: str, user_id: str) -> list[str]:
    """Required fields that are neither set on the case nor confirmed.

    This is what makes POST /route a 409 rather than a route computed from
    half-known facts.
    """
    case = repo.get_case(case_id, user_id)
    confirmed = confirmed_values(case_id, user_id)

    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        if field == "denial_reasons":
            if not _reasons(case, confirmed):
                missing.append(field)
            continue
        if (
            case.get(field) in (None, "", "unknown")
            and _coerce(field, confirmed.get(field)) is None
        ):
            missing.append(field)
    return missing


def _reasons(case: dict[str, Any], confirmed: dict[str, Any]) -> list[DenialReason]:
    raw = confirmed.get("denial_reasons") or case.get("denial_reasons")
    if not raw:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
    elif isinstance(raw, list):
        parts = [str(p).strip() for p in raw]
    else:
        return []
    reasons: list[DenialReason] = []
    for part in parts:
        try:
            reasons.append(DenialReason(part))
        except ValueError:
            continue
    return list(dict.fromkeys(reasons))


def build_case_facts(case_id: str, user_id: str) -> CaseFacts:
    """Assemble :class:`CaseFacts` from confirmed values only.

    Raises a 409 naming the pending fields rather than filling a gap with a
    default. A default here would become a premise, and a premise becomes a
    deadline.
    """
    missing = pending_required_fields(case_id, user_id)
    if missing:
        raise facts_not_confirmed(missing)

    case = repo.get_case(case_id, user_id)
    confirmed = confirmed_values(case_id, user_id)

    def pick(field: str) -> Any:
        on_case = case.get(field)
        if on_case not in (None, "", "unknown"):
            return on_case
        return _coerce(field, confirmed.get(field))

    reasons = _reasons(case, confirmed)
    if not reasons:  # pragma: no cover -- pending_required_fields covers it
        raise facts_not_confirmed(["denial_reasons"])

    from datetime import date

    def as_date(field: str) -> date | None:
        raw = pick(field)
        if not raw:
            return None
        return date.fromisoformat(str(raw)[:10])

    denial_date = as_date("denial_date")
    if denial_date is None:  # pragma: no cover
        raise facts_not_confirmed(["denial_date"])

    try:
        return CaseFacts(
            plan_type=PlanType(str(pick("plan_type"))),
            state=str(pick("state")),
            insurer_name=str(case.get("insurer_name") or "the insurer"),
            member_id_present=bool(confirmed.get("member_id_present", True)),
            claim_number=case.get("claim_number"),
            denial_date=denial_date,
            denial_received_date=as_date("denial_received_date"),
            service_date=as_date("service_date"),
            service_timing=ServiceTiming(str(pick("service_timing"))),
            denial_reasons=reasons,
            cited_policy_language=confirmed.get("cited_policy_language"),
            claim_amount_usd=(
                Decimal(str(case["claim_amount_usd"]))
                if case.get("claim_amount_usd") is not None
                else None
            ),
            is_urgent_medical=bool(case.get("is_urgent_medical")),
            filer=str(case.get("filer") or "member"),  # type: ignore[arg-type]
        )
    except ValueError as error:
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            "Some of the confirmed facts do not fit together. Check the dates and "
            f"the plan type. ({error})",
        ) from None
