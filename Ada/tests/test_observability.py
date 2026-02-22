"""Tests for Observability module.

Covers:
- NodeMetrics data structure
- MetricsCollector aggregation
- timed_node_execution wrapper
- ResourceLimits
- AdaNode observability wrapper
"""

import asyncio
import pytest
import time

from agent.observability import (
    NodeMetrics,
    RequestMetrics,
    MetricsCollector,
    ResourceLimits,
    estimate_cost,
    timed_node_execution,
)


class TestNodeMetrics:
    """Test NodeMetrics data structure."""

    def test_default_values(self):
        m = NodeMetrics(node_name="test")
        assert m.node_name == "test"
        assert m.execution_time_ms == 0.0
        assert m.success is True
        assert m.error is None

    def test_to_dict(self):
        m = NodeMetrics(
            node_name="sentinel",
            execution_time_ms=1.234,
            tokens_used=100,
            success=True,
        )
        d = m.to_dict()
        assert d["node_name"] == "sentinel"
        assert d["execution_time_ms"] == 1.23
        assert d["tokens_used"] == 100

    def test_error_metrics(self):
        m = NodeMetrics(node_name="test", success=False, error="timeout")
        d = m.to_dict()
        assert d["success"] is False
        assert d["error"] == "timeout"


class TestMetricsCollector:
    """Test MetricsCollector aggregation."""

    def test_empty_collector(self):
        c = MetricsCollector(request_id="abc")
        assert c.total_time_ms == 0.0
        assert c.total_tokens == 0
        assert c.node_count == 0

    def test_record_metrics(self):
        c = MetricsCollector(request_id="abc", tenant_id="xyz")
        c.record(NodeMetrics(node_name="sentinel", execution_time_ms=1.0, tokens_used=0))
        c.record(NodeMetrics(node_name="invoke_llm", execution_time_ms=500.0, tokens_used=1000))
        assert c.node_count == 2
        assert c.total_time_ms == 501.0
        assert c.total_tokens == 1000

    def test_summary(self):
        c = MetricsCollector(request_id="req1", tenant_id="t1")
        c.record(NodeMetrics(node_name="sentinel", execution_time_ms=2.5))
        summary = c.summary()
        assert summary["request_id"] == "req1"
        assert summary["tenant_id"] == "t1"
        assert len(summary["nodes"]) == 1


class TestEstimateCost:
    """Test cost estimation."""

    def test_known_model(self):
        cost = estimate_cost("gpt-4o", 1000)
        assert cost == 0.01  # $0.010 per 1K tokens

    def test_unknown_model_uses_default(self):
        cost = estimate_cost("unknown-model", 1000)
        assert cost == 0.01  # Default rate


class TestTimedNodeExecution:
    """Test timed_node_execution wrapper."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        async def mock_node():
            return {"result": "ok"}

        result = await timed_node_execution("test_node", mock_node())
        assert result["result"] == "ok"

    @pytest.mark.asyncio
    async def test_records_metrics(self):
        collector = MetricsCollector(request_id="test")

        async def mock_node():
            await asyncio.sleep(0.01)
            return {"result": "ok"}

        await timed_node_execution("test_node", mock_node(), collector=collector)
        assert collector.node_count == 1
        assert collector.total_time_ms > 0

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        async def slow_node():
            await asyncio.sleep(10)
            return {}

        limits = ResourceLimits(timeout_sec=0.05)
        with pytest.raises(asyncio.TimeoutError):
            await timed_node_execution("slow", slow_node(), limits=limits)

    @pytest.mark.asyncio
    async def test_error_records_failure(self):
        collector = MetricsCollector(request_id="test")

        async def failing_node():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await timed_node_execution("fails", failing_node(), collector=collector)
        assert collector.node_count == 1
        summary = collector.summary()
        assert summary["nodes"][0]["success"] is False


class TestAdaNodeObservabilityWrapper:
    """Test that AdaNode.as_graph_node() adds observability."""

    @pytest.mark.asyncio
    async def test_wrapper_records_metrics(self):
        """as_graph_node wrapper should add node_metrics to result."""
        from agent.nodes.sentinel import sentinel_node

        state = {
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "node_metrics": [],
        }
        wrapped_fn = sentinel_node.as_graph_node()
        result = await wrapped_fn(state)
        assert "node_metrics" in result
        assert len(result["node_metrics"]) == 1
        assert result["node_metrics"][0]["node_name"] == "sentinel"
        assert result["node_metrics"][0]["execution_time_ms"] > 0
        assert result["node_metrics"][0]["success"] is True
