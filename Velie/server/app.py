"""Velie QA Agent — FastAPI Webhook Server."""

from __future__ import annotations

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
from server.config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    # Startup
    checkpointer = await init_checkpointer()
    rebuild_with_checkpointer(checkpointer)
    logger.info("Velie QA Agent started")
    yield
    # Shutdown
    await close_checkpointer()
    logger.info("Velie QA Agent stopped")


app = FastAPI(
    title="Velie QA Agent",
    description="AI-powered code review bot for RYKNSH records",
    version="0.2.0",
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
# Background Task — Run the QA Agent
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
    has_checkpointer = get_checkpointer() is not None
    return {
        "status": "ok",
        "service": "velie-qa-agent",
        "version": "0.2.0",
        "stateful": has_checkpointer,
    }


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

    # 3. Parse payload from raw body (avoid double read via request.json())
    payload = json.loads(body)

    # 4. Only process pull_request events (opened or synchronize)
    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"Event type: {x_github_event}"}

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"PR action: {action}"}

    # 5. Extract PR data
    pr = payload["pull_request"]
    repo = payload["repository"]

    state: QAState = {
        "pr_number": pr["number"],
        "repo_full_name": repo["full_name"],
        "pr_title": pr.get("title", ""),
        "pr_author": pr.get("user", {}).get("login", "unknown"),
        "pr_body": pr.get("body", "") or "",
        "installation_id": payload.get("installation", {}).get("id"),
        "diff": "",
        "review_body": "",
    }

    # 6. Resolve tenant and build RunnableConfig
    tenant = await resolve_tenant(state["installation_id"])
    thread_id = build_thread_id(tenant.tenant_id, state["repo_full_name"], state["pr_number"])

    config = {
        "configurable": {
            "thread_id": thread_id,
            "tenant_id": str(tenant.tenant_id),
            "llm_model": tenant.llm_model,
        }
    }

    # 7. Enqueue background review
    background_tasks.add_task(run_review, state, config)

    logger.info(
        "Queued review for PR #%d in %s (tenant: %s, action: %s)",
        state["pr_number"], state["repo_full_name"], tenant.name, action,
    )

    return {
        "status": "queued",
        "pr_number": state["pr_number"],
        "repo": state["repo_full_name"],
        "tenant": tenant.name,
    }
