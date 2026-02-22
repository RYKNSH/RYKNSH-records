"""Integration test for Intelligence Layer graph."""

import pytest

from engine.graph import run_intelligence


@pytest.fixture
def b2b_blueprint():
    return {
        "blueprint_id": "test-b2b",
        "tenant_id": "test-tenant",
        "business_model": "b2b",
        "entity_config": {
            "type": "organization",
            "industry": "saas",
            "size": "mid",
        },
    }


@pytest.fixture
def b2c_blueprint():
    return {
        "blueprint_id": "test-b2c",
        "tenant_id": "test-tenant",
        "business_model": "b2c",
        "entity_config": {
            "type": "individual",
            "context": "fan",
            "demographics": {"age": "15-35"},
        },
    }


class TestIntelligenceGraph:
    @pytest.mark.asyncio
    async def test_full_pipeline_b2b(self, b2b_blueprint):
        result = await run_intelligence(b2b_blueprint)
        # All 3 nodes should have produced output
        assert "market_data" in result
        assert "icp_profiles" in result
        assert "detected_signals" in result
        # 3 nodes should have metrics
        assert len(result.get("node_metrics", [])) == 3

    @pytest.mark.asyncio
    async def test_full_pipeline_b2c(self, b2c_blueprint):
        result = await run_intelligence(b2c_blueprint)
        assert "market_data" in result
        assert "icp_profiles" in result
        assert "detected_signals" in result

    @pytest.mark.asyncio
    async def test_no_errors(self, b2b_blueprint):
        result = await run_intelligence(b2b_blueprint)
        assert result.get("errors", []) == []

    @pytest.mark.asyncio
    async def test_node_execution_order(self, b2b_blueprint):
        result = await run_intelligence(b2b_blueprint)
        metrics = result.get("node_metrics", [])
        node_names = [m["node"] for m in metrics]
        assert node_names == ["market_scanner", "icp_profiler", "signal_detector"]
