"""Ada Core API — Tenant Resolution.

Resolves API keys to internal tenant configuration,
providing tenant-specific model access and rate limiting.

PRODUCTION:
- Internal key (ADA_API_KEY env var) → default RYKNSH tenant
- External keys (ada_live_*) → resolve via api_key_store → Supabase lookup
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
            name=row.get("name", ""),
            default_model=config.get("default_model", "claude-sonnet-4-20250514"),
            allowed_models=allowed,
            rate_limit_rpm=config.get("rate_limit_rpm", 60),
            monthly_budget_usd=config.get("monthly_budget_usd", 500.0),
            system_prompt_override=config.get("system_prompt_override"),
        )

    @classmethod
    def from_tenant_id(cls, tenant_id: str, name: str = "") -> TenantConfig:
        """Create TenantConfig from a tenant_id string."""
        try:
            tid = UUID(tenant_id)
        except (ValueError, AttributeError):
            tid = UUID("00000000-0000-0000-0000-000000000000")
        return cls(tenant_id=tid, name=name or tenant_id[:8])

    @classmethod
    def default(cls) -> TenantConfig:
        """Create default tenant config (for stateless / no-DB mode)."""
        return cls(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
            name=_DEFAULT_TENANT_NAME,
        )


async def resolve_tenant_by_api_key(api_key: str) -> TenantConfig:
    """Resolve an API key to a TenantConfig.

    Resolution order:
    1. Internal key (ADA_API_KEY env var) → default RYKNSH tenant
    2. External key (ada_live_*) → api_key_store → Supabase hash lookup
    3. Legacy: Supabase ada_tenants.api_key column lookup
    4. Fallback: default tenant
    """
    cfg = get_settings()

    # 1. Internal key — default tenant (self-use by RYKNSH subsidiaries)
    if api_key == cfg.ada_api_key:
        return TenantConfig.default()

    # 2. External key — resolve via new api_key_store (SHA-256 hash lookup)
    if api_key.startswith("ada_live_") or api_key.startswith("ada_test_"):
        try:
            from server.api_keys import api_key_store
            key_record = await api_key_store.validate(api_key)
            if key_record:
                # Found in api_key_store — load tenant config from Supabase
                tenant = await _load_tenant_by_id(key_record.tenant_id)
                if tenant:
                    return tenant
                # Tenant row doesn't exist yet — create minimal config
                return TenantConfig.from_tenant_id(key_record.tenant_id)
        except Exception as e:
            logger.warning("api_key_store validation failed: %s", e)

    # 3. Legacy: Supabase ada_tenants.api_key column lookup
    if cfg.supabase_url and cfg.supabase_anon_key:
        tenant = await _legacy_supabase_lookup(api_key)
        if tenant:
            return tenant

    logger.warning("No tenant resolved for api_key — using default")
    return TenantConfig.default()


async def _load_tenant_by_id(tenant_id: str) -> TenantConfig | None:
    """Load TenantConfig from Supabase by tenant ID."""
    cfg = get_settings()
    if not (cfg.supabase_url and cfg.supabase_anon_key):
        return None
    try:
        url = f"{cfg.supabase_url}/rest/v1/ada_tenants?id=eq.{tenant_id}&limit=1"
        headers = {
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            rows = resp.json()
            if rows:
                return TenantConfig.from_db_row(rows[0])
    except Exception as e:
        logger.debug("Tenant load by ID failed: %s", e)
    return None


async def _legacy_supabase_lookup(api_key: str) -> TenantConfig | None:
    """Legacy lookup: query ada_tenants by plain api_key column."""
    cfg = get_settings()
    try:
        url = f"{cfg.supabase_url}/rest/v1/ada_tenants"
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
            logger.info("Resolved tenant (legacy): %s", tenant.name)
            return tenant
    except Exception:
        logger.debug("Legacy tenant lookup failed")
    return None


def build_thread_id(tenant_id: UUID, request_id: str) -> str:
    """Build a deterministic thread_id for LangGraph checkpointing.

    Format: {tenant_id}:{request_id}
    """
    return f"{tenant_id}:{request_id}"
