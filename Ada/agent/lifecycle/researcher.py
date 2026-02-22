"""Ada Core API — Researcher Node.

Gathers relevant knowledge for a given goal using RAG and scoring.
Part of the Lifecycle pipeline: goal_intake → researcher → debater.

Responsibilities:
1. Query formulation from structured goal
2. RAG search execution
3. Relevance scoring
4. Source diversity assessment

WHITEPAPER ref: Section 2 — researcher
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def formulate_queries(goal_result: dict[str, Any]) -> list[str]:
    """Generate search queries from goal intake result.

    Creates multiple queries to ensure diverse retrieval.
    """
    goal_text = goal_result.get("goal_text", "")
    task_type = goal_result.get("task_type", "qa")
    skills = goal_result.get("required_skills", [])

    queries = [goal_text]  # Primary: raw goal

    # Skill-specific query
    if skills:
        skill_query = f"{task_type}: {', '.join(skills)} — {goal_text[:100]}"
        queries.append(skill_query)

    # Task-type specific enrichment
    enrichment_map = {
        "code": f"implementation guide: {goal_text[:100]}",
        "analysis": f"analysis framework: {goal_text[:100]}",
        "creative": f"creative approach: {goal_text[:100]}",
        "qa": f"explanation: {goal_text[:100]}",
    }
    if task_type in enrichment_map:
        queries.append(enrichment_map[task_type])

    return queries


def score_relevance(
    query: str,
    result: dict[str, Any],
) -> float:
    """Score the relevance of a retrieved document to the query.

    Simple keyword overlap heuristic (LLM-based scoring in M3+).
    Returns 0.0-1.0.
    """
    content = result.get("content", "").lower()
    query_words = set(query.lower().split())
    if not query_words:
        return 0.0

    content_words = set(content.split())
    overlap = query_words & content_words
    return min(len(overlap) / max(len(query_words), 1), 1.0)


def assess_diversity(results: list[dict[str, Any]]) -> float:
    """Assess source diversity of retrieved results.

    Higher diversity = more varied information sources.
    Returns 0.0-1.0.
    """
    if not results:
        return 0.0

    sources = set()
    for r in results:
        source = r.get("metadata", {}).get("source", r.get("source", "unknown"))
        sources.add(source)

    return min(len(sources) / max(len(results), 1), 1.0)


async def research(
    goal_result: dict[str, Any],
    tenant_id: str = "",
) -> dict[str, Any]:
    """Execute research for a given goal.

    Uses RAG retrieval with multiple queries and relevance scoring.
    Falls back gracefully when RAG is not available.
    """
    queries = formulate_queries(goal_result)

    all_results: list[dict[str, Any]] = []
    scored_results: list[dict[str, Any]] = []

    # Attempt RAG retrieval for each query
    for query in queries:
        try:
            from agent.rag.retriever import retrieve
            results = await retrieve(query, tenant_id=tenant_id, top_k=3)
            for r in results:
                relevance = score_relevance(query, r)
                scored_results.append({
                    **r,
                    "relevance_score": relevance,
                    "query": query,
                })
                all_results.append(r)
        except Exception:
            logger.debug("RAG retrieval failed for query: %s", query[:50])

    # Deduplicate by content
    seen_content: set[str] = set()
    unique_results: list[dict[str, Any]] = []
    for r in scored_results:
        content_key = r.get("content", "")[:100]
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_results.append(r)

    # Sort by relevance
    unique_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    diversity = assess_diversity(all_results)

    research_result = {
        "queries": queries,
        "results": unique_results[:10],  # Top 10
        "total_found": len(all_results),
        "unique_count": len(unique_results),
        "diversity_score": diversity,
        "has_context": len(unique_results) > 0,
    }

    logger.info(
        "Research: %d queries, %d results, diversity=%.2f",
        len(queries), len(unique_results), diversity,
    )

    return research_result
