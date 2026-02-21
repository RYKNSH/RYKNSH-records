"""Velie QA Agent — Worker Consumer.

Reads review jobs from the queue and executes the LangGraph agent.
Includes retry logic with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging

from agent.graph import qa_agent, QAState
from agent.tenant import build_thread_id, resolve_tenant
from server.queue import ack, dequeue

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_BACKOFF = 2  # seconds


async def process_job(payload: dict) -> None:
    """Process a single review job."""
    state: QAState = {
        "pr_number": payload["pr_number"],
        "repo_full_name": payload["repo_full_name"],
        "pr_title": payload.get("pr_title", ""),
        "pr_author": payload.get("pr_author", "unknown"),
        "pr_body": payload.get("pr_body", ""),
        "installation_id": payload.get("installation_id"),
        "diff": "",
        "review_body": "",
    }

    # Resolve tenant
    tenant = await resolve_tenant(state["installation_id"])
    thread_id = build_thread_id(tenant.tenant_id, state["repo_full_name"], state["pr_number"])

    config = {
        "configurable": {
            "thread_id": thread_id,
            "tenant_id": str(tenant.tenant_id),
            "llm_model": tenant.llm_model,
        }
    }

    pr_id = f"PR #{state['pr_number']} in {state['repo_full_name']}"
    logger.info("Worker processing %s (tenant: %s)", pr_id, tenant.name)

    await qa_agent.ainvoke(state, config=config)
    logger.info("Worker completed %s", pr_id)


async def process_with_retry(payload: dict) -> None:
    """Process a job with exponential backoff retry."""
    msg_id = payload.get("_msg_id")
    pr_id = f"PR #{payload.get('pr_number', '?')}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await process_job(payload)
            if msg_id:
                await ack(msg_id)
            return
        except Exception:
            if attempt == MAX_RETRIES:
                logger.exception(
                    "Worker FAILED %s after %d attempts — sending to DLQ",
                    pr_id, MAX_RETRIES,
                )
                if msg_id:
                    await ack(msg_id)
                return

            backoff = BASE_BACKOFF ** attempt
            logger.warning(
                "Worker error on %s (attempt %d/%d), retrying in %ds",
                pr_id, attempt, MAX_RETRIES, backoff,
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
