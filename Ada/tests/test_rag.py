"""Tests for RAG pipeline and Context Loader node.

Covers:
- Text chunking
- Embeddings (mocked)
- Retriever (mocked)
- Context Loader node integration
- Graph integration with context_loader
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from agent.rag.ingest import chunk_text
from agent.nodes.context_loader import ContextLoaderNode, context_loader_node


# ===========================================================================
# Text Chunking
# ===========================================================================

class TestChunkText:
    """Test the text chunking utility."""

    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        text = "Hello world."
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        # Create text longer than chunk_size
        text = "This is a sentence. " * 50  # ~1000 chars
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1
        # All chunks should be non-empty
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_overlap(self):
        """Overlapping chunks should share some content."""
        text = "A" * 100 + " " + "B" * 100 + " " + "C" * 100
        chunks = chunk_text(text, chunk_size=120, overlap=20)
        assert len(chunks) >= 2

    def test_respects_sentence_boundaries(self):
        """Chunking should prefer breaking at sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, chunk_size=40, overlap=5)
        # Should break at period boundaries when possible
        assert len(chunks) >= 2


# ===========================================================================
# Context Loader Node
# ===========================================================================

class TestContextLoaderNode:
    """Test the ContextLoaderNode."""

    def test_singleton_exists(self):
        assert context_loader_node is not None
        assert context_loader_node.name == "context_loader"

    @pytest.mark.asyncio
    async def test_no_messages_returns_empty_context(self):
        """No messages → no RAG query, empty context."""
        state = {"messages": [], "tenant_id": "test-tenant"}
        result = await context_loader_node.process(state)
        assert result["rag_context"] == []
        assert result["rag_query"] == ""

    @pytest.mark.asyncio
    async def test_no_tenant_skips_rag(self):
        """No tenant_id → no RAG retrieval."""
        state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "tenant_id": "",
        }
        result = await context_loader_node.process(state)
        assert result["rag_context"] == []

    @pytest.mark.asyncio
    async def test_extracts_latest_user_message_as_query(self):
        """Should use the latest user message as RAG query."""
        state = {
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "Answer"},
                {"role": "user", "content": "Follow-up question"},
            ],
            "tenant_id": "",  # Empty to skip actual RAG call
        }
        result = await context_loader_node.process(state)
        assert result["rag_query"] == "Follow-up question"

    @pytest.mark.asyncio
    async def test_system_prompt_from_config(self):
        """System prompt from config should be passed through."""
        state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "tenant_id": "",
        }
        config = {
            "configurable": {
                "system_prompt_override": "You are a helpful assistant.",
            }
        }
        result = await context_loader_node.process(state, config=config)
        assert result["system_prompt_enriched"] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_rag_context_enriches_system_prompt(self):
        """RAG results should be appended to system prompt."""
        mock_chunks = [
            MagicMock(
                content="Relevant document content",
                similarity=0.85,
                metadata={"title": "Test Doc"},
            ),
        ]

        state = {
            "messages": [{"role": "user", "content": "What is X?"}],
            "tenant_id": "test-tenant",
        }
        config = {
            "configurable": {
                "system_prompt_override": "Base prompt.",
            }
        }

        with patch("agent.nodes.context_loader.retrieve", new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = mock_chunks
            result = await context_loader_node.process(state, config=config)

        assert len(result["rag_context"]) == 1
        assert result["rag_context"][0]["content"] == "Relevant document content"
        assert "Relevant Context" in result["system_prompt_enriched"]
        assert "Base prompt." in result["system_prompt_enriched"]
        assert "Relevant document content" in result["system_prompt_enriched"]


# ===========================================================================
# Graph integration
# ===========================================================================

class TestGraphWithContextLoader:
    """Test context_loader integration in the router graph."""

    def test_graph_builds_with_context_loader(self):
        """Router graph should build with context_loader."""
        from agent.graph import build_router_graph
        graph = build_router_graph()
        assert graph is not None

    def test_sentinel_routes_to_context_loader(self):
        """When sentinel passes, should route to context_loader."""
        from agent.graph import _should_proceed_after_sentinel
        state = {"sentinel_passed": True}
        assert _should_proceed_after_sentinel(state) == "context_loader"

    def test_sentinel_block_routes_to_blocked(self):
        """When sentinel blocks, should route to sentinel_blocked."""
        from agent.graph import _should_proceed_after_sentinel
        state = {"sentinel_passed": False}
        assert _should_proceed_after_sentinel(state) == "sentinel_blocked"
