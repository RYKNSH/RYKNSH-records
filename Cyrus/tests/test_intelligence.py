"""Tests for Intelligence Layer nodes (mock mode)."""

import pytest

from nodes.intelligence.market_scanner import MarketScanner
from nodes.intelligence.icp_profiler import ICPProfiler
from nodes.intelligence.signal_detector import SignalDetector


@pytest.fixture
def b2b_state():
    return {
        "blueprint": {
            "business_model": "b2b",
            "entity_config": {"type": "organization", "industry": "saas", "size": "mid"},
        },
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


@pytest.fixture
def b2c_state():
    return {
        "blueprint": {
            "business_model": "b2c",
            "entity_config": {"type": "individual", "context": "fan"},
        },
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


class TestMarketScanner:
    @pytest.mark.asyncio
    async def test_returns_market_data(self, b2b_state):
        scanner = MarketScanner()
        result = await scanner(b2b_state)
        assert "market_data" in result
        data = result["market_data"]
        assert "market_trends" in data
        assert "competitor_landscape" in data
        assert "tam_sam_som" in data

    @pytest.mark.asyncio
    async def test_node_metrics(self, b2b_state):
        scanner = MarketScanner()
        result = await scanner(b2b_state)
        assert result["current_layer"] == "intelligence"
        assert result["current_node"] == "market_scanner"
        assert len(result["node_metrics"]) == 1
        assert result["node_metrics"][0]["success"] is True


class TestICPProfiler:
    @pytest.mark.asyncio
    async def test_returns_icp(self, b2b_state):
        # First run market scanner to get market_data
        scanner = MarketScanner()
        scan_result = await scanner(b2b_state)
        state = {**b2b_state, **scan_result}

        profiler = ICPProfiler()
        result = await profiler(state)
        assert "icp_profiles" in result
        assert len(result["icp_profiles"]) > 0
        profile = result["icp_profiles"][0]
        assert "icp_name" in profile
        assert "pain_points" in profile

    @pytest.mark.asyncio
    async def test_node_identity(self, b2b_state):
        profiler = ICPProfiler()
        result = await profiler(b2b_state)
        assert result["current_node"] == "icp_profiler"


class TestSignalDetector:
    @pytest.mark.asyncio
    async def test_returns_signals(self, b2b_state):
        detector = SignalDetector()
        result = await detector(b2b_state)
        assert "detected_signals" in result
        signals = result["detected_signals"]
        assert len(signals) > 0
        for signal in signals:
            assert "type" in signal
            assert "confidence" in signal
            assert "priority" in signal

    @pytest.mark.asyncio
    async def test_signal_has_recommended_action(self, b2b_state):
        detector = SignalDetector()
        result = await detector(b2b_state)
        for signal in result["detected_signals"]:
            assert "recommended_action" in signal
