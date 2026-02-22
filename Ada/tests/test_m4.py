"""Tests for M4 — Tool Registry, Billing, Catalog.

Covers:
- Tool Registry (registration, filtering, catalog)
- Usage Billing (tracking, aggregation, invoicing)
- Node Set Catalog (blueprint generation, SDK summary)
"""

import pytest
from datetime import datetime, timezone

from agent.tools.registry import ToolSpec, ToolRegistry, tool_registry
from agent.billing import UsageRecord, UsageTracker
from agent.catalog import (
    CATALOG,
    build_blueprint_from_catalog,
    get_catalog_summary,
)


class TestToolRegistry:
    """Test ToolRegistry."""

    def test_default_tools_registered(self):
        assert len(tool_registry.list_all()) >= 10

    def test_get_by_name(self):
        tool = tool_registry.get("github_diff")
        assert tool is not None
        assert tool.provider == "velie"
        assert tool.category == "code_review"

    def test_list_by_category(self):
        code_tools = tool_registry.list_by_category("code_review")
        assert len(code_tools) >= 3

    def test_list_by_provider(self):
        velie_tools = tool_registry.list_by_provider("velie")
        assert len(velie_tools) >= 3
        assert all(t.provider == "velie" for t in velie_tools)

    def test_filter_for_blueprint(self):
        tools = tool_registry.filter_for_blueprint(["github_diff", "linter", "nonexistent"])
        assert len(tools) == 2

    def test_catalog_export(self):
        catalog = tool_registry.catalog()
        assert len(catalog) >= 10
        assert all("name" in t for t in catalog)

    def test_register_custom_tool(self):
        registry = ToolRegistry()
        registry.register(ToolSpec(name="custom", description="Custom tool", category="test"))
        assert registry.get("custom") is not None


class TestUsageBilling:
    """Test UsageTracker."""

    @pytest.fixture
    def tracker(self):
        return UsageTracker()

    def test_track_record(self, tracker):
        tracker.track(UsageRecord(
            request_id="r1", tenant_id="t1",
            event_type="node_execution", resource_name="sentinel",
            execution_time_ms=0.5,
        ))
        usage = tracker.get_tenant_usage("t1")
        assert usage["total_requests"] == 1

    def test_multiple_records_same_request(self, tracker):
        for node in ["sentinel", "strategist", "validator"]:
            tracker.track(UsageRecord(
                request_id="r1", tenant_id="t1",
                event_type="node_execution", resource_name=node,
                execution_time_ms=1.0,
            ))
        usage = tracker.get_tenant_usage("t1")
        assert usage["total_requests"] == 1  # Same request_id
        assert len(usage["breakdown"]) == 3

    def test_llm_usage_tracking(self, tracker):
        tracker.track(UsageRecord(
            request_id="r1", tenant_id="t1",
            event_type="llm_invocation", resource_name="gpt-4o",
            tokens_used=1000, cost_usd=0.01,
        ))
        usage = tracker.get_tenant_usage("t1")
        assert usage["total_tokens"] == 1000
        assert usage["total_cost_usd"] == 0.01

    def test_invoice_generation(self, tracker):
        tracker.track(UsageRecord(
            request_id="r1", tenant_id="t1",
            event_type="llm_invocation", resource_name="gpt-4o",
            tokens_used=1000, cost_usd=0.10,
        ))
        invoice = tracker.generate_invoice("t1")
        assert invoice["total_cost_usd"] == 0.10
        assert invoice["billable_amount_usd"] == 0.13  # 30% markup
        assert invoice["markup_rate"] == 1.3

    def test_tenant_isolation(self, tracker):
        tracker.track(UsageRecord(request_id="r1", tenant_id="t1", event_type="x", resource_name="y"))
        tracker.track(UsageRecord(request_id="r2", tenant_id="t2", event_type="x", resource_name="y"))
        assert tracker.get_tenant_usage("t1")["total_requests"] == 1
        assert tracker.get_tenant_usage("t2")["total_requests"] == 1

    def test_empty_tenant_usage(self, tracker):
        usage = tracker.get_tenant_usage("nonexistent")
        assert usage["total_requests"] == 0


class TestCatalog:
    """Test Node Set Catalog."""

    def test_catalog_has_entries(self):
        assert len(CATALOG) == 3

    def test_code_reviewer_entry(self):
        entry = CATALOG["code_reviewer"]
        assert entry["provider"] == "velie"
        assert "github_diff" in entry["blueprint_template"]["tools"]

    def test_build_blueprint_from_catalog(self):
        bp = build_blueprint_from_catalog("code_reviewer", "test-tenant")
        assert bp.tenant_id == "test-tenant"
        assert bp.name == "code_reviewer"
        assert bp.temperature == 0.2
        assert "github_diff" in bp.tools
        assert bp.priority_weights.quality == 0.5

    def test_build_with_overrides(self):
        bp = build_blueprint_from_catalog(
            "code_reviewer", "t1",
            overrides={"temperature": 0.3, "quality_tier": "light"},
        )
        assert bp.temperature == 0.3
        assert bp.quality_tier == "light"

    def test_unknown_catalog_raises(self):
        with pytest.raises(ValueError):
            build_blueprint_from_catalog("nonexistent", "t1")

    def test_catalog_summary(self):
        summary = get_catalog_summary()
        assert len(summary) == 3
        providers = {s["provider"] for s in summary}
        assert providers == {"velie", "cyrus", "lumina"}

    def test_growth_hacker_blueprint(self):
        bp = build_blueprint_from_catalog("growth_hacker", "t1")
        assert bp.default_model == "gpt-4o"
        assert "analytics_query" in bp.tools

    def test_creative_director_blueprint(self):
        bp = build_blueprint_from_catalog("creative_director", "t1")
        assert bp.temperature == 0.8
        assert bp.rag_enabled is False

    def test_blueprint_to_config_bridge(self):
        """Catalog blueprint should produce valid RunnableConfig."""
        bp = build_blueprint_from_catalog("code_reviewer", "t1")
        config = bp.to_runnable_config()
        assert config["configurable"]["default_model"] == "claude-sonnet-4-20250514"
        assert config["configurable"]["quality_tier"] == "full"
        assert config["configurable"]["priority_weights"]["quality"] == 0.5
