"""Ada Core API — Dashboard API Routes.

Backend endpoints for the customer dashboard.
Provides usage stats, API key management, and billing info.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DashboardUsage(BaseModel):
    """Usage response for dashboard."""
    plan: str
    plan_name: str
    request_count: int
    request_limit: int
    remaining: int
    usage_percentage: float
    cost_usd: float


class KeyCreateRequest(BaseModel):
    """API key creation request."""
    name: str = "default"


class KeyResponse(BaseModel):
    """API key response (prefix only, no plain key)."""
    id: str
    name: str
    prefix: str
    is_active: bool


class KeyCreateResponse(BaseModel):
    """Response after key creation (includes plain key once)."""
    id: str
    name: str
    api_key: str  # Shown only once
    prefix: str


async def get_usage(tenant_id: str) -> DashboardUsage:
    """Get usage stats for dashboard."""
    from server.stripe_billing import stripe_billing
    # Load from Supabase to get latest data
    await stripe_billing.load_subscription(tenant_id)
    billing = stripe_billing.get_billing_info(tenant_id)
    remaining = max(0, billing["request_limit"] - billing["request_count"])
    pct = (billing["request_count"] / max(billing["request_limit"], 1)) * 100

    return DashboardUsage(
        plan=billing["plan"],
        plan_name=billing["plan_name"],
        request_count=billing["request_count"],
        request_limit=billing["request_limit"],
        remaining=remaining,
        usage_percentage=round(pct, 1),
        cost_usd=billing["total_cost_usd"],
    )


async def list_keys(tenant_id: str) -> list[KeyResponse]:
    """List API keys for a tenant."""
    from server.api_keys import api_key_store
    keys = await api_key_store.list_by_tenant(tenant_id)
    return [
        KeyResponse(id=k.id, name=k.name, prefix=k.key_prefix, is_active=k.is_active)
        for k in keys
    ]


async def create_key(tenant_id: str, request: KeyCreateRequest) -> KeyCreateResponse:
    """Create a new API key."""
    from server.api_keys import api_key_store
    plain_key, key_record = await api_key_store.create(tenant_id, request.name)
    return KeyCreateResponse(
        id=key_record.id,
        name=key_record.name,
        api_key=plain_key,
        prefix=key_record.key_prefix,
    )


async def revoke_key(tenant_id: str, key_id: str) -> dict[str, bool]:
    """Revoke an API key."""
    from server.api_keys import api_key_store
    success = await api_key_store.revoke(key_id, tenant_id)
    return {"revoked": success}


async def get_billing(tenant_id: str) -> dict[str, Any]:
    """Get billing info for dashboard."""
    from server.stripe_billing import stripe_billing
    await stripe_billing.load_subscription(tenant_id)
    return stripe_billing.get_billing_info(tenant_id)


async def create_checkout(tenant_id: str, plan: str) -> dict[str, str]:
    """Create Stripe checkout session for plan upgrade."""
    from server.stripe_billing import stripe_billing
    return await stripe_billing.create_checkout_session(tenant_id, plan)


async def get_catalog_api() -> list[dict[str, str]]:
    """Get node set catalog for dashboard/LP."""
    from agent.catalog import get_catalog_summary
    return get_catalog_summary()
