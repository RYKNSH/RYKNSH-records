"""Tests for the LangGraph QA Agent graph structure."""


class TestGraphStructure:
    """Verify the graph is correctly constructed."""

    def test_graph_compiles(self):
        """The graph should compile without errors."""
        from agent.graph import build_qa_graph
        graph = build_qa_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        """The graph should contain fetch_diff, review_code, post_review."""
        from agent.graph import build_qa_graph
        graph = build_qa_graph()
        node_names = set(graph.get_graph().nodes.keys())
        assert "fetch_diff" in node_names
        assert "review_code" in node_names
        assert "post_review" in node_names

    def test_qa_state_type(self):
        """QAState should be a valid TypedDict."""
        from agent.graph import QAState
        state: QAState = {
            "pr_number": 1,
            "repo_full_name": "test/repo",
            "pr_title": "Test",
            "pr_author": "author",
            "pr_body": "body",
            "installation_id": None,
            "diff": "",
            "review_body": "",
        }
        assert state["pr_number"] == 1
        assert state["repo_full_name"] == "test/repo"
