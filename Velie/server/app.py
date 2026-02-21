"""Velie QA Agent — FastAPI Webhook Server."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
import httpx

from agent.checkpointer import close_checkpointer, init_checkpointer
from agent.graph import qa_agent, rebuild_with_checkpointer, QAState
from agent.tenant import build_thread_id, resolve_tenant
from agent.usage import check_usage_allowed, get_usage, record_usage, update_plan
from server.config import get_settings
from server.queue import close_queue, enqueue, init_queue
from worker.consumer import consumer_loop

logger = logging.getLogger(__name__)

# Background worker task
_worker_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    global _worker_task

    # Startup
    checkpointer = await init_checkpointer()
    rebuild_with_checkpointer(checkpointer)

    has_redis = await init_queue()
    if has_redis:
        _worker_task = asyncio.create_task(consumer_loop())
        logger.info("Worker consumer task started")

    logger.info("Velie QA Agent v0.4.0 started")
    yield

    # Shutdown
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass

    await close_queue()
    await close_checkpointer()
    logger.info("Velie QA Agent stopped")


app = FastAPI(
    title="Velie QA Agent",
    description="AI-powered code review bot for RYKNSH records",
    version="0.4.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Webhook Signature Verification
# ---------------------------------------------------------------------------

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Background Task — Direct execution (fallback when no queue)
# ---------------------------------------------------------------------------

async def run_review(state: QAState, config: dict | None = None) -> None:
    """Execute the LangGraph QA review pipeline in background."""
    pr_id = f"PR #{state['pr_number']} in {state['repo_full_name']}"
    try:
        logger.info("Starting review for %s", pr_id)
        if config:
            await qa_agent.ainvoke(state, config=config)
        else:
            await qa_agent.ainvoke(state)

        # Record usage after successful review
        tenant_id = (config or {}).get("configurable", {}).get("tenant_id", "default")
        model_used = (config or {}).get("configurable", {}).get("llm_model", "claude-sonnet")
        record_usage(
            tenant_id=tenant_id,
            repo_full_name=state["repo_full_name"],
            pr_number=state["pr_number"],
            model_used=model_used,
        )

        logger.info("Review completed for %s", pr_id)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "GitHub API error for %s: %s %s",
            pr_id, exc.response.status_code, exc.response.text[:200],
        )
    except Exception:
        logger.exception("Unexpected error reviewing %s", pr_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from agent.checkpointer import get_checkpointer
    from server.queue import _redis
    has_checkpointer = get_checkpointer() is not None
    has_redis = _redis is not None
    return {
        "status": "ok",
        "service": "velie-qa-agent",
        "version": "0.4.0",
        "stateful": has_checkpointer,
        "queue": "redis" if has_redis else "memory",
    }


@app.get("/api/usage/{tenant_id}")
async def usage_endpoint(tenant_id: str, month: str | None = None):
    """Get usage data for a tenant."""
    return get_usage(tenant_id, month)


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    """Receive GitHub webhook events and trigger QA review."""

    # 1. Read raw body (single read, parse once)
    body = await request.body()

    # 2. Verify signature
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature header")

    if not verify_signature(body, x_hub_signature_256, get_settings().github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 3. Parse payload from raw body
    payload = json.loads(body)

    # 4. Handle installation events (tenant auto-registration)
    if x_github_event == "installation":
        return await _handle_installation(payload)

    # 5. Only process pull_request events (opened or synchronize)
    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"Event type: {x_github_event}"}

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"PR action: {action}"}

    # 6. Extract PR data
    pr = payload["pull_request"]
    repo = payload["repository"]

    pr_data = {
        "pr_number": pr["number"],
        "repo_full_name": repo["full_name"],
        "pr_title": pr.get("title", ""),
        "pr_author": pr.get("user", {}).get("login", "unknown"),
        "pr_body": pr.get("body", "") or "",
        "installation_id": payload.get("installation", {}).get("id"),
    }

    # 7. Resolve tenant
    tenant = await resolve_tenant(pr_data["installation_id"])
    thread_id = build_thread_id(tenant.tenant_id, pr_data["repo_full_name"], pr_data["pr_number"])

    # 8. Check usage limits
    allowed, reason = check_usage_allowed(str(tenant.tenant_id))
    if not allowed:
        logger.warning(
            "Usage limit reached for tenant %s: %s",
            tenant.name, reason,
        )
        return {"status": "skipped", "reason": reason}

    config = {
        "configurable": {
            "thread_id": thread_id,
            "tenant_id": str(tenant.tenant_id),
            "llm_model": tenant.llm_model,
            "auto_suggest": tenant.auto_suggest,
            "auto_fix_threshold": tenant.auto_fix_threshold,
        }
    }

    # 9. Enqueue or run directly
    from server.queue import _redis
    if _redis is not None:
        # Queue mode: enqueue for worker
        pr_data["_config"] = config
        job_id = await enqueue(pr_data)
        dispatch = f"queued (job={job_id})"
    else:
        # Direct mode: BackgroundTasks fallback
        state: QAState = {**pr_data, "diff": "", "review_body": "", "suggestions": [], "fix_pr_url": ""}
        background_tasks.add_task(run_review, state, config)
        dispatch = "background_task"

    logger.info(
        "Queued review for PR #%d in %s (tenant: %s, dispatch: %s)",
        pr_data["pr_number"], pr_data["repo_full_name"], tenant.name, dispatch,
    )

    return {
        "status": "queued",
        "pr_number": pr_data["pr_number"],
        "repo": pr_data["repo_full_name"],
        "tenant": tenant.name,
    }


async def _handle_installation(payload: dict) -> dict:
    """Handle GitHub App installation/uninstallation events."""
    action = payload.get("action", "")
    installation = payload.get("installation", {})
    installation_id = installation.get("id")
    account = installation.get("account", {}).get("login", "unknown")

    if action == "created":
        logger.info("GitHub App installed by %s (installation_id=%s)", account, installation_id)
        # Auto-register tenant with free plan
        update_plan(str(installation_id), "free")
        return {"status": "installed", "account": account, "plan": "free"}

    elif action == "deleted":
        logger.info("GitHub App uninstalled by %s (installation_id=%s)", account, installation_id)
        return {"status": "uninstalled", "account": account}

    return {"status": "ignored", "reason": f"Installation action: {action}"}

