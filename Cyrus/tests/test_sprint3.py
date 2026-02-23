"""Tests for Sprint 3: Content & Campaign nodes."""

import pytest

from nodes.acquisition.content_architect import ContentArchitect
from nodes.acquisition.campaign_orchestrator import CampaignOrchestrator
from nodes.acquisition.viral_engineer import ViralEngineer
from nodes.acquisition.ad_optimizer import AdOptimizer
from engine.graph import run_growth


@pytest.fixture
def b2b_state():
    return {
        "blueprint": {
            "business_model": "b2b",
            "tenant_id": "test",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {"personalization_depth": "l2_context", "method": "challenger"},
            "acquisition_config": {
                "channels": {"linkedin": 0.4, "google": 0.3, "meta": 0.2, "x": 0.1},
            },
        },
        "market_data": {"market_trends": [{"trend": "AI sales", "relevance": 0.9}]},
        "icp_profiles": [{"icp_name": "Growth CTO", "pain_points": ["slow pipeline"]}],
        "detected_signals": [{"type": "hiring", "confidence": 0.85}],
        "outbound_messages": [{"subject": "test", "body": "hello"}],
        "inbound_magnets": [{"title": "Report", "strategy": "authority_building"}],
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


class TestContentArchitect:
    @pytest.mark.asyncio
    async def test_returns_content_plan(self, b2b_state):
        node = ContentArchitect()
        result = await node(b2b_state)
        assert "content_plan" in result
        assert len(result["content_plan"]) > 0
        for item in result["content_plan"]:
            assert "type" in item
            assert "title" in item
            assert "hook" in item

    @pytest.mark.asyncio
    async def test_has_content_calendar(self, b2b_state):
        node = ContentArchitect()
        result = await node(b2b_state)
        assert "content_calendar" in result


class TestViralEngineer:
    @pytest.mark.asyncio
    async def test_returns_strategies(self, b2b_state):
        node = ViralEngineer()
        result = await node(b2b_state)
        assert "viral_strategies" in result
        assert len(result["viral_strategies"]) > 0
        for s in result["viral_strategies"]:
            assert "virality_score" in s
            assert "platform" in s

    @pytest.mark.asyncio
    async def test_has_trend_signals(self, b2b_state):
        node = ViralEngineer()
        result = await node(b2b_state)
        assert "trend_signals" in result


class TestCampaignOrchestrator:
    @pytest.mark.asyncio
    async def test_returns_campaign(self, b2b_state):
        node = CampaignOrchestrator()
        result = await node(b2b_state)
        assert "campaign" in result
        campaign = result["campaign"]
        assert "name" in campaign
        assert "channels" in campaign
        assert "sequence" in campaign

    @pytest.mark.asyncio
    async def test_has_success_metrics(self, b2b_state):
        node = CampaignOrchestrator()
        result = await node(b2b_state)
        assert "success_metrics" in result["campaign"]


class TestAdOptimizer:
    @pytest.mark.asyncio
    async def test_returns_ad_plan(self, b2b_state):
        node = AdOptimizer()
        result = await node(b2b_state)
        assert "ad_plan" in result
        plan = result["ad_plan"]
        assert "allocation" in plan
        assert len(plan["allocation"]) > 0

    @pytest.mark.asyncio
    async def test_has_optimization_rules(self, b2b_state):
        node = AdOptimizer()
        result = await node(b2b_state)
        assert "optimization_rules" in result["ad_plan"]


class TestFullGrowthGraph:
    @pytest.mark.asyncio
    async def test_full_pipeline_with_conversion(self):
        blueprint = {
            "blueprint_id": "test",
            "tenant_id": "test",
            "business_model": "b2b",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {"method": "challenger"},
            "acquisition_config": {"channels": {"linkedin": 0.5}},
        }
        result = await run_growth(blueprint)

        # All sprint outputs present
        assert "market_data" in result
        assert "trust_scores" in result
        assert "inbound_magnets" in result
        assert "content_plan" in result
        assert "viral_strategies" in result
        assert "campaign" in result
        assert "ad_plan" in result

        # 14 nodes (10 shared + 4 B2B, default mode=b2b)
        metrics = result.get("node_metrics", [])
        assert len(metrics) == 14

    @pytest.mark.asyncio
    async def test_no_errors(self):
        blueprint = {
            "blueprint_id": "test",
            "tenant_id": "test",
            "business_model": "b2b",
            "entity_config": {"type": "organization"},
            "trust_config": {},
        }
        result = await run_growth(blueprint)
        assert result.get("errors", []) == []
