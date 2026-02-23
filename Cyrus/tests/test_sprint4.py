"""Tests for Sprint 4: Conversion Layer — B2B + B2C + C2C Pipelines."""

import pytest

from nodes.conversion.nurture_sequencer import NurtureSequencer
from nodes.conversion.proposal_generator import ProposalGenerator
from nodes.conversion.meeting_setter import MeetingSetter
from nodes.conversion.close_advisor import CloseAdvisor
from nodes.conversion.activation_optimizer import ActivationOptimizer
from nodes.conversion.retention_looper import RetentionLooper
from nodes.conversion.monetization_trigger import MonetizationTrigger
from nodes.conversion.onboarding_sequencer import OnboardingSequencer
from nodes.conversion.trust_builder import TrustBuilder
from nodes.conversion.marketplace_growth_driver import MarketplaceGrowthDriver
from engine.graph import run_growth


@pytest.fixture
def b2b_state():
    return {
        "blueprint": {
            "business_model": "b2b",
            "tenant_id": "test",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {"method": "challenger"},
            "conversion_config": {"mode": "b2b", "pipeline": ["nurture", "proposal", "meeting", "close"]},
            "pricing_model": "full_outcome",
            "outcome_config": {"rate": 0.25},
        },
        "trust_engine_output": {
            "personality_profile": {"communication_style": "analytical", "hot_buttons": ["ROI"], "preferred_channel": "email", "preferred_content_format": "data_heavy", "avoid_topics": []},
            "timing_decision": {"optimal_day": "tuesday", "optimal_time": "morning"},
            "value_first_actions": {"actions": [{"title": "Report"}]},
            "trust_score": 50,
            "trust_stage": "trusted",
        },
        "market_data": {"competitive_landscape": {"competitors": 5}},
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


@pytest.fixture
def b2c_state():
    return {
        "blueprint": {
            "business_model": "b2c",
            "tenant_id": "test",
            "entity_config": {"type": "individual", "context": "subscriber", "industry": "entertainment"},
            "conversion_config": {"mode": "b2c"},
            "pricing_model": "usage",
        },
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


@pytest.fixture
def c2c_state():
    return {
        "blueprint": {
            "business_model": "c2c",
            "tenant_id": "test",
            "entity_config": {"type": "creator", "domain": "musician"},
            "conversion_config": {"mode": "c2c"},
        },
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


# --- B2B Pipeline ---

class TestNurtureSequencer:
    @pytest.mark.asyncio
    async def test_returns_sequence(self, b2b_state):
        node = NurtureSequencer()
        result = await node(b2b_state)
        assert "nurture_sequence" in result
        seq = result["nurture_sequence"]
        assert "sequence" in seq
        assert len(seq["sequence"]) > 0


class TestProposalGenerator:
    @pytest.mark.asyncio
    async def test_returns_proposal(self, b2b_state):
        node = ProposalGenerator()
        result = await node(b2b_state)
        assert "proposal" in result
        assert "sections" in result["proposal"]
        assert result["proposal"]["lumina_handoff"] is True


class TestMeetingSetter:
    @pytest.mark.asyncio
    async def test_returns_meeting(self, b2b_state):
        node = MeetingSetter()
        result = await node(b2b_state)
        assert "meeting" in result
        assert result["meeting"]["preferred_day"] == "tuesday"
        assert "agenda" in result["meeting"]


class TestCloseAdvisor:
    @pytest.mark.asyncio
    async def test_returns_strategy(self, b2b_state):
        node = CloseAdvisor()
        result = await node(b2b_state)
        assert "close_strategy" in result
        cs = result["close_strategy"]
        assert cs["readiness"] == "warm"  # trust_score=50 → warm
        assert "recommended_tactics" in cs

    @pytest.mark.asyncio
    async def test_ready_at_high_trust(self, b2b_state):
        b2b_state["trust_engine_output"]["trust_score"] = 80
        node = CloseAdvisor()
        result = await node(b2b_state)
        assert result["close_strategy"]["readiness"] == "ready"


# --- B2C Pipeline ---

class TestActivationOptimizer:
    @pytest.mark.asyncio
    async def test_returns_activation(self, b2c_state):
        node = ActivationOptimizer()
        result = await node(b2c_state)
        assert "activation" in result
        assert "onboarding_flow" in result["activation"]
        assert result["activation"]["aha_moment"] is not None


class TestRetentionLooper:
    @pytest.mark.asyncio
    async def test_returns_retention_plan(self, b2c_state):
        node = RetentionLooper()
        result = await node(b2c_state)
        assert "retention_plan" in result
        assert "cohort_tracking" in result["retention_plan"]
        assert "d1" in result["retention_plan"]["cohort_tracking"]


class TestMonetizationTrigger:
    @pytest.mark.asyncio
    async def test_returns_monetization(self, b2c_state):
        node = MonetizationTrigger()
        result = await node(b2c_state)
        assert "monetization" in result
        assert "triggers" in result["monetization"]
        assert len(result["monetization"]["triggers"]) >= 3


# --- C2C Pipeline ---

class TestOnboardingSequencer:
    @pytest.mark.asyncio
    async def test_returns_dual_onboarding(self, c2c_state):
        node = OnboardingSequencer()
        result = await node(c2c_state)
        assert "onboarding" in result
        assert "supply_side" in result["onboarding"]
        assert "demand_side" in result["onboarding"]


class TestTrustBuilderNode:
    @pytest.mark.asyncio
    async def test_returns_trust_building(self, c2c_state):
        node = TrustBuilder()
        result = await node(c2c_state)
        assert "trust_building" in result
        assert "verification_layers" in result["trust_building"]
        assert "dispute_resolution" in result["trust_building"]


class TestMarketplaceGrowthDriver:
    @pytest.mark.asyncio
    async def test_returns_strategy(self, c2c_state):
        node = MarketplaceGrowthDriver()
        result = await node(c2c_state)
        assert "marketplace_strategy" in result
        assert "chicken_egg_strategy" in result["marketplace_strategy"]


# --- Full Pipeline Integration ---

class TestFullPipelineB2B:
    @pytest.mark.asyncio
    async def test_b2b_pipeline(self):
        blueprint = {
            "blueprint_id": "test-b2b",
            "tenant_id": "test",
            "business_model": "b2b",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {"method": "challenger"},
            "conversion_config": {"mode": "b2b"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        # B2B pipeline outputs
        assert "nurture_sequence" in result
        assert "proposal" in result
        assert "meeting" in result
        assert "close_strategy" in result
        # 14 nodes (10 shared + 4 B2B)
        assert len(result.get("node_metrics", [])) == 14
        assert result.get("errors", []) == []


class TestFullPipelineB2C:
    @pytest.mark.asyncio
    async def test_b2c_pipeline(self):
        blueprint = {
            "blueprint_id": "test-b2c",
            "tenant_id": "test",
            "business_model": "b2c",
            "entity_config": {"type": "individual", "context": "fan"},
            "trust_config": {},
            "conversion_config": {"mode": "b2c"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        # B2C pipeline outputs
        assert "activation" in result
        assert "retention_plan" in result
        assert "monetization" in result
        # 13 nodes (10 shared + 3 B2C)
        assert len(result.get("node_metrics", [])) == 13
        assert result.get("errors", []) == []


class TestFullPipelineC2C:
    @pytest.mark.asyncio
    async def test_c2c_pipeline(self):
        blueprint = {
            "blueprint_id": "test-c2c",
            "tenant_id": "test",
            "business_model": "c2c",
            "entity_config": {"type": "creator", "domain": "musician"},
            "trust_config": {},
            "conversion_config": {"mode": "c2c"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        # C2C pipeline outputs
        assert "onboarding" in result
        assert "trust_building" in result
        assert "marketplace_strategy" in result
        # 13 nodes (10 shared + 3 C2C)
        assert len(result.get("node_metrics", [])) == 13
        assert result.get("errors", []) == []


class TestB2CHighDealComplexity:
    @pytest.mark.asyncio
    async def test_routes_to_b2b(self):
        """B2C with high deal_complexity should use B2B pipeline."""
        blueprint = {
            "blueprint_id": "test-b2c-high",
            "tenant_id": "test",
            "business_model": "b2c",
            "deal_complexity": "high",
            "entity_config": {"type": "individual"},
            "trust_config": {},
            "conversion_config": {"mode": "b2c"},
            "acquisition_config": {"channels": {}},
        }
        result = await run_growth(blueprint)
        # Should route to B2B pipeline
        assert "nurture_sequence" in result
        assert "close_strategy" in result
        assert len(result.get("node_metrics", [])) == 14
