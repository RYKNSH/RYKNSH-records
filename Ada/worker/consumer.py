"""Ada Core API — Worker Consumer.

Reads completion jobs from the queue and executes the LangGraph router.
Includes retry logic with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging

from agent.graph import router_graph, RouterState
from agent.tenant import build_thread_id, resolve_tenant_by_api_key
from server.queue import ack, dequeue

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_BACKOFF = 2  # seconds


async def process_job(payload: dict) -> None:
    """Process a single completion job."""
    state: RouterState = {
        "messages": payload["messages"],
        "model": payload.get("model"),
        "temperature": payload.get("temperature", 0.7),
        "max_tokens": payload.get("max_tokens"),
        "tenant_id": payload.get("tenant_id", "unknown"),
        "selected_model": "",
        "langchain_messages": [],
        "response_content": "",
        "response_model": "",
        "usage": {},
        "request_id": payload.get("request_id", "unknown"),
    }

    config = payload.get("_config", {})
    request_id = state["request_id"]
    logger.info("Worker processing request %s", request_id)

    await router_graph.ainvoke(state, config=config)
    logger.info("Worker completed request %s", request_id)


async def process_with_retry(payload: dict) -> None:
    """Process a job with exponential backoff retry."""
    msg_id = payload.get("_msg_id")
    request_id = payload.get("request_id", "?")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await process_job(payload)
            if msg_id:
                await ack(msg_id)
            return
        except Exception:
            if attempt == MAX_RETRIES:
                logger.exception(
                    "Worker FAILED request %s after %d attempts — sending to DLQ",
                    request_id, MAX_RETRIES,
                )
                if msg_id:
                    await ack(msg_id)
                return

            backoff = BASE_BACKOFF ** attempt
            logger.warning(
                "Worker error on request %s (attempt %d/%d), retrying in %ds",
                request_id, attempt, MAX_RETRIES, backoff,
                exc_info=True,
            )
            await asyncio.sleep(backoff)


async def consumer_loop() -> None:
    """Main consumer loop — continuously reads and processes jobs."""
    logger.info("Worker consumer started")

    while True:
        try:
            payload = await dequeue()
            if payload is None:
                continue
            await process_with_retry(payload)
        except asyncio.CancelledError:
            logger.info("Worker consumer shutting down")
            break
        except Exception:
            logger.exception("Unexpected error in consumer loop")
            await asyncio.sleep(5)
