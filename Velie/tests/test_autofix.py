"""Tests for the auto-fix module."""

import pytest

from agent.autofix import should_auto_fix


class TestShouldAutoFix:
    """Test threshold-based auto-fix gating."""

    def test_off_never_triggers(self):
        assert should_auto_fix("critical", "off") is False
        assert should_auto_fix("warning", "off") is False
        assert should_auto_fix("clean", "off") is False

    def test_critical_threshold_critical_severity(self):
        assert should_auto_fix("critical", "critical") is True

    def test_critical_threshold_warning_severity(self):
        assert should_auto_fix("warning", "critical") is False

    def test_critical_threshold_clean_severity(self):
        assert should_auto_fix("clean", "critical") is False

    def test_warning_threshold_critical_severity(self):
        assert should_auto_fix("critical", "warning") is True

    def test_warning_threshold_warning_severity(self):
        assert should_auto_fix("warning", "warning") is True

    def test_warning_threshold_clean_severity(self):
        assert should_auto_fix("clean", "warning") is False

    def test_unknown_severity(self):
        assert should_auto_fix("unknown", "critical") is False

    def test_unknown_threshold(self):
        assert should_auto_fix("critical", "unknown") is True


class TestGraphWithAutoFix:
    """Verify the graph includes the auto-fix node."""

    def test_graph_has_create_fix_pr_node(self):
        from agent.graph import build_qa_graph
        graph = build_qa_graph()
        node_names = set(graph.get_graph().nodes.keys())
        assert "create_fix_pr" in node_names

    def test_graph_has_all_phase2_nodes(self):
        from agent.graph import build_qa_graph
        graph = build_qa_graph()
        node_names = set(graph.get_graph().nodes.keys())
        expected = {"fetch_diff", "review_code", "generate_suggestions", "post_review", "create_fix_pr"}
        assert expected.issubset(node_names)


class TestShouldFix:
    """Test the should_fix router function."""

    def test_returns_end_when_no_suggestions(self):
        from agent.graph import should_fix
        state = {"review_body": "🔴 Critical issue", "suggestions": []}
        assert should_fix(state) == "end"

    def test_returns_create_fix_pr_for_critical(self):
        from agent.graph import should_fix
        state = {
            "review_body": "🔴 Critical: SQL injection",
            "suggestions": [{"path": "a.py", "line": 1, "original": "x", "suggested": "y", "reason": "fix"}],
        }
        assert should_fix(state) == "create_fix_pr"

    def test_returns_create_fix_pr_for_warning(self):
        from agent.graph import should_fix
        state = {
            "review_body": "🟡 Warning: missing error handling",
            "suggestions": [{"path": "a.py", "line": 1, "original": "x", "suggested": "y", "reason": "fix"}],
        }
        assert should_fix(state) == "create_fix_pr"

    def test_returns_end_for_clean(self):
        from agent.graph import should_fix
        state = {
            "review_body": "Code looks good! No issues found.",
            "suggestions": [{"path": "a.py", "line": 1, "original": "x", "suggested": "y", "reason": "fix"}],
        }
        assert should_fix(state) == "end"
