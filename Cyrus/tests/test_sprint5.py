"""Tests for Sprint 5: Evolution Layer + final 23-node pipeline."""

import pytest

from nodes.evolution.performance_analyst import PerformanceAnalyst
from nodes.evolution.ab_optimizer import ABOptimizer
from nodes.acquisition.community_seeder import CommunitySeeder
from nodes.acquisition.lead_qualifier import LeadQualifier
from engine.graph import run_growth


@pytest.fixture
def b2b_state():
    return {
        "blueprint": {
            "business_model": "b2b",
            "tenant_id": "test",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {"method": "challenger"},
            "conversion_config": {"mode": "b2b"},
        },
        "trust_scores": {"overall": 50, "stage": "trusted"},
        "trust_engine_output": {"personality_profile": {}, "trust_score": 50, "trust_stage": "trusted"},
        "content_plan": [{"type": "blog"}],
        "outbound_messages": [{"subject": "test"}],
        "ad_plan": {"allocation": [{"platform": "linkedin"}]},
        "inbound_magnets": [{"title": "report"}],
        "campaign": {"name": "Q1"},
        "viral_strategies": [{"name": "v1"}],
        "nurture_sequence": {"sequence": [{"step": 1}]},
        "proposal": {"sections": []},
        "meeting": {"status": "proposed"},
        "close_strategy": {"readiness": "warm"},
        "icp_profiles": [{"icp_name": "CTO"}],
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


class TestPerformanceAnalyst:
    @pytest.mark.asyncio
    async def test_returns_metrics(self, b2b_state):
        node = PerformanceAnalyst()
        result = await node(b2b_state)
        assert "performance_metrics" in result
        metrics = result["performance_metrics"]
        assert "business_model" in metrics
        assert "metrics_framework" in metrics
        assert "health_score" in metrics

    @pytest.mark.asyncio
    async def test_b2b_framework(self, b2b_state):
        node = PerformanceAnalyst()
        result = await node(b2b_state)
        fw = result["performance_metrics"]["metrics_framework"]
        assert "acquisition" in fw
        assert "cac" in fw["acquisition"]

    @pytest.mark.asyncio
    async def test_b2c_framework(self, b2b_state):
        b2b_state["blueprint"]["business_model"] = "b2c"
        node = PerformanceAnalyst()
        result = await node(b2b_state)
        fw = result["performance_metrics"]["metrics_framework"]
        assert "engagement" in fw
        assert "dau_mau" in fw["engagement"]


class TestABOptimizer:
    @pytest.mark.asyncio
    async def test_returns_actions(self, b2b_state):
        node = ABOptimizer()
        result = await node(b2b_state)
        assert "optimization_actions" in result
        assert len(result["optimization_actions"]) > 0
        plan = result["optimization_actions"][0]
        assert "active_tests" in plan
        assert "feedback_loop" in plan

    @pytest.mark.asyncio
    async def test_generates_content_test(self, b2b_state):
        node = ABOptimizer()
        result = await node(b2b_state)
        tests = result["optimization_actions"][0]["active_tests"]
        test_types = [t["type"] for t in tests]
        assert "content" in test_types

    @pytest.mark.asyncio
    async def test_has_auto_thresholds(self, b2b_state):
        node = ABOptimizer()
        result = await node(b2b_state)
        plan = result["optimization_actions"][0]
        assert plan["auto_adopt_threshold"]["confidence"] == 0.95


class TestCommunitySeeder:
    @pytest.mark.asyncio
    async def test_returns_plan(self, b2b_state):
        node = CommunitySeeder()
        result = await node(b2b_state)
        assert "community_seeding" in result
        assert "recruitment_strategy" in result["community_seeding"]


class TestLeadQualifier:
    @pytest.mark.asyncio
    async def test_returns_qualification(self, b2b_state):
        node = LeadQualifier()
        result = await node(b2b_state)
        assert "qualified_leads" in result
        assert result["qualified_leads"][0]["model"] == "b2b"

    @pytest.mark.asyncio
    async def test_c2c_model(self, b2b_state):
        b2b_state["blueprint"]["business_model"] = "c2c"
        node = LeadQualifier()
        result = await node(b2b_state)
        assert result["qualified_leads"][0]["model"] == "c2c"


# --- Full 23-node Pipeline ---

class TestFull23NodeB2B:
    @pytest.mark.asyncio
    async def test_complete_b2b_pipeline(self):
        blueprint = {
            "blueprint_id": "full-b2b",
            "tenant_id": "test",
            "business_model": "b2b",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {"method": "challenger"},
            "conversion_config": {"mode": "b2b"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)

        # All 4 layers present
        assert "market_data" in result            # Intelligence
        assert "trust_scores" in result            # Trust
        assert "content_plan" in result            # Acquisition
        assert "community_seeding" in result       # Acquisition
        assert "qualified_leads" in result         # Acquisition
        assert "close_strategy" in result          # Conversion (B2B)
        assert "performance_metrics" in result     # Evolution
        assert "optimization_actions" in result    # Evolution

        # 16 nodes: Intelligence(3) + Trust(1) + Acquisition(7) + B2B(4) + Evolution(2) - but
        # acquisition has 7 nodes in the sequential chain so total = 3+1+7+4+2 = 17
        # Wait: trust(1), acq sequential = outbound,inbound,content,viral,campaign,ad,community,lead = 8
        # Actually: 3(intel) + 1(trust) + 8(acq: outbound,inbound,content,viral,campaign,ad,community,lead) + 4(b2b) + 2(evolution) = 18
        metrics = result.get("node_metrics", [])
        assert len(metrics) == 18
        assert result.get("errors", []) == []


class TestFull23NodeB2C:
    @pytest.mark.asyncio
    async def test_complete_b2c_pipeline(self):
        blueprint = {
            "blueprint_id": "full-b2c",
            "tenant_id": "test",
            "business_model": "b2c",
            "entity_config": {"type": "individual", "context": "fan"},
            "trust_config": {},
            "conversion_config": {"mode": "b2c"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        assert "activation" in result
        assert "performance_metrics" in result
        # 3+1+8+3+2 = 17
        assert len(result.get("node_metrics", [])) == 17
        assert result.get("errors", []) == []


class TestFull23NodeC2C:
    @pytest.mark.asyncio
    async def test_complete_c2c_pipeline(self):
        blueprint = {
            "blueprint_id": "full-c2c",
            "tenant_id": "test",
            "business_model": "c2c",
            "entity_config": {"type": "creator", "domain": "musician"},
            "trust_config": {},
            "conversion_config": {"mode": "c2c"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        assert "marketplace_strategy" in result
        assert "performance_metrics" in result
        # 3+1+8+3+2 = 17
        assert len(result.get("node_metrics", [])) == 17
        assert result.get("errors", []) == []


class TestEvolutionFeedbackLoop:
    @pytest.mark.asyncio
    async def test_has_feedback_loop(self):
        blueprint = {
            "blueprint_id": "feedback",
            "tenant_id": "test",
            "business_model": "b2b",
            "entity_config": {"type": "organization"},
            "trust_config": {},
            "conversion_config": {"mode": "b2b"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        actions = result.get("optimization_actions", [])
        assert len(actions) > 0
        loop = actions[0].get("feedback_loop", {})
        assert "Trigger Intelligence Layer re-scan" in str(loop.get("actions", []))
