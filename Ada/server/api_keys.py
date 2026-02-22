"""Ada Core API — API Key Management.

Handles generation, hashing, validation, and lifecycle of API keys.
Keys are hashed before storage (SHA-256). Plain text is shown only at creation.

Key format: ada_live_<32hex> (production) / ada_test_<32hex> (test)
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
    key_prefix: str = ""  # First 8 chars for identification
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


class APIKeyStore:
    """In-memory API key store with Supabase fallback."""

    def __init__(self) -> None:
        self._keys: dict[str, APIKey] = {}  # key_hash -> APIKey

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
        self._keys[key_hash] = key_record

        # Persist to Supabase
        await self._persist(key_record)

        logger.info("API key created: %s... (tenant=%s)", key_record.key_prefix, tenant_id)
        return plain_key, key_record

    async def validate(self, plain_key: str) -> APIKey | None:
        """Validate an API key and return the record."""
        key_hash = hash_api_key(plain_key)
        key_record = self._keys.get(key_hash)

        if key_record and key_record.is_active:
            key_record.last_used_at = datetime.now(timezone.utc)
            return key_record

        # Try Supabase lookup
        return await self._lookup_supabase(key_hash)

    async def list_by_tenant(self, tenant_id: str) -> list[APIKey]:
        """List all keys for a tenant."""
        return [k for k in self._keys.values() if k.tenant_id == tenant_id]

    async def revoke(self, key_id: str, tenant_id: str) -> bool:
        """Revoke an API key."""
        for key in self._keys.values():
            if key.id == key_id and key.tenant_id == tenant_id:
                key.is_active = False
                return True
        return False

    async def _persist(self, key_record: APIKey) -> None:
        try:
            from server.config import get_settings
            cfg = get_settings()
            if not (cfg.supabase_url and cfg.supabase_anon_key):
                return
            import httpx
            url = f"{cfg.supabase_url}/rest/v1/ada_api_keys"
            headers = {
                "apikey": cfg.supabase_anon_key,
                "Authorization": f"Bearer {cfg.supabase_anon_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, headers=headers, json={
                    "id": key_record.id,
                    "tenant_id": key_record.tenant_id,
                    "name": key_record.name,
                    "key_hash": key_record.key_hash,
                    "key_prefix": key_record.key_prefix,
                    "is_active": key_record.is_active,
                })
        except Exception:
            logger.debug("API key persistence failed (non-critical)")

    async def _lookup_supabase(self, key_hash: str) -> APIKey | None:
        try:
            from server.config import get_settings
            cfg = get_settings()
            if not (cfg.supabase_url and cfg.supabase_anon_key):
                return None
            import httpx
            url = f"{cfg.supabase_url}/rest/v1/ada_api_keys?key_hash=eq.{key_hash}&is_active=eq.true&limit=1"
            headers = {
                "apikey": cfg.supabase_anon_key,
                "Authorization": f"Bearer {cfg.supabase_anon_key}",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
                rows = resp.json()
                if rows:
                    row = rows[0]
                    key = APIKey(
                        id=row["id"], tenant_id=row["tenant_id"],
                        name=row.get("name", ""), key_hash=row["key_hash"],
                        key_prefix=row.get("key_prefix", ""), is_active=True,
                    )
                    self._keys[key_hash] = key
                    return key
        except Exception:
            pass
        return None


api_key_store = APIKeyStore()
