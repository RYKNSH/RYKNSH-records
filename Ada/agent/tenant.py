"""Ada Core API — Tenant Resolution.

Resolves API keys to internal tenant configuration,
providing tenant-specific model access and rate limiting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

import httpx

from server.config import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_TENANT_NAME = "RYKNSH records"


@dataclass(frozen=True)
class TenantConfig:
    """Tenant-specific configuration for the Ada Core API."""

    tenant_id: UUID
    name: str
    default_model: str = "claude-sonnet-4-20250514"
    allowed_models: tuple[str, ...] = (
        "claude-sonnet-4-20250514",
        "gpt-4o",
        "gpt-4o-mini",
    )
    rate_limit_rpm: int = 60
    monthly_budget_usd: float = 500.0
    system_prompt_override: str | None = None

    @classmethod
    def from_db_row(cls, row: dict) -> TenantConfig:
        """Create TenantConfig from a database row."""
        config = row.get("config", {}) or {}
        allowed = config.get("allowed_models")
        if isinstance(allowed, list):
            allowed = tuple(allowed)
        else:
            allowed = cls.allowed_models

        return cls(
            tenant_id=UUID(str(row["id"])),
            name=row["name"],
            default_model=config.get("default_model", "claude-sonnet-4-20250514"),
            allowed_models=allowed,
            rate_limit_rpm=config.get("rate_limit_rpm", 60),
            monthly_budget_usd=config.get("monthly_budget_usd", 500.0),
            system_prompt_override=config.get("system_prompt_override"),
        )

    @classmethod
    def default(cls) -> TenantConfig:
        """Create default tenant config (for stateless / no-DB mode)."""
        return cls(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
            name=_DEFAULT_TENANT_NAME,
        )


async def resolve_tenant_by_api_key(api_key: str) -> TenantConfig:
    """Resolve an API key to a TenantConfig.

    Falls back to default tenant if:
    - api_key matches the internal ADA_API_KEY
    - Supabase is not configured
    - Tenant not found in DB
    """
    cfg = get_settings()

    # Internal key — default tenant (self-use by RYKNSH subsidiaries)
    if api_key == cfg.ada_api_key:
        return TenantConfig.default()

    if not cfg.supabase_url or not cfg.supabase_anon_key:
        logger.warning("Supabase not configured — using default tenant")
        return TenantConfig.default()

    # Query Supabase REST API for tenant by api_key
    try:
        url = f"{cfg.supabase_url}/rest/v1/tenants"
        headers = {
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Accept": "application/json",
        }
        params = {
            "api_key": f"eq.{api_key}",
            "select": "*",
            "limit": "1",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            rows = resp.json()

        if rows:
            tenant = TenantConfig.from_db_row(rows[0])
            logger.info("Resolved tenant: %s", tenant.name)
            return tenant

        logger.warning("No tenant found for api_key, using default")
        return TenantConfig.default()

    except Exception:
        logger.exception("Failed to resolve tenant by api_key")
        return TenantConfig.default()


def build_thread_id(tenant_id: UUID, request_id: str) -> str:
    """Build a deterministic thread_id for LangGraph checkpointing.

    Format: {tenant_id}:{request_id}
    """
    return f"{tenant_id}:{request_id}"
