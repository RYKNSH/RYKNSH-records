"""Tenant authentication and API key management."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory store for development. Production: Supabase cyrus_tenants table.
_TENANTS: dict[str, dict[str, Any]] = {}
_API_KEYS: dict[str, str] = {}  # hashed_key -> tenant_id


class Tenant(BaseModel):
    """Tenant model."""

    tenant_id: str
    name: str
    plan: str = "free"  # free | usage | growth | full_outcome
    api_keys: list[str] = []
    settings: dict[str, Any] = {}


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def create_tenant(tenant_id: str, name: str, plan: str = "free") -> tuple[Tenant, str]:
    """Create a tenant and return (tenant, api_key)."""
    api_key = f"cyrus_{secrets.token_urlsafe(32)}"
    hashed = _hash_key(api_key)

    tenant = Tenant(tenant_id=tenant_id, name=name, plan=plan, api_keys=[hashed])
    _TENANTS[tenant_id] = tenant.model_dump()
    _API_KEYS[hashed] = tenant_id

    return tenant, api_key


def get_tenant(tenant_id: str) -> Tenant | None:
    """Get tenant by ID."""
    data = _TENANTS.get(tenant_id)
    return Tenant(**data) if data else None


async def authenticate(api_key: str = Security(api_key_header)) -> Tenant:
    """Authenticate request via API key. Returns tenant or raises 401."""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    hashed = _hash_key(api_key)
    tenant_id = _API_KEYS.get(hashed)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=401, detail="Tenant not found")

    return tenant


# Plan limits
PLAN_LIMITS = {
    "free": {"monthly_runs": 100, "nodes_per_run": 3, "pipelines": ["intelligence"]},
    "usage": {"monthly_runs": 1000, "nodes_per_run": 23, "pipelines": ["intelligence", "growth"]},
    "growth": {"monthly_runs": 10000, "nodes_per_run": 23, "pipelines": ["intelligence", "growth"]},
    "full_outcome": {"monthly_runs": -1, "nodes_per_run": 23, "pipelines": ["intelligence", "growth"]},
}


def check_plan_access(tenant: Tenant, pipeline: str) -> None:
    """Check if tenant's plan allows access to the requested pipeline."""
    limits = PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS["free"])
    if pipeline not in limits["pipelines"]:
        raise HTTPException(
            status_code=403,
            detail=f"Pipeline '{pipeline}' not available on '{tenant.plan}' plan. Upgrade to access.",
        )
