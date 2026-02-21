"""Velie QA Agent — LangGraph Code Review Graph.

The core loop: fetch_diff → review_code → post_review
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

from agent.prompts import REVIEW_USER_TEMPLATE, SYSTEM_PROMPT
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


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

async def fetch_diff(state: QAState) -> dict:
    """Fetch the PR diff from GitHub API."""
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    cfg = get_settings()
    headers = {
        "Authorization": f"Bearer {cfg.github_token}",
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
    return {"diff": diff_text}


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


async def post_review(state: QAState) -> dict:
    """Post the review as a comment on the PR."""
    repo = state["repo_full_name"]
    pr_number = state["pr_number"]
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    cfg = get_settings()
    headers = {
        "Authorization": f"Bearer {cfg.github_token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    comment_body = f"## 🔍 Velie Code Review\n\n{state['review_body']}"

    client = _get_http_client()
    resp = await client.post(url, headers=headers, json={"body": comment_body})
    resp.raise_for_status()

    logger.info("Posted review comment on PR #%d in %s", pr_number, repo)
    return {}


# ---------------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------------

def build_qa_graph(checkpointer: AsyncPostgresSaver | None = None) -> CompiledStateGraph:
    """Build the QA review graph: fetch_diff → review_code → post_review.

    Args:
        checkpointer: Optional AsyncPostgresSaver for stateful persistence.
                      If None, the graph runs in stateless mode.
    """
    graph = StateGraph(QAState)

    graph.add_node("fetch_diff", fetch_diff)
    graph.add_node("review_code", review_code)
    graph.add_node("post_review", post_review)

    graph.set_entry_point("fetch_diff")
    graph.add_edge("fetch_diff", "review_code")
    graph.add_edge("review_code", "post_review")
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
