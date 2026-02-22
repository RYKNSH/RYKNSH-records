"""Tests for Aggregator node and parallel execution foundations.

Covers:
- AggregatorNode passthrough (single result)
- Weighted merge (multiple results)
- Contradiction detection
- Graph integration
"""

import pytest

from agent.nodes.aggregator import AggregatorNode, aggregator_node


class TestAggregatorNode:
    """Test the AggregatorNode."""

    def test_singleton_exists(self):
        assert aggregator_node is not None
        assert aggregator_node.name == "aggregator"

    @pytest.mark.asyncio
    async def test_single_result_passthrough(self):
        """Single result should pass through unchanged."""
        state = {
            "response_content": "This is the LLM response.",
            "parallel_results": [],
        }
        result = await aggregator_node.process(state)
        assert result["aggregated_content"] == "This is the LLM response."
        assert result["aggregation_method"] == "passthrough"

    @pytest.mark.asyncio
    async def test_empty_response_passthrough(self):
        """Empty response should passthrough as empty."""
        state = {"response_content": "", "parallel_results": []}
        result = await aggregator_node.process(state)
        assert result["aggregated_content"] == ""
        assert result["aggregation_method"] == "passthrough"

    @pytest.mark.asyncio
    async def test_multiple_results_uses_weighted_merge(self):
        """Multiple parallel results should trigger weighted merge."""
        state = {
            "response_content": "",
            "parallel_results": [
                {"content": "Result A with good detail.", "validation_score": 0.9},
                {"content": "Result B shorter.", "validation_score": 0.5},
            ],
        }
        result = await aggregator_node.process(state)
        assert result["aggregation_method"] == "weighted_merge"
        assert len(result["aggregated_content"]) > 0


class TestContradictionDetection:
    """Test contradiction detection between parallel results."""

    def test_no_contradictions(self):
        results = [
            {"content": "Python is great for scripting."},
            {"content": "Python is widely used in data science."},
        ]
        contradictions = AggregatorNode.detect_contradictions(results)
        assert len(contradictions) == 0

    def test_detects_yes_no_contradiction(self):
        results = [
            {"content": "Yes, this approach is correct."},
            {"content": "No, this approach has issues."},
        ]
        contradictions = AggregatorNode.detect_contradictions(results)
        assert len(contradictions) > 0

    def test_detects_true_false_contradiction(self):
        results = [
            {"content": "This statement is true."},
            {"content": "This statement is false."},
        ]
        contradictions = AggregatorNode.detect_contradictions(results)
        assert len(contradictions) > 0

    def test_single_result_no_contradictions(self):
        results = [{"content": "Only one result."}]
        assert AggregatorNode.detect_contradictions(results) == []

    def test_empty_results_no_contradictions(self):
        assert AggregatorNode.detect_contradictions([]) == []


class TestWeightedMerge:
    """Test the weighted merge logic."""

    def test_single_result(self):
        results = [{"content": "Only result"}]
        merged = AggregatorNode._weighted_merge(results)
        assert merged == "Only result"

    def test_empty_results(self):
        assert AggregatorNode._weighted_merge([]) == ""

    def test_selects_best_by_score(self):
        """Should select the result with highest weighted score."""
        results = [
            {"content": "Short", "validation_score": 0.5, "time_ms": 100, "cost_usd": 0.001},
            {"content": "A much longer and more detailed response that covers the topic thoroughly.",
             "validation_score": 0.95, "time_ms": 500, "cost_usd": 0.01},
        ]
        merged = AggregatorNode._weighted_merge(results)
        # Longer, higher validation should win
        assert "detailed" in merged
