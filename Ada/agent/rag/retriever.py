"""Ada Core API — RAG Retriever.

Searches Supabase pgvector for document chunks similar to a query.
Returns ranked results with metadata and relevance scores.

WHITEPAPER ref: Section 3 — context_loader, Section 6 — AgentBlueprint rag_config
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from agent.rag.embeddings import embed_text

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A document chunk retrieved from the vector store."""

    content: str
    metadata: dict[str, Any]
    similarity: float
    chunk_id: str


async def retrieve(
    query: str,
    tenant_id: str,
    top_k: int = 5,
    threshold: float = 0.7,
) -> list[RetrievedChunk]:
    """Search for document chunks relevant to a query.

    Uses pgvector cosine similarity via Supabase RPC.

    Args:
        query: The search query text.
        tenant_id: Tenant ID for RLS filtering.
        top_k: Maximum number of results to return.
        threshold: Minimum similarity score (0.0-1.0).

    Returns:
        List of RetrievedChunk sorted by similarity (highest first).
        Returns empty list if Supabase is not configured.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        logger.debug("Supabase not configured — skipping RAG retrieval")
        return []

    try:
        # Generate query embedding
        query_vector = await embed_text(query)

        # Call Supabase RPC function for vector similarity search
        rpc_url = f"{supabase_url}/rest/v1/rpc/match_documents"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query_embedding": query_vector,
            "match_threshold": threshold,
            "match_count": top_k,
            "p_tenant_id": tenant_id,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(rpc_url, headers=headers, json=payload)
            resp.raise_for_status()
            rows = resp.json()

        chunks = [
            RetrievedChunk(
                content=row["content"],
                metadata=row.get("metadata", {}),
                similarity=row.get("similarity", 0.0),
                chunk_id=str(row.get("id", "")),
            )
            for row in rows
        ]

        logger.info(
            "RAG retrieved %d chunks for tenant=%s (threshold=%.2f)",
            len(chunks), tenant_id, threshold,
        )
        return chunks

    except Exception:
        logger.exception("RAG retrieval failed — continuing without context")
        return []
