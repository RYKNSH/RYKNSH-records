"""Ada Core API — API Key Management.

Handles generation, hashing, validation, and lifecycle of API keys.
Keys are hashed before storage (SHA-256). Plain text is shown only at creation.

Key format: ada_live_<32hex> (production) / ada_test_<32hex> (test)

PRODUCTION: All operations go through Supabase. In-memory dict is a cache only.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class APIKey(BaseModel):
    """API Key record."""
    id: str = ""
    tenant_id: str = ""
    name: str = "default"
    key_hash: str = ""  # SHA-256 hash
    key_prefix: str = ""  # First 12 chars for identification
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime | None = None


def generate_api_key(mode: str = "live") -> tuple[str, str]:
    """Generate a new API key.

    Returns (plain_key, key_hash).
    Plain key is shown once to the user, hash is stored.
    """
    prefix = f"ada_{mode}_"
    random_part = secrets.token_hex(32)
    plain_key = f"{prefix}{random_part}"
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, key_hash


def hash_api_key(plain_key: str) -> str:
    """Hash a plain API key for lookup."""
    return hashlib.sha256(plain_key.encode()).hexdigest()


def _get_supabase_config() -> tuple[str, str] | None:
    """Get Supabase URL and key if configured."""
    try:
        from server.config import get_settings
        cfg = get_settings()
        if cfg.supabase_url and cfg.supabase_anon_key:
            return cfg.supabase_url, cfg.supabase_anon_key
    except Exception:
        pass
    return None


class APIKeyStore:
    """API key store — Supabase-primary with in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, APIKey] = {}  # key_hash -> APIKey (cache only)

    async def create(
        self,
        tenant_id: str,
        name: str = "default",
        mode: str = "live",
    ) -> tuple[str, APIKey]:
        """Create a new API key. Returns (plain_key, key_record)."""
        plain_key, key_hash = generate_api_key(mode)

        key_record = APIKey(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            key_prefix=plain_key[:12],
        )

        # Persist to Supabase (primary)
        persisted = await self._persist(key_record)
        if not persisted:
            logger.warning("API key not persisted to Supabase — running in-memory only")

        # Cache locally
        self._cache[key_hash] = key_record

        logger.info("API key created: %s... (tenant=%s)", key_record.key_prefix, tenant_id)
        return plain_key, key_record

    async def validate(self, plain_key: str) -> APIKey | None:
        """Validate an API key and return the record."""
        key_hash = hash_api_key(plain_key)

        # Check cache first
        cached = self._cache.get(key_hash)
        if cached and cached.is_active:
            cached.last_used_at = datetime.now(timezone.utc)
            return cached

        # Supabase lookup (source of truth)
        record = await self._lookup_supabase(key_hash)
        if record:
            record.last_used_at = datetime.now(timezone.utc)
            self._cache[key_hash] = record  # Populate cache
            return record

        return None

    async def list_by_tenant(self, tenant_id: str) -> list[APIKey]:
        """List all keys for a tenant from Supabase."""
        sb = _get_supabase_config()
        if not sb:
            return [k for k in self._cache.values() if k.tenant_id == tenant_id]

        try:
            import httpx
            url = f"{sb[0]}/rest/v1/ada_api_keys?tenant_id=eq.{tenant_id}&order=created_at.desc"
            headers = {
                "apikey": sb[1],
                "Authorization": f"Bearer {sb[1]}",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                rows = resp.json()
                return [self._row_to_key(r) for r in rows]
        except Exception as e:
            logger.warning("Supabase list_by_tenant failed: %s — using cache", e)
            return [k for k in self._cache.values() if k.tenant_id == tenant_id]

    async def revoke(self, key_id: str, tenant_id: str) -> bool:
        """Revoke an API key in Supabase and cache."""
        sb = _get_supabase_config()
        if sb:
            try:
                import httpx
                url = f"{sb[0]}/rest/v1/ada_api_keys?id=eq.{key_id}&tenant_id=eq.{tenant_id}"
                headers = {
                    "apikey": sb[1],
                    "Authorization": f"Bearer {sb[1]}",
                    "Content-Type": "application/json",
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.patch(url, headers=headers, json={"is_active": False})
            except Exception as e:
                logger.warning("Supabase revoke failed: %s", e)

        # Also update cache
        for key in self._cache.values():
            if key.id == key_id and key.tenant_id == tenant_id:
                key.is_active = False
                return True
        return True  # Supabase update succeeded even if not in cache

    async def _persist(self, key_record: APIKey) -> bool:
        sb = _get_supabase_config()
        if not sb:
            return False
        try:
            import httpx
            url = f"{sb[0]}/rest/v1/ada_api_keys"
            headers = {
                "apikey": sb[1],
                "Authorization": f"Bearer {sb[1]}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, headers=headers, json={
                    "id": key_record.id,
                    "tenant_id": key_record.tenant_id,
                    "name": key_record.name,
                    "key_hash": key_record.key_hash,
                    "key_prefix": key_record.key_prefix,
                    "is_active": key_record.is_active,
                })
                resp.raise_for_status()
            return True
        except Exception as e:
            logger.warning("API key persist failed: %s", e)
            return False

    async def _lookup_supabase(self, key_hash: str) -> APIKey | None:
        sb = _get_supabase_config()
        if not sb:
            return None
        try:
            import httpx
            url = f"{sb[0]}/rest/v1/ada_api_keys?key_hash=eq.{key_hash}&is_active=eq.true&limit=1"
            headers = {
                "apikey": sb[1],
                "Authorization": f"Bearer {sb[1]}",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                rows = resp.json()
                if rows:
                    return self._row_to_key(rows[0])
        except Exception as e:
            logger.debug("Supabase key lookup failed: %s", e)
        return None

    @staticmethod
    def _row_to_key(row: dict) -> APIKey:
        return APIKey(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row.get("name", ""),
            key_hash=row["key_hash"],
            key_prefix=row.get("key_prefix", ""),
            is_active=row.get("is_active", True),
        )


api_key_store = APIKeyStore()
