"""Velie QA Agent — LangGraph Code Review Graph.

The core loop: fetch_diff → review_code → generate_suggestions → post_review
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypedDict

from langchain_core.runnables import RunnableConfig

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.github_app import get_auth_token
from agent.prompts import (
    REVIEW_USER_TEMPLATE,
    SUGGESTION_SYSTEM_PROMPT,
    SUGGESTION_USER_TEMPLATE,
    SYSTEM_PROMPT,
)
from agent.sanitizer import sanitize_diff
from agent.suggestions import build_review_comments, parse_suggestions
from server.config import get_settings

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)

# Shared HTTP client — reused across node invocations for connection pooling
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create a shared httpx.AsyncClient for GitHub API calls."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class QAState(TypedDict):
    """State that flows through the QA review graph."""

    # Input
    pr_number: int
    repo_full_name: str  # e.g. "RYKNSH/RYKNSH-records"
    pr_title: str
    pr_author: str
    pr_body: str
    installation_id: int | None

    # Intermediate
    diff: str

    # Output
    review_body: str
    suggestions: list[dict]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def fetch_diff(state: QAState) -> dict:
    """Fetch the PR diff from GitHub API."""
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    token = await get_auth_token(state.get("installation_id"))
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    client = _get_http_client()
    resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    diff_text = resp.text
    original_len = len(diff_text)

    # Truncate very large diffs to avoid token limits
    max_chars = 60_000
    if original_len > max_chars:
        diff_text = diff_text[:max_chars] + "\n\n... [diff truncated due to size]"
        logger.warning(
            "Diff truncated for PR #%d in %s (original: %d chars)",
            pr_number, repo, original_len,
        )

    logger.info("Fetched diff for PR #%d (%d chars)", pr_number, len(diff_text))
    return {"diff": sanitize_diff(diff_text)}


async def review_code(state: QAState, config: RunnableConfig) -> dict:
    """Use Claude to review the code diff."""
    cfg = get_settings()

    # Check for tenant-specific model override via config
    tenant_model = (config.get("configurable", {}) or {}).get("llm_model")
    model_name = tenant_model or "claude-sonnet-4-20250514"

    llm = ChatAnthropic(
        model=model_name,
        api_key=cfg.anthropic_api_key,
        max_tokens=4096,
        temperature=0.1,
    )

    user_prompt = REVIEW_USER_TEMPLATE.format(
        pr_number=state["pr_number"],
        repo_full_name=state["repo_full_name"],
        pr_title=state["pr_title"],
        pr_author=state["pr_author"],
        pr_body=state.get("pr_body", "No description provided."),
        diff=state["diff"],
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)
    review_body = response.content

    logger.info("Generated review for PR #%d (%d chars)", state["pr_number"], len(review_body))
    return {"review_body": review_body}


async def generate_suggestions(state: QAState, config: RunnableConfig) -> dict:
    """Generate concrete code fix suggestions based on the review."""
    # Check if auto_suggest is enabled for this tenant
    auto_suggest = (config.get("configurable", {}) or {}).get("auto_suggest", True)
    if not auto_suggest:
        logger.info("Suggestions disabled for this tenant, skipping")
        return {"suggestions": []}

    if not state.get("review_body"):
        return {"suggestions": []}

    cfg = get_settings()
    tenant_model = (config.get("configurable", {}) or {}).get("llm_model")
    model_name = tenant_model or "claude-sonnet-4-20250514"

    llm = ChatAnthropic(
        model=model_name,
        api_key=cfg.anthropic_api_key,
        max_tokens=4096,
        temperature=0.0,  # Deterministic for code suggestions
    )

    user_prompt = SUGGESTION_USER_TEMPLATE.format(
        review_body=state["review_body"],
        diff=state["diff"],
    )

    messages = [
        SystemMessage(content=SUGGESTION_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        suggestions = parse_suggestions(response.content)
        suggestion_dicts = [s.__dict__ for s in suggestions]
        logger.info(
            "Generated %d suggestions for PR #%d",
            len(suggestion_dicts), state["pr_number"],
        )
        return {"suggestions": suggestion_dicts}
    except Exception:
        logger.exception("Failed to generate suggestions, continuing without")
        return {"suggestions": []}


async def post_review(state: QAState) -> dict:
    """Post the review with inline suggestions on the PR."""
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]

    token = await get_auth_token(state.get("installation_id"))
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    client = _get_http_client()

    # Build inline suggestion comments
    suggestions = state.get("suggestions", [])
    review_comments: list[dict] = []
    if suggestions:
        parsed = [__import__('agent.suggestions', fromlist=['Suggestion']).Suggestion(**s) for s in suggestions]
        review_comments = build_review_comments(parsed, state["diff"])

    if review_comments:
        # Use PR Review API with inline suggestions
        review_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"

        # Get latest commit SHA for the review
        pr_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        pr_resp = await client.get(pr_url, headers=headers)
        pr_resp.raise_for_status()
        commit_sha = pr_resp.json()["head"]["sha"]

        review_body = f"## 🔍 Velie Code Review\n\n{state['review_body']}\n\n---\n✨ **{len(review_comments)} auto-fix suggestion(s)** posted inline. Click \"Apply suggestion\" to fix."

        review_payload = {
            "commit_id": commit_sha,
            "body": review_body,
            "event": "COMMENT",
            "comments": review_comments,
        }

        try:
            resp = await client.post(review_url, headers=headers, json=review_payload)
            resp.raise_for_status()
            logger.info(
                "Posted review with %d suggestions on PR #%d in %s",
                len(review_comments), pr_number, repo,
            )
        except Exception:
            logger.exception("Failed to post review with suggestions, falling back to comment")
            # Fallback to simple comment
            await _post_simple_comment(client, repo, pr_number, state["review_body"], headers)
    else:
        # No suggestions — post as regular comment
        await _post_simple_comment(client, repo, pr_number, state["review_body"], headers)

    # --- Save review ---
    await _save_review_to_supabase(state)

    return {}


async def _post_simple_comment(
    client: httpx.AsyncClient,
    repo: str,
    pr_number: int,
    review_body: str,
    headers: dict,
) -> None:
    """Fallback: post review as a simple issue comment."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    comment_body = f"## 🔍 Velie Code Review\n\n{review_body}"
    resp = await client.post(url, headers=headers, json={"body": comment_body})
    resp.raise_for_status()
    logger.info("Posted review comment on PR #%d in %s", pr_number, repo)


