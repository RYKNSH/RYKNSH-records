"""Tests for Sprint 2: Trust Engine + Outbound + Inbound Magnet."""

import pytest

from nodes.conversion.trust_engine import TrustEngine, get_trust_stage, TRUST_STAGES
from nodes.acquisition.outbound_personalizer import OutboundPersonalizer
from nodes.acquisition.inbound_magnet import InboundMagnet
from engine.graph import run_growth


@pytest.fixture
def b2b_state():
    return {
        "blueprint": {
            "business_model": "b2b",
            "tenant_id": "test",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {
                "personalization_depth": "l3_empathy",
                "method": "challenger_spin_consultative_meddic",
            },
        },
        "market_data": {
            "market_trends": [{"trend": "AI automation", "relevance": 0.9}],
        },
        "icp_profiles": [
            {"icp_name": "Growth CTO", "pain_points": ["slow CI", "no QA team"]},
        ],
        "detected_signals": [
            {"type": "hiring", "confidence": 0.85, "source": "linkedin"},
            {"type": "funding", "confidence": 0.95, "source": "crunchbase"},
        ],
        "tenant_id": "test",
        "node_metrics": [],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# Trust Engine Tests
# ---------------------------------------------------------------------------

class TestTrustStages:
    def test_stranger(self):
        stage = get_trust_stage(10)
        assert stage["label"] == "stranger"

    def test_acquaintance(self):
        stage = get_trust_stage(40)
        assert stage["label"] == "acquaintance"

    def test_trusted(self):
        stage = get_trust_stage(65)
        assert stage["label"] == "trusted"

    def test_partner(self):
        stage = get_trust_stage(90)
        assert stage["label"] == "partner"


class TestTrustEngine:
    @pytest.mark.asyncio
    async def test_returns_trust_output(self, b2b_state):
        engine = TrustEngine()
        result = await engine(b2b_state)
        assert "trust_scores" in result
        assert "trust_engine_output" in result
        output = result["trust_engine_output"]
        assert "personality_profile" in output
        assert "value_first_actions" in output
        assert "timing_decision" in output
        assert "trust_score" in output
        assert "trust_stage" in output

    @pytest.mark.asyncio
    async def test_trust_score_calculation(self, b2b_state):
        engine = TrustEngine()
        result = await engine(b2b_state)
        score = result["trust_scores"]["overall"]
        # Base 10 + signal bonuses (0.85 conf → +5, 0.95 conf → +5) = 20
        assert score >= 15

    @pytest.mark.asyncio
    async def test_node_identity(self, b2b_state):
        engine = TrustEngine()
        result = await engine(b2b_state)
        assert result["current_node"] == "trust_engine"
        assert result["current_layer"] == "conversion"


# ---------------------------------------------------------------------------
# Outbound Personalizer Tests
# ---------------------------------------------------------------------------

class TestOutboundPersonalizer:
    @pytest.mark.asyncio
    async def test_generates_message(self, b2b_state):
        # First run trust engine to get trust_engine_output
        engine = TrustEngine()
        trust_result = await engine(b2b_state)
        state = {**b2b_state, **trust_result}

        personalizer = OutboundPersonalizer()
        result = await personalizer(state)
        assert "outbound_messages" in result
        assert len(result["outbound_messages"]) > 0
        msg = result["outbound_messages"][0]
        assert "subject" in msg
        assert "body" in msg
        assert "channel" in msg

    @pytest.mark.asyncio
    async def test_defers_on_bad_timing(self, b2b_state):
        # Simulate trust output with timing = don't reach out
        state = {
            **b2b_state,
            "trust_engine_output": {
                "personality_profile": {},
                "value_first_actions": {},
                "timing_decision": {"should_reach_out": False, "reason": "Too early"},
                "trust_score": 10,
                "trust_stage": "stranger",
            },
        }
        personalizer = OutboundPersonalizer()
        result = await personalizer(state)
        assert result["outbound_status"] == "deferred"
        assert result["outbound_messages"] == []


# ---------------------------------------------------------------------------
# Inbound Magnet Tests
# ---------------------------------------------------------------------------

class TestInboundMagnet:
    @pytest.mark.asyncio
    async def test_generates_magnets(self, b2b_state):
        magnet = InboundMagnet()
        result = await magnet(b2b_state)
        assert "inbound_magnets" in result
        assert len(result["inbound_magnets"]) > 0
        for m in result["inbound_magnets"]:
            assert "strategy" in m
            assert "title" in m
            assert "distribution_channel" in m

    @pytest.mark.asyncio
    async def test_has_always_on_schedule(self, b2b_state):
        magnet = InboundMagnet()
        result = await magnet(b2b_state)
        assert "inbound_schedule" in result
        schedule = result["inbound_schedule"]
        assert "daily" in schedule
        assert "weekly" in schedule


# ---------------------------------------------------------------------------
# Growth Graph Integration Tests
# ---------------------------------------------------------------------------

class TestGrowthGraph:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        blueprint = {
            "blueprint_id": "test-growth",
            "tenant_id": "test-tenant",
            "business_model": "b2b",
            "entity_config": {"type": "organization", "industry": "saas"},
            "trust_config": {
                "personalization_depth": "l2_context",
                "method": "challenger_spin_consultative_meddic",
            },
        }
        result = await run_growth(blueprint)

        # Intelligence outputs
        assert "market_data" in result
        assert "icp_profiles" in result
        assert "detected_signals" in result

        # Trust Engine outputs
        assert "trust_scores" in result

        # Acquisition outputs
        assert "outbound_messages" in result or "outbound_status" in result
        assert "inbound_magnets" in result

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

    @pytest.mark.asyncio
    async def test_node_count(self):
        blueprint = {
            "blueprint_id": "test",
            "tenant_id": "test",
            "business_model": "b2b",
            "entity_config": {"type": "organization"},
            "trust_config": {},
        }
        result = await run_growth(blueprint)
        metrics = result.get("node_metrics", [])
        # 14 nodes (10 shared + 4 B2B pipeline, default mode=b2b)
        assert len(metrics) == 14
