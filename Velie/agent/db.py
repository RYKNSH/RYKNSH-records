"""Velie QA Agent — Supabase Client.

Provides a shared Supabase client for all modules.
Falls back to None if Supabase is not configured, allowing
modules to use local JSON fallback.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def get_client():
    """Get Supabase client (lazy init, singleton).

    Returns:
        Supabase client or None if not configured.
    """
    global _client, _initialized

    if _initialized:
        return _client

    _initialized = True
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        logger.info("Supabase not configured — falling back to local JSON")
        return None

    try:
        from supabase import create_client

        _client = create_client(url, key)
        logger.info("Supabase client initialized: %s", url[:30])
        return _client
    except ImportError:
        logger.warning("supabase package not installed — falling back to local JSON")
        return None
    except Exception as e:
        logger.error("Failed to init Supabase: %s", e)
        return None


def is_supabase_available() -> bool:
    """Check if Supabase is available."""
    return get_client() is not None
