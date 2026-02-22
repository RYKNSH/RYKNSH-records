"""Ada Core API — Tenant Onboarding.

Handles new tenant registration, API key provisioning, and setup.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from pydantic import BaseModel, Field

from server.api_keys import api_key_store
from server.stripe_billing import stripe_billing

logger = logging.getLogger(__name__)


class SignupRequest(BaseModel):
    """New tenant signup request."""
    email: str
    company_name: str = ""
    plan: str = "free"


class SignupResponse(BaseModel):
    """Signup response with API key."""
    tenant_id: str
    email: str
    plan: str
    api_key: str  # Shown once
    api_key_prefix: str
    dashboard_url: str


async def signup(request: SignupRequest) -> SignupResponse:
    """Register a new tenant and provision API key.

    Returns the API key in plain text (shown only once).
    """
    from server.config import get_settings
    cfg = get_settings()

    tenant_id = str(uuid.uuid4())

    # Create API key
    plain_key, key_record = await api_key_store.create(
        tenant_id=tenant_id,
        name="default",
        mode="live",
    )

    # Initialize subscription
    stripe_billing.get_or_create_subscription(tenant_id)
    if request.plan != "free":
        stripe_billing.upgrade_plan(tenant_id, request.plan)

    # Persist tenant to Supabase
    await _persist_tenant(tenant_id, request)

    logger.info("New tenant: %s (%s) plan=%s", tenant_id, request.email, request.plan)

    return SignupResponse(
        tenant_id=tenant_id,
        email=request.email,
        plan=request.plan,
        api_key=plain_key,
        api_key_prefix=key_record.key_prefix,
        dashboard_url=f"{cfg.app_url}/dashboard",
    )


async def _persist_tenant(tenant_id: str, request: SignupRequest) -> None:
    """Persist tenant to Supabase (best effort)."""
    try:
        from server.config import get_settings
        cfg = get_settings()
        if not (cfg.supabase_url and cfg.supabase_anon_key):
            return
        import httpx
        url = f"{cfg.supabase_url}/rest/v1/ada_tenants"
        headers = {
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, headers=headers, json={
                "id": tenant_id,
                "email": request.email,
                "company_name": request.company_name,
                "plan": request.plan,
            })
    except Exception:
        logger.debug("Tenant persistence failed (non-critical)")
