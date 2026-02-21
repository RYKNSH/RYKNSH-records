"""Velie QA Agent — GitHub App Authentication.

Handles JWT generation and Installation Access Token management
for GitHub App authentication (replacing PAT-based auth).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import lru_cache

import httpx
import jwt

from server.config import get_settings

logger = logging.getLogger(__name__)

# Token cache: installation_id → (token, expires_at)
_token_cache: dict[int, tuple[str, float]] = {}


def _generate_jwt() -> str:
    """Generate a short-lived JWT for GitHub App authentication.

    The JWT is signed with RS256 using the App's private key
    and is valid for 10 minutes (GitHub maximum).
    """
    cfg = get_settings()

    if not cfg.github_app_id or not cfg.github_app_private_key:
        raise ValueError("GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY must be set")

    now = int(time.time())
    payload = {
        "iat": now - 60,       # Issued at (60s clock drift buffer)
        "exp": now + (10 * 60),  # Expires in 10 minutes
        "iss": str(cfg.github_app_id),
    }

    # Handle private key that may be stored with escaped newlines
    private_key = cfg.github_app_private_key.replace("\\n", "\n")

    token = jwt.encode(payload, private_key, algorithm="RS256")
    logger.debug("Generated GitHub App JWT (app_id=%s)", cfg.github_app_id)
    return token


async def get_installation_token(installation_id: int) -> str:
    """Get an Installation Access Token for a specific GitHub App installation.

    Tokens are cached and automatically refreshed when expired (1-hour validity).
    """
    # Check cache
    if installation_id in _token_cache:
        token, expires_at = _token_cache[installation_id]
        if time.time() < expires_at - 300:  # 5-minute safety margin
            return token

    # Generate new token
    app_jwt = _generate_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    token = data["token"]
    # GitHub tokens expire in 1 hour, parse or assume 3600s
    expires_at = time.time() + 3500  # ~58 minutes, conservative

    _token_cache[installation_id] = (token, expires_at)
    logger.info(
        "Obtained Installation Access Token for installation=%d (cached for ~58min)",
        installation_id,
    )
    return token


async def get_auth_token(installation_id: int | None) -> str:
    """Get the appropriate auth token based on configuration.

    - If GitHub App is configured and installation_id is available: use App token
    - Otherwise: fall back to PAT (github_token)
    """
    cfg = get_settings()

    if cfg.github_app_id and cfg.github_app_private_key and installation_id:
        return await get_installation_token(installation_id)

    if cfg.github_token:
        return cfg.github_token

    raise ValueError("No GitHub authentication method available")


def clear_token_cache() -> None:
    """Clear all cached installation tokens. Useful for testing."""
    _token_cache.clear()
