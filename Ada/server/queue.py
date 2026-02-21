"""Ada Core API — Message Queue.

Abstracts queue operations for decoupling API reception from LLM execution.
Supports Redis Streams with in-memory fallback for development.
"""

from __future__ import annotations

import json
import logging
from collections import deque

import redis.asyncio as aioredis

from server.config import get_settings

logger = logging.getLogger(__name__)

# In-memory fallback queue (for development without Redis)
_memory_queue: deque[dict] = deque()

# Redis client singleton
_redis: aioredis.Redis | None = None

STREAM_NAME = "ada:completions"
GROUP_NAME = "ada-workers"
CONSUMER_NAME = "worker-1"


async def init_queue() -> bool:
    """Initialize the queue backend. Returns True if Redis is available."""
    global _redis

    cfg = get_settings()
    if not cfg.redis_url:
        logger.info("REDIS_URL not set — using in-memory queue (development mode)")
        return False

    try:
        _redis = aioredis.from_url(cfg.redis_url, decode_responses=True)
        await _redis.ping()

        # Create consumer group (idempotent)
        try:
            await _redis.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        logger.info("Redis queue initialized (stream=%s, group=%s)", STREAM_NAME, GROUP_NAME)
        return True

    except Exception:
        logger.exception("Failed to connect to Redis — falling back to in-memory queue")
        _redis = None
        return False


async def close_queue() -> None:
    """Close the queue connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed")


async def enqueue(payload: dict) -> str:
    """Add a completion job to the queue. Returns a job ID."""
    if _redis is not None:
        job_data = {"payload": json.dumps(payload)}
        msg_id = await _redis.xadd(STREAM_NAME, job_data)
        logger.info("Enqueued job %s to Redis stream", msg_id)
        return str(msg_id)

    # In-memory fallback
    job_id = f"mem-{len(_memory_queue)}"
    payload["_job_id"] = job_id
    _memory_queue.append(payload)
    logger.info("Enqueued job %s to in-memory queue", job_id)
    return job_id


async def dequeue() -> dict | None:
    """Read the next job from the queue. Returns None if empty."""
    if _redis is not None:
        messages = await _redis.xreadgroup(
            GROUP_NAME, CONSUMER_NAME,
            {STREAM_NAME: ">"},
            count=1,
            block=5000,
        )
        if not messages:
            return None

        stream_name, entries = messages[0]
        msg_id, fields = entries[0]
        payload = json.loads(fields["payload"])
        payload["_msg_id"] = msg_id
        return payload

    # In-memory fallback
    if _memory_queue:
        return _memory_queue.popleft()
    return None


async def ack(msg_id: str) -> None:
    """Acknowledge a processed message (Redis only)."""
    if _redis is not None:
        await _redis.xack(STREAM_NAME, GROUP_NAME, msg_id)
        logger.debug("Acknowledged message %s", msg_id)
