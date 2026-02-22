"""L1 Adversarial Tests — M4 外販基盤.

World-class edge cases for ToolRegistry, UsageBilling, Catalog.
Tests billing precision, catalog robustness, registry edge cases.
"""

import pytest
from datetime import datetime, timezone, timedelta

from agent.tools.registry import ToolSpec, ToolRegistry, tool_registry
from agent.billing import UsageRecord, UsageTracker
from agent.catalog import (
    CATALOG,
    build_blueprint_from_catalog,
    get_catalog_summary,
)


class TestToolRegistryAdversarial:
    """Registry edge cases."""

    def test_duplicate_registration(self):
        """Re-registering should overwrite."""
        reg = ToolRegistry()
        reg.register(ToolSpec(name="dup", description="v1", category="test"))
        reg.register(ToolSpec(name="dup", description="v2", category="test"))
        assert reg.get("dup").description == "v2"

    def test_get_nonexistent(self):
        assert tool_registry.get("definitely_not_a_tool_42") is None

    def test_list_empty_category(self):
        assert tool_registry.list_by_category("nonexistent_category") == []

    def test_filter_all_nonexistent(self):
        assert tool_registry.filter_for_blueprint(["a", "b", "c"]) == []

    def test_filter_mixed(self):
        tools = tool_registry.filter_for_blueprint(["github_diff", "nonexistent", "linter"])
        assert len(tools) == 2

    def test_catalog_sorted(self):
        """Catalog should be sorted by category then name."""
        catalog = tool_registry.catalog()
        categories = [t["category"] for t in catalog]
        assert categories == sorted(categories)

    def test_tool_spec_cost_boundary(self):
        spec = ToolSpec(name="free", description="Free tool", category="test", cost_per_call_usd=0.0)
        assert spec.cost_per_call_usd == 0.0


class TestBillingAdversarial:
    """Billing precision and edge cases."""

    def test_zero_cost_tracking(self):
        tracker = UsageTracker()
        tracker.track(UsageRecord(
            request_id="r1", tenant_id="t1",
            event_type="node_execution", resource_name="sentinel",
            cost_usd=0.0,
        ))
        usage = tracker.get_tenant_usage("t1")
        assert usage["total_cost_usd"] == 0.0

    def test_floating_point_precision(self):
        """Many small costs should not accumulate floating point errors."""
        tracker = UsageTracker()
        for i in range(1000):
            tracker.track(UsageRecord(
                request_id=f"r{i}", tenant_id="t1",
                event_type="llm_invocation", resource_name="gpt-4o",
                tokens_used=100, cost_usd=0.001,
            ))
        usage = tracker.get_tenant_usage("t1")
        assert abs(usage["total_cost_usd"] - 1.0) < 0.01

    def test_invoice_with_zero_usage(self):
        tracker = UsageTracker()
        invoice = tracker.generate_invoice("empty_tenant")
        assert invoice["billable_amount_usd"] == 0.0

    def test_large_token_count(self):
        tracker = UsageTracker()
        tracker.track(UsageRecord(
            request_id="r1", tenant_id="t1",
            event_type="llm_invocation", resource_name="gpt-4o",
            tokens_used=1_000_000, cost_usd=10.0,
        ))
        usage = tracker.get_tenant_usage("t1")
        assert usage["total_tokens"] == 1_000_000

    def test_multiple_event_types(self):
        tracker = UsageTracker()
        tracker.track(UsageRecord(request_id="r1", tenant_id="t1", event_type="node_execution", resource_name="sentinel"))
        tracker.track(UsageRecord(request_id="r1", tenant_id="t1", event_type="tool_call", resource_name="github_diff"))
        tracker.track(UsageRecord(request_id="r1", tenant_id="t1", event_type="llm_invocation", resource_name="gpt-4o", tokens_used=500))
        usage = tracker.get_tenant_usage("t1")
        assert len(usage["breakdown"]) == 3

    def test_track_from_state(self):
        tracker = UsageTracker()
        state = {
            "node_metrics": [
                {"node_name": "sentinel", "execution_time_ms": 0.5},
                {"node_name": "strategist", "execution_time_ms": 2.0},
            ],
            "usage": {"total_tokens": 1000},
            "response_model": "gpt-4o",
        }
        records = tracker.track_from_state(state, "r1", "t1")
        assert len(records) == 3  # 2 nodes + 1 LLM

    def test_since_filter(self):
        tracker = UsageTracker()
        old = UsageRecord(
            request_id="r1", tenant_id="t1",
            event_type="x", resource_name="y",
            timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        new = UsageRecord(
            request_id="r2", tenant_id="t1",
            event_type="x", resource_name="y",
        )
        tracker.track(old)
        tracker.track(new)
        usage = tracker.get_tenant_usage("t1", since=datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert usage["total_requests"] == 1


class TestCatalogAdversarial:
    """Catalog edge cases."""

    def test_all_blueprints_produce_valid_config(self):
        """Every catalog entry should produce a valid RunnableConfig."""
        for key in CATALOG:
            bp = build_blueprint_from_catalog(key, "test")
            config = bp.to_runnable_config()
            assert "configurable" in config
            assert config["configurable"]["default_model"] is not None
            assert 0.0 <= config["configurable"]["temperature"] <= 1.0

    def test_override_with_invalid_field(self):
        """Unknown override fields should be silently ignored."""
        bp = build_blueprint_from_catalog("code_reviewer", "t1", overrides={"nonexistent_field": "value"})
        assert bp.name == "code_reviewer"

    def test_override_model(self):
        bp = build_blueprint_from_catalog("code_reviewer", "t1", overrides={"default_model": "gpt-4o-mini"})
        assert bp.default_model == "gpt-4o-mini"

    def test_catalog_metadata_preserved(self):
        bp = build_blueprint_from_catalog("growth_hacker", "t1")
        assert bp.metadata["catalog_source"] == "growth_hacker"
        assert bp.metadata["provider"] == "cyrus"

    def test_catalog_summary_completeness(self):
        summary = get_catalog_summary()
        for entry in summary:
            assert "key" in entry
            assert "name" in entry
            assert "description" in entry
            assert "provider" in entry
            assert len(entry["description"]) > 10  # Not empty
