"""Ada Core API — Stripe Billing Integration.

Handles subscription management, usage-based billing, and webhook processing.
Supports Free/Pro/Enterprise tiers with metered billing.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Plan definitions
PLANS = {
    "free": {"name": "Free", "price_usd": 0, "request_limit": 100, "overage_rate": 0},
    "pro": {"name": "Pro", "price_usd": 49, "request_limit": 10_000, "overage_rate": 0.005},
    "enterprise": {"name": "Enterprise", "price_usd": 299, "request_limit": 100_000, "overage_rate": 0.003},
}


class SubscriptionInfo(BaseModel):
    """Tenant subscription information."""
    tenant_id: str
    plan: str = "free"
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""
    request_count: int = 0
    request_limit: int = 100
    is_active: bool = True


class StripeBilling:
    """Stripe billing integration.

    Falls back to in-memory tracking when Stripe is not configured.
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, SubscriptionInfo] = {}

    def get_or_create_subscription(self, tenant_id: str) -> SubscriptionInfo:
        """Get or create a subscription for a tenant (defaults to free)."""
        if tenant_id not in self._subscriptions:
            self._subscriptions[tenant_id] = SubscriptionInfo(
                tenant_id=tenant_id,
                plan="free",
                request_limit=PLANS["free"]["request_limit"],
            )
        return self._subscriptions[tenant_id]

    def check_quota(self, tenant_id: str) -> dict[str, Any]:
        """Check if tenant has remaining quota."""
        sub = self.get_or_create_subscription(tenant_id)
        remaining = max(0, sub.request_limit - sub.request_count)
        return {
            "plan": sub.plan,
            "request_count": sub.request_count,
            "request_limit": sub.request_limit,
            "remaining": remaining,
            "has_quota": remaining > 0 or sub.plan != "free",
            "overage_rate": PLANS[sub.plan]["overage_rate"],
        }

    def increment_usage(self, tenant_id: str) -> dict[str, Any]:
        """Record a request and return updated quota."""
        sub = self.get_or_create_subscription(tenant_id)
        sub.request_count += 1
        return self.check_quota(tenant_id)

    def upgrade_plan(self, tenant_id: str, plan: str) -> SubscriptionInfo:
        """Upgrade a tenant's plan."""
        if plan not in PLANS:
            raise ValueError(f"Unknown plan: {plan}")
        sub = self.get_or_create_subscription(tenant_id)
        sub.plan = plan
        sub.request_limit = PLANS[plan]["request_limit"]
        logger.info("Plan upgraded: tenant=%s plan=%s", tenant_id, plan)
        return sub

    async def create_checkout_session(
        self,
        tenant_id: str,
        plan: str,
    ) -> dict[str, str]:
        """Create a Stripe Checkout session."""
        from server.config import get_settings
        cfg = get_settings()

        if not cfg.stripe_secret_key:
            return {"url": "", "error": "Stripe not configured"}

        try:
            import stripe
            stripe.api_key = cfg.stripe_secret_key

            price_id = ""
            if plan == "pro":
                price_id = cfg.stripe_price_id_pro
            elif plan == "enterprise":
                price_id = cfg.stripe_price_id_enterprise

            if not price_id:
                return {"url": "", "error": f"No price ID for plan: {plan}"}

            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=f"{cfg.app_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{cfg.app_url}/dashboard",
                metadata={"tenant_id": tenant_id, "plan": plan},
            )
            return {"url": session.url, "session_id": session.id}
        except Exception as e:
            logger.error("Stripe checkout failed: %s", e)
            return {"url": "", "error": str(e)}

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict[str, Any]:
        """Process Stripe webhook events."""
        from server.config import get_settings
        cfg = get_settings()

        if not cfg.stripe_secret_key:
            return {"processed": False, "reason": "Stripe not configured"}

        try:
            import stripe
            stripe.api_key = cfg.stripe_secret_key

            event = stripe.Webhook.construct_event(
                payload, sig_header, cfg.stripe_webhook_secret,
            )

            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                tenant_id = session["metadata"].get("tenant_id", "")
                plan = session["metadata"].get("plan", "pro")
                if tenant_id:
                    self.upgrade_plan(tenant_id, plan)
                return {"processed": True, "event": "checkout_completed"}

            elif event["type"] == "customer.subscription.deleted":
                session = event["data"]["object"]
                tenant_id = session.get("metadata", {}).get("tenant_id", "")
                if tenant_id:
                    self.upgrade_plan(tenant_id, "free")
                return {"processed": True, "event": "subscription_cancelled"}

            return {"processed": True, "event": event["type"]}

        except Exception as e:
            logger.error("Webhook processing failed: %s", e)
            return {"processed": False, "error": str(e)}

    def get_billing_info(self, tenant_id: str) -> dict[str, Any]:
        """Get billing information for dashboard."""
        sub = self.get_or_create_subscription(tenant_id)
        plan_info = PLANS[sub.plan]
        overage = max(0, sub.request_count - sub.request_limit)
        overage_cost = overage * plan_info["overage_rate"]

        return {
            "plan": sub.plan,
            "plan_name": plan_info["name"],
            "monthly_cost_usd": plan_info["price_usd"],
            "request_count": sub.request_count,
            "request_limit": sub.request_limit,
            "overage_count": overage,
            "overage_cost_usd": round(overage_cost, 4),
            "total_cost_usd": round(plan_info["price_usd"] + overage_cost, 4),
        }


stripe_billing = StripeBilling()
