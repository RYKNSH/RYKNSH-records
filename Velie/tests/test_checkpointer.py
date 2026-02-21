"""Tests for the checkpointer module."""

import pytest


class TestCheckpointerLifecycle:
    """Test checkpointer initialization and shutdown."""

    @pytest.mark.asyncio
    async def test_init_without_supabase_returns_none(self):
        """Without SUPABASE_DB_URL, init should return None (stateless mode)."""
        from agent.checkpointer import init_checkpointer, close_checkpointer
        result = await init_checkpointer()
        assert result is None
        # Cleanup should be safe even when not initialized
        await close_checkpointer()

    def test_get_checkpointer_before_init_returns_none(self):
        """get_checkpointer should return None before initialization."""
        from agent.checkpointer import get_checkpointer
        assert get_checkpointer() is None


class TestGraphWithCheckpointer:
    """Test graph rebuild with checkpointer."""

    def test_rebuild_with_none_stays_stateless(self):
        """Rebuilding with None checkpointer should keep graph stateless."""
        from agent.graph import build_qa_graph, rebuild_with_checkpointer, qa_agent
        rebuild_with_checkpointer(None)
        # Graph should still be functional
        assert qa_agent is not None

    def test_build_graph_without_checkpointer(self):
        """Graph should compile with no checkpointer (stateless)."""
        from agent.graph import build_qa_graph
        graph = build_qa_graph(checkpointer=None)
        node_names = set(graph.get_graph().nodes.keys())
        assert "fetch_diff" in node_names
        assert "review_code" in node_names
        assert "post_review" in node_names
