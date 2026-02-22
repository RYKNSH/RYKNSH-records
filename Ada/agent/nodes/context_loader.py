"""Ada Core API — Context Loader Node.

Enriches the graph state with tenant-specific context:
1. System prompt injection (tenant persona)
2. RAG retrieval (relevant document chunks)

Runs after sentinel, before select_model.

WHITEPAPER ref: Section 3 — context_loader, Section 7 — Quality Tiers
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from agent.nodes.base import AdaNode
from agent.rag.retriever import retrieve, RetrievedChunk

logger = logging.getLogger(__name__)


class ContextLoaderNode(AdaNode):
    """Context enrichment node: injects system prompt and RAG results.

    State updates:
        rag_context (list[dict]): Retrieved document chunks
        rag_query (str): The query used for RAG search
    """

    name = "context_loader"

    async def process(
        self,
        state: dict,
        config: RunnableConfig | None = None,
    ) -> dict:
        """Load tenant context and RAG results into state."""

        tenant_id = state.get("tenant_id", "")
        messages = state.get("messages", [])

        # Extract system prompt from config
        system_prompt = None
        rag_collections = None
        rag_threshold = 0.7

        if config and "configurable" in config:
            system_prompt = config["configurable"].get("system_prompt_override")
            rag_config = config["configurable"].get("rag_config", {})
            if rag_config:
                rag_collections = rag_config.get("collections")
                rag_threshold = rag_config.get("relevance_threshold", 0.7)

        # -----------------------------------------------------------------
        # 1. RAG retrieval — search for relevant context
        # -----------------------------------------------------------------
        rag_context: list[dict[str, Any]] = []
        rag_query = ""

        # Use the latest user message as the RAG query
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            rag_query = user_messages[-1].get("content", "")

        if rag_query and tenant_id:
            chunks = await retrieve(
                query=rag_query,
                tenant_id=tenant_id,
                top_k=5,
                threshold=rag_threshold,
            )
            if chunks:
                rag_context = [
                    {
                        "content": c.content,
                        "similarity": c.similarity,
                        "metadata": c.metadata,
                    }
                    for c in chunks
                ]
                logger.info(
                    "Context loader: %d RAG chunks retrieved (tenant=%s)",
                    len(rag_context), tenant_id,
                )

        # -----------------------------------------------------------------
        # 2. System prompt enrichment — append RAG context
        # -----------------------------------------------------------------
        enriched_system_prompt = system_prompt or ""

        if rag_context:
            context_text = "\n\n---\n\n".join(
                f"[Source: {c['metadata'].get('title', 'document')}]\n{c['content']}"
                for c in rag_context
            )
            rag_section = (
                "\n\n## Relevant Context\n"
                "Use the following information to inform your response:\n\n"
                f"{context_text}"
            )
            enriched_system_prompt = enriched_system_prompt + rag_section

        return {
            "rag_context": rag_context,
            "rag_query": rag_query,
            "system_prompt_enriched": enriched_system_prompt if enriched_system_prompt else None,
        }


# Module-level singleton
context_loader_node = ContextLoaderNode()