async def _save_review_to_supabase(state: QAState) -> None:
    """Persist review result. Tries Supabase first, falls back to local JSON."""
    import json
    from pathlib import Path
    from datetime import datetime, timezone

    review_record = {
        "id": f"{state['repo_full_name']}-{state['pr_number']}-{int(datetime.now(timezone.utc).timestamp())}",
        "pr_number": state["pr_number"],
        "repo_full_name": state["repo_full_name"],
        "pr_title": state.get("pr_title", ""),
        "pr_author": state.get("pr_author", "unknown"),
        "severity": _detect_severity(state["review_body"]),
        "review_body": state["review_body"][:10000],
        "installation_id": state.get("installation_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Try Supabase first
    cfg = get_settings()
    if cfg.supabase_url and cfg.supabase_anon_key:
        try:
            client = _get_http_client()
            resp = await client.post(
                f"{cfg.supabase_url}/rest/v1/reviews",
                headers={
                    "apikey": cfg.supabase_anon_key,
                    "Authorization": f"Bearer {cfg.supabase_anon_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=review_record,
            )
            resp.raise_for_status()
            logger.info("Saved review to Supabase (PR #%d)", state["pr_number"])
            return
        except Exception:
            logger.warning("Supabase save failed — falling back to local JSON")

    # Fallback: local JSON file
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    reviews_file = data_dir / "reviews.json"

    existing: list = []
    if reviews_file.exists():
        try:
            existing = json.loads(reviews_file.read_text())
        except Exception:
            existing = []

    existing.insert(0, review_record)  # newest first
    existing = existing[:500]  # cap at 500

    reviews_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    logger.info("Saved review to local JSON (PR #%d, total=%d)", state["pr_number"], len(existing))


def _detect_severity(review_body: str) -> str:
    """Auto-detect severity from review body content."""
    body_lower = review_body.lower()
    if "🔴" in review_body or "critical" in body_lower:
        return "critical"
    if "🟡" in review_body or "warning" in body_lower:
        return "warning"
    return "clean"


# ---------------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------------

def build_qa_graph(checkpointer: AsyncPostgresSaver | None = None) -> CompiledStateGraph:
    """Build the QA review graph: fetch_diff → review_code → generate_suggestions → post_review.

    Args:
        checkpointer: Optional AsyncPostgresSaver for stateful persistence.
                      If None, the graph runs in stateless mode.
    """
    graph = StateGraph(QAState)

    graph.add_node("fetch_diff", fetch_diff)
    graph.add_node("review_code", review_code)
    graph.add_node("generate_suggestions", generate_suggestions)
    graph.add_node("post_review", post_review)

    graph.set_entry_point("fetch_diff")
    graph.add_edge("fetch_diff", "review_code")
    graph.add_edge("review_code", "generate_suggestions")
    graph.add_edge("generate_suggestions", "post_review")
    graph.add_edge("post_review", END)

    return graph.compile(checkpointer=checkpointer)


# Compiled graph — starts stateless, rebuilt with checkpointer via lifespan
qa_agent = build_qa_graph()


def rebuild_with_checkpointer(checkpointer: AsyncPostgresSaver | None) -> None:
    """Rebuild the global qa_agent with a checkpointer (called during lifespan)."""
    global qa_agent
    if checkpointer is not None:
        qa_agent = build_qa_graph(checkpointer=checkpointer)
        logger.info("QA Agent rebuilt with AsyncPostgresSaver (stateful mode)")
    else:
        logger.info("QA Agent running in stateless mode (no checkpointer)")
