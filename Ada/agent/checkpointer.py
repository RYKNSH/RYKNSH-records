"""Ada Core API — AsyncPostgresSaver Checkpointer.

Manages LangGraph checkpoint persistence via Supabase PostgreSQL.
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from server.config import get_settings

logger = logging.getLogger(__name__)

# Module-level state for lifecycle management
_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None


async def init_checkpointer() -> AsyncPostgresSaver:
    """Initialize the AsyncPostgresSaver with a connection pool.

    Should be called once during application startup (FastAPI lifespan).
    """
    global _pool, _checkpointer

    cfg = get_settings()
    if not cfg.supabase_db_url:
        logger.warning("SUPABASE_DB_URL not set — checkpointer disabled (stateless mode)")
        return None

    _pool = AsyncConnectionPool(
        conninfo=cfg.supabase_db_url,
        min_size=2,
        max_size=10,
        open=False,
    )
    await _pool.open()

    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()

    logger.info("AsyncPostgresSaver initialized with connection pool (min=2, max=10)")
    return _checkpointer


async def close_checkpointer() -> None:
    """Close the connection pool. Called during application shutdown."""
    global _pool, _checkpointer

    if _pool is not None:
        await _pool.close()
        _pool = None
        _checkpointer = None
        logger.info("Checkpointer connection pool closed")


def get_checkpointer() -> AsyncPostgresSaver | None:
    """Get the current checkpointer instance. Returns None if not initialized."""
    return _checkpointer
