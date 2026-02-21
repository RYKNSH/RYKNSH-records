"""Velie QA Agent — FastAPI Webhook Server."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
import httpx

from agent.graph import qa_agent, QAState
from server.config import get_settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Velie QA Agent",
    description="AI-powered code review bot for RYKNSH records",
    version="0.1.0",
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

async def run_review(state: QAState) -> None:
    """Execute the LangGraph QA review pipeline in background."""
    pr_id = f"PR #{state['pr_number']} in {state['repo_full_name']}"
    try:
        logger.info("Starting review for %s", pr_id)
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
    return {"status": "ok", "service": "velie-qa-agent", "version": "0.1.0"}


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

    # 6. Enqueue background review
    background_tasks.add_task(run_review, state)

    logger.info(
        "Queued review for PR #%d in %s (action: %s)",
        state["pr_number"], state["repo_full_name"], action,
    )

    return {
        "status": "queued",
        "pr_number": state["pr_number"],
        "repo": state["repo_full_name"],
    }
