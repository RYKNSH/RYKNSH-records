"""Velie QA Agent — Tenant Resolution.

Resolves GitHub App installation_id to internal tenant_id,
and provides tenant-specific configuration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any
from uuid import UUID

import httpx

from server.config import get_settings

logger = logging.getLogger(__name__)

# Default tenant ID — will be fetched from DB once Supabase is connected
_DEFAULT_TENANT_NAME = "RYKNSH records"


@dataclass(frozen=True)
class TenantConfig:
    """Tenant-specific configuration for the QA Agent."""

    tenant_id: UUID
    name: str
    system_prompt_override: str | None = None
    llm_model: str = "claude-sonnet-4-20250514"
    max_diff_chars: int = 60_000
    review_language: str = "en"
    auto_suggest: bool = True

    @classmethod
    def from_db_row(cls, row: dict) -> TenantConfig:
        """Create TenantConfig from a database row."""
        config = row.get("config", {}) or {}
        return cls(
            tenant_id=UUID(str(row["id"])),
            name=row["name"],
            system_prompt_override=config.get("system_prompt_override"),
            llm_model=config.get("llm_model", "claude-sonnet-4-20250514"),
            max_diff_chars=config.get("max_diff_chars", 60_000),
            review_language=config.get("review_language", "en"),
            auto_suggest=config.get("auto_suggest", True),
        )

    @classmethod
    def default(cls) -> TenantConfig:
        """Create default tenant config (for stateless / no-DB mode)."""
        return cls(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
            name=_DEFAULT_TENANT_NAME,
            review_language="ja",
        )


async def resolve_tenant(installation_id: int | None) -> TenantConfig:
    """Resolve a GitHub installation_id to a TenantConfig.

    Falls back to default tenant if:
    - installation_id is None
    - Supabase is not configured
    - Tenant not found in DB
    """
    cfg = get_settings()

    if not installation_id or not cfg.supabase_db_url:
        return TenantConfig.default()

    # Query Supabase REST API for tenant
    try:
        url = f"{cfg.supabase_url}/rest/v1/tenants"
        headers = {
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Accept": "application/json",
        }
        params = {
            "installation_id": f"eq.{installation_id}",
            "select": "*",
            "limit": "1",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            rows = resp.json()

        if rows:
            tenant = TenantConfig.from_db_row(rows[0])
            logger.info("Resolved tenant: %s (installation=%d)", tenant.name, installation_id)
            return tenant

        logger.warning("No tenant found for installation_id=%d, using default", installation_id)
        return TenantConfig.default()

    except Exception:
        logger.exception("Failed to resolve tenant for installation_id=%d", installation_id)
        return TenantConfig.default()


def build_thread_id(tenant_id: UUID, repo: str, pr_number: int) -> str:
    """Build a deterministic thread_id for LangGraph checkpointing.

    Format: {tenant_id}:{repo}:pr-{pr_number}
    This ensures thread isolation across tenants and PRs.
    """
    return f"{tenant_id}:{repo}:pr-{pr_number}"
