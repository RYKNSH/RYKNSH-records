"""Tests for AgentBlueprint and BlueprintStore.

Covers:
- Blueprint schema (creation, serialization, defaults)
- PriorityWeights
- to_runnable_config bridge
- Supabase serialization roundtrip
- BlueprintStore (save, get, version, list, delete)
"""

import pytest

from agent.lifecycle.blueprint import AgentBlueprint, PriorityWeights
from agent.lifecycle.blueprint_store import BlueprintStore


class TestPriorityWeights:
    """Test PriorityWeights model."""

    def test_defaults(self):
        w = PriorityWeights()
        assert w.quality == 0.4
        assert w.efficiency == 0.3
        assert w.speed == 0.2
        assert w.cost == 0.1

    def test_to_dict(self):
        w = PriorityWeights(quality=0.5, efficiency=0.3, speed=0.15, cost=0.05)
        d = w.to_dict()
        assert d["quality"] == 0.5
        assert sum(d.values()) == pytest.approx(1.0)


class TestAgentBlueprint:
    """Test AgentBlueprint schema."""

    def test_default_creation(self):
        bp = AgentBlueprint.default(tenant_id="test-tenant")
        assert bp.tenant_id == "test-tenant"
        assert bp.version == 1
        assert bp.default_model == "claude-sonnet-4-20250514"
        assert bp.quality_tier == "standard"

    def test_to_runnable_config(self):
        bp = AgentBlueprint.default()
        config = bp.to_runnable_config()
        assert "configurable" in config
        assert config["configurable"]["default_model"] == "claude-sonnet-4-20250514"
        assert "priority_weights" in config["configurable"]

    def test_supabase_roundtrip(self):
        bp = AgentBlueprint.default(tenant_id="roundtrip")
        bp.persona = "Expert coder"
        bp.system_prompt = "You are an expert."
        bp.tools = ["web_search", "code_executor"]

        row = bp.to_supabase_row()
        restored = AgentBlueprint.from_supabase_row(row)

        assert restored.tenant_id == "roundtrip"
        assert restored.persona == "Expert coder"
        assert restored.tools == ["web_search", "code_executor"]
        assert restored.priority_weights.quality == 0.4

    def test_custom_weights(self):
        bp = AgentBlueprint(
            priority_weights=PriorityWeights(quality=0.6, efficiency=0.2, speed=0.1, cost=0.1),
        )
        config = bp.to_runnable_config()
        assert config["configurable"]["priority_weights"]["quality"] == 0.6


class TestBlueprintStore:
    """Test BlueprintStore (in-memory mode)."""

    @pytest.fixture
    def store(self):
        return BlueprintStore()

    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        bp = AgentBlueprint.default(tenant_id="t1")
        saved = await store.save(bp)
        assert saved.version == 1

        loaded = await store.get_latest("t1", "default")
        assert loaded is not None
        assert loaded.tenant_id == "t1"

    @pytest.mark.asyncio
    async def test_auto_versioning(self, store):
        bp1 = AgentBlueprint.default(tenant_id="t1")
        await store.save(bp1)

        bp2 = AgentBlueprint.default(tenant_id="t1")
        saved = await store.save(bp2)
        assert saved.version == 2

    @pytest.mark.asyncio
    async def test_get_latest_empty(self, store):
        result = await store.get_latest("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_blueprints(self, store):
        await store.save(AgentBlueprint.default(tenant_id="t1"))
        bp2 = AgentBlueprint.default(tenant_id="t1")
        bp2.name = "custom"
        await store.save(bp2)

        results = await store.list_blueprints("t1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_delete(self, store):
        await store.save(AgentBlueprint.default(tenant_id="t1"))
        deleted = await store.delete("t1", "default")
        assert deleted is True
        assert await store.get_latest("t1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        assert await store.delete("none", "none") is False
