"""Ada Core API — Blueprint Store.

CRUD operations for AgentBlueprint persistence in Supabase.
Supports versioning, tenant isolation, and graceful degradation
when Supabase is not configured.

WHITEPAPER ref: Section 2 — scribe永続化
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from agent.lifecycle.blueprint import AgentBlueprint

logger = logging.getLogger(__name__)


class BlueprintStore:
    """Supabase-backed blueprint storage.

    All operations are tenant-scoped and version-aware.
    Falls back to in-memory storage when Supabase is not configured.
    """

    TABLE = "ada_blueprints"

    def __init__(self) -> None:
        self._memory_store: dict[str, list[AgentBlueprint]] = {}

    async def save(self, blueprint: AgentBlueprint) -> AgentBlueprint:
        """Save a blueprint (creates new version).

        Returns the saved blueprint with updated version and timestamps.
        """
        from server.config import get_settings

        cfg = get_settings()

        # Assign ID if missing
        if not blueprint.id:
            blueprint.id = str(uuid.uuid4())

        # Increment version
        existing = await self.get_latest(blueprint.tenant_id, blueprint.name)
        if existing:
            blueprint.version = existing.version + 1

        blueprint.updated_at = datetime.now(timezone.utc)

        # Try Supabase first
        if cfg.supabase_url and cfg.supabase_anon_key:
            try:
                import httpx

                url = f"{cfg.supabase_url}/rest/v1/{self.TABLE}"
                headers = {
                    "apikey": cfg.supabase_anon_key,
                    "Authorization": f"Bearer {cfg.supabase_anon_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                }
                row = blueprint.to_supabase_row()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, headers=headers, json=row)
                    resp.raise_for_status()
                logger.info(
                    "Blueprint saved to Supabase: %s v%d (tenant=%s)",
                    blueprint.name, blueprint.version, blueprint.tenant_id,
                )
                return blueprint
            except Exception:
                logger.warning("Supabase save failed, using memory store")

        # Fallback: in-memory
        key = f"{blueprint.tenant_id}:{blueprint.name}"
        if key not in self._memory_store:
            self._memory_store[key] = []
        self._memory_store[key].append(blueprint)
        logger.info(
            "Blueprint saved to memory: %s v%d (tenant=%s)",
            blueprint.name, blueprint.version, blueprint.tenant_id,
        )
        return blueprint

    async def get_latest(
        self,
        tenant_id: str,
        name: str = "default",
    ) -> AgentBlueprint | None:
        """Get the latest version of a blueprint by tenant and name."""
        from server.config import get_settings

        cfg = get_settings()

        if cfg.supabase_url and cfg.supabase_anon_key:
            try:
                import httpx

                url = (
                    f"{cfg.supabase_url}/rest/v1/{self.TABLE}"
                    f"?tenant_id=eq.{tenant_id}"
                    f"&name=eq.{name}"
                    f"&order=version.desc"
                    f"&limit=1"
                )
                headers = {
                    "apikey": cfg.supabase_anon_key,
                    "Authorization": f"Bearer {cfg.supabase_anon_key}",
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    rows = resp.json()
                    if rows:
                        return AgentBlueprint.from_supabase_row(rows[0])
            except Exception:
                logger.debug("Supabase get failed, checking memory store")

        # Fallback: in-memory
        key = f"{tenant_id}:{name}"
        versions = self._memory_store.get(key, [])
        return versions[-1] if versions else None

    async def get_version(
        self,
        tenant_id: str,
        name: str,
        version: int,
    ) -> AgentBlueprint | None:
        """Get a specific version of a blueprint."""
        # In-memory lookup
        key = f"{tenant_id}:{name}"
        versions = self._memory_store.get(key, [])
        for bp in versions:
            if bp.version == version:
                return bp
        return None

    async def list_blueprints(
        self,
        tenant_id: str,
    ) -> list[AgentBlueprint]:
        """List all blueprints for a tenant (latest versions only)."""
        # Collect latest from memory store
        results: list[AgentBlueprint] = []
        for key, versions in self._memory_store.items():
            if key.startswith(f"{tenant_id}:") and versions:
                results.append(versions[-1])
        return results

    async def delete(
        self,
        tenant_id: str,
        name: str,
    ) -> bool:
        """Delete all versions of a blueprint."""
        key = f"{tenant_id}:{name}"
        if key in self._memory_store:
            del self._memory_store[key]
            return True
        return False


# Module-level singleton
blueprint_store = BlueprintStore()
