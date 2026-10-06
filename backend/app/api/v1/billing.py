"""Stripe: one-time Appeal Package and subscription, with entitlement gating.

What is gated and what is not
-----------------------------
Gating decisions here are product decisions with a real cost to someone who is
unwell, so they are stated rather than left in a config file:

* **Never gated:** the free triage check, opening a case, uploading a denial
  letter, confirming the extracted facts, and **seeing the route with its real
  deadlines and citations**. Somebody who finds out from us that they have 14
  days left must be told that whether or not they can pay. Hiding a deadline
  behind a paywall would make the product the thing it exists to fight.
* **Gated:** generating and exporting the appeal letter, and the full argument
  graph detail. That is the work product.

The entitlement is read from ``profiles.plan_tier``, which the webhook sets.
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.config import get_settings
from app.deps import CurrentUserDep
from app.problem import ErrorCode, Problem

logger = logging.getLogger("appeal_architect.billing")

router = APIRouter(prefix="/billing", tags=["billing"])

Tier = Literal["free", "appeal_package", "subscription"]

#: Tiers that may generate and export a letter.
PAID_TIERS = {"appeal_package", "subscription"}


def current_tier(user_id: str) -> str:
    settings = get_settings()
    if not settings.supabase_configured:
        return "free"
    from app.db.client import get_client
    from app.db.repo import narrow_rows

    rows = narrow_rows(
        get_client()
        .table("profiles")
        .select("plan_tier")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    )
    return str(rows[0]["plan_tier"]) if rows else "free"


def require_paid(user_id: str) -> None:
    """Gate the work product, never the deadline.

    The error names what is still free, because somebody who cannot pay today
    should leave knowing their deadline rather than knowing only that they
    cannot pay.
    """
    if current_tier(user_id) in PAID_TIERS:
        return
    raise Problem(
        402,
        ErrorCode.FORBIDDEN,
        "Writing the letter is part of the Appeal Package. Your route, your "
        "deadlines and the rule behind each one stay available either way — "
        "nothing about your case is hidden from you.",
        title="This part needs the Appeal Package",
        extra={"tier": current_tier(user_id), "gated": "letter_generation"},
    )


class CheckoutRequest(BaseModel):
    product: Literal["appeal_package", "subscription"]
    success_url: str
    cancel_url: str


class CheckoutSession(BaseModel):
    url: str


@router.post("/checkout", response_model=CheckoutSession)
async def create_checkout(payload: CheckoutRequest, user: CurrentUserDep) -> CheckoutSession:
    """Open a Stripe Checkout session."""
    settings = get_settings()
    if not settings.stripe_configured:
        raise Problem(
            503,
            ErrorCode.SERVICE_NOT_CONFIGURED,
            "Payment is not set up on this server. Set STRIPE_SECRET_KEY and "
            "STRIPE_WEBHOOK_SECRET and restart.",
            extra={"missing_env": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"]},
        )

    import stripe

    stripe.api_key = settings.stripe_secret_key
    price_id = (
        settings.stripe_price_appeal_package
        if payload.product == "appeal_package"
        else settings.stripe_price_subscription
    )
    if not price_id:
        raise Problem(
            503,
            ErrorCode.SERVICE_NOT_CONFIGURED,
            "That product is not configured on this server.",
            extra={"missing_env": ["STRIPE_PRICE_APPEAL_PACKAGE", "STRIPE_PRICE_SUBSCRIPTION"]},
        )

    create_args: dict[str, object] = {
        "mode": "payment" if payload.product == "appeal_package" else "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": payload.success_url,
        "cancel_url": payload.cancel_url,
        "client_reference_id": user.id,
        # No case id, no diagnosis, nothing clinical reaches Stripe.
        "metadata": {"user_id": user.id, "product": payload.product},
    }
    if user.email:
        create_args["customer_email"] = user.email

    try:
        session = stripe.checkout.Session.create(**create_args)  # type: ignore[arg-type]
    except Exception:
        logger.warning("stripe checkout failed", exc_info=False)
        raise Problem(
            502,
            ErrorCode.INTERNAL_ERROR,
            "We could not start the payment just now. Nothing was charged. Try again shortly.",
        ) from None

    url = getattr(session, "url", None)
    if not url:  # pragma: no cover
        raise Problem(502, ErrorCode.INTERNAL_ERROR, "Stripe did not return a checkout link.")
    return CheckoutSession(url=str(url))


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request) -> dict[str, bool]:
    """Set the user's tier when a payment completes.

    The signature is verified before anything is read from the body: an
    unverified webhook is an unauthenticated request that grants entitlements.
    """
    settings = get_settings()
    if not settings.stripe_configured:
        raise Problem(
            503, ErrorCode.SERVICE_NOT_CONFIGURED, "Payment is not set up on this server."
        )

    import stripe

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception:
        raise Problem(
            400, ErrorCode.VALIDATION_FAILED, "That webhook signature did not verify."
        ) from None

    kind = event["type"]
    data = event["data"]["object"]

    if kind == "checkout.session.completed":
        user_id = data.get("client_reference_id") or (data.get("metadata") or {}).get("user_id")
        product = (data.get("metadata") or {}).get("product", "appeal_package")
        if user_id:
            _set_tier(str(user_id), str(product), data.get("customer"))
    elif kind in {"customer.subscription.deleted", "customer.subscription.paused"}:
        customer = data.get("customer")
        if customer:
            _downgrade_by_customer(str(customer))

    return {"received": True}


def _set_tier(user_id: str, tier: str, customer: object) -> None:
    from app.db.client import get_client

    get_client().table("profiles").upsert(
        {
            "user_id": user_id,
            "plan_tier": tier,
            "stripe_customer_id": str(customer) if customer else None,
        },
        on_conflict="user_id",
    ).execute()
    logger.info("tier set for a user: %s", tier)


def _downgrade_by_customer(customer_id: str) -> None:
    """A cancelled subscription drops to free. Cases and documents are untouched.

    Someone who stops paying keeps their deadlines and their letter. Taking
    those away would be taking away the thing they were relying on.
    """
    from app.db.client import get_client

    get_client().table("profiles").update({"plan_tier": "free"}).eq(
        "stripe_customer_id", customer_id
    ).execute()


class Entitlement(BaseModel):
    tier: str
    can_generate_letter: bool
    #: What stays available at every tier, so the UI can say so plainly.
    always_available: list[str]


@router.get("/entitlement", response_model=Entitlement)
async def get_entitlement(user: CurrentUserDep) -> Entitlement:
    tier = current_tier(user.id)
    return Entitlement(
        tier=tier,
        can_generate_letter=tier in PAID_TIERS,
        always_available=[
            "Your appeal route and review levels",
            "Every deadline, with the rule it comes from",
            "Reading your denial letter and confirming the facts",
            "Deadline reminder emails",
            "Deleting your data",
        ],
    )
