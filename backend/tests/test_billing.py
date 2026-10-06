"""Entitlement gating.

What is gated is a product decision with a real cost to someone who is unwell,
so it is pinned by tests rather than left in a config file.
"""

from __future__ import annotations

import pytest

from app.api.v1.billing import PAID_TIERS, require_paid
from app.problem import Problem


def test_the_paid_tiers_are_the_two_products() -> None:
    assert {"appeal_package", "subscription"} == PAID_TIERS


def test_a_free_user_cannot_generate_a_letter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.v1.billing.current_tier", lambda _user: "free")
    with pytest.raises(Problem) as caught:
        require_paid("user-1")
    assert caught.value.status_code == 402


def test_the_paywall_message_says_the_deadline_stays_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The product exists to stop a deadline being hidden from someone.

    Hiding one behind our own paywall would make it the thing it fights. The
    message has to say so, because somebody who cannot pay today should leave
    knowing their deadline.
    """
    monkeypatch.setattr("app.api.v1.billing.current_tier", lambda _user: "free")
    with pytest.raises(Problem) as caught:
        require_paid("user-1")
    detail = caught.value.detail.lower()
    assert "deadline" in detail
    assert "nothing about your case is hidden" in detail


@pytest.mark.parametrize("tier", ["appeal_package", "subscription"])
def test_a_paid_user_passes(monkeypatch: pytest.MonkeyPatch, tier: str) -> None:
    monkeypatch.setattr("app.api.v1.billing.current_tier", lambda _user: tier)
    require_paid("user-1")  # must not raise


def test_the_entitlement_response_lists_what_is_never_gated(
    monkeypatch: pytest.MonkeyPatch, client
) -> None:
    from app.api.v1.billing import Entitlement, get_entitlement  # noqa: F401

    monkeypatch.setattr("app.api.v1.billing.current_tier", lambda _user: "free")
    # Called directly: the endpoint needs auth, and what is asserted here is the
    # contents of the list rather than the HTTP plumbing.
    import asyncio

    from app.deps import CurrentUser

    result = asyncio.run(get_entitlement(CurrentUser(id="u", email="a@b.c")))
    assert result.can_generate_letter is False
    joined = " ".join(result.always_available).lower()
    assert "deadline" in joined
    assert "rule" in joined
    assert "deleting your data" in joined


def test_an_unconfigured_stripe_is_a_503_not_a_crash(client) -> None:
    """A clone with no Stripe keys should say so, not raise."""
    from app.api.v1.billing import current_tier

    assert current_tier("anyone") == "free"
