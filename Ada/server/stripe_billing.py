"""Ada Core API — Stripe Billing Integration.

Handles subscription management, usage-based billing, and webhook processing.
Supports Free/Pro/Enterprise tiers with metered billing.

PRODUCTION: Subscription state is persisted in Supabase `ada_subscriptions` table.
In-memory dict is a cache for fast lookups within a single process lifetime.
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


def _get_supabase_config() -> tuple[str, str] | None:
    try:
        from server.config import get_settings
        cfg = get_settings()
        if cfg.supabase_url and cfg.supabase_anon_key:
            return cfg.supabase_url, cfg.supabase_anon_key
    except Exception:
        pass
    return None


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
    """Stripe billing — Supabase-primary with in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, SubscriptionInfo] = {}

    def get_or_create_subscription(self, tenant_id: str) -> SubscriptionInfo:
        """Get or create a subscription for a tenant (defaults to free)."""
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        # Not in cache — create default and persist
        sub = SubscriptionInfo(
            tenant_id=tenant_id,
            plan="free",
            request_limit=PLANS["free"]["request_limit"],
        )
        self._cache[tenant_id] = sub
        return sub

    async def load_subscription(self, tenant_id: str) -> SubscriptionInfo:
        """Load subscription from Supabase, fallback to cache/default."""
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        sb = _get_supabase_config()
        if sb:
            try:
                import httpx
                url = f"{sb[0]}/rest/v1/ada_subscriptions?tenant_id=eq.{tenant_id}&limit=1"
                headers = {"apikey": sb[1], "Authorization": f"Bearer {sb[1]}"}
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    rows = resp.json()
                    if rows:
                        row = rows[0]
                        sub = SubscriptionInfo(
                            tenant_id=tenant_id,
                            plan=row.get("plan", "free"),
                            stripe_customer_id=row.get("stripe_customer_id", ""),
                            stripe_subscription_id=row.get("stripe_subscription_id", ""),
                            request_count=row.get("request_count", 0),
                            request_limit=PLANS.get(row.get("plan", "free"), PLANS["free"])["request_limit"],
                            is_active=row.get("is_active", True),
                        )
                        self._cache[tenant_id] = sub
                        return sub
            except Exception as e:
                logger.warning("Supabase subscription load failed: %s", e)

        return self.get_or_create_subscription(tenant_id)

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

    async def increment_usage(self, tenant_id: str) -> dict[str, Any]:
        """Record a request and persist to Supabase."""
        sub = self.get_or_create_subscription(tenant_id)
        sub.request_count += 1

        # Persist usage increment to Supabase
        await self._persist_usage(tenant_id, sub.request_count)

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

    async def upgrade_plan_and_persist(self, tenant_id: str, plan: str) -> SubscriptionInfo:
        """Upgrade plan and persist to Supabase."""
        sub = self.upgrade_plan(tenant_id, plan)
        await self._persist_subscription(sub)
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
            return {"url": "", "error": "Stripe not configured — upgrade plan manually via API"}

        try:
            import stripe
            stripe.api_key = cfg.stripe_secret_key

            price_id = ""
            if plan == "pro":
                price_id = cfg.stripe_price_id_pro
            elif plan == "enterprise":
                price_id = cfg.stripe_price_id_enterprise

            if not price_id:
                return {"url": "", "error": f"No price ID configured for plan: {plan}"}

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
                    await self.upgrade_plan_and_persist(tenant_id, plan)
                return {"processed": True, "event": "checkout_completed"}

            elif event["type"] == "customer.subscription.deleted":
                session = event["data"]["object"]
                tenant_id = session.get("metadata", {}).get("tenant_id", "")
                if tenant_id:
                    await self.upgrade_plan_and_persist(tenant_id, "free")
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

    async def _persist_subscription(self, sub: SubscriptionInfo) -> None:
        """Upsert subscription to Supabase."""
        sb = _get_supabase_config()
        if not sb:
            return
        try:
            import httpx
            url = f"{sb[0]}/rest/v1/ada_subscriptions"
            headers = {
                "apikey": sb[1],
                "Authorization": f"Bearer {sb[1]}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, headers=headers, json={
                    "tenant_id": sub.tenant_id,
                    "plan": sub.plan,
                    "stripe_customer_id": sub.stripe_customer_id,
                    "stripe_subscription_id": sub.stripe_subscription_id,
                    "request_count": sub.request_count,
                    "is_active": sub.is_active,
                })
        except Exception as e:
            logger.warning("Subscription persist failed: %s", e)

    async def _persist_usage(self, tenant_id: str, request_count: int) -> None:
        """Update request count in Supabase."""
        sb = _get_supabase_config()
        if not sb:
            return
        try:
            import httpx
            url = f"{sb[0]}/rest/v1/ada_subscriptions?tenant_id=eq.{tenant_id}"
            headers = {
                "apikey": sb[1],
                "Authorization": f"Bearer {sb[1]}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.patch(url, headers=headers, json={
                    "request_count": request_count,
                })
        except Exception:
            pass  # Non-blocking — usage sync is best-effort


stripe_billing = StripeBilling()
