"""Tests for agent.tenant — API key-based tenant resolution."""

from uuid import UUID

import pytest

from agent.tenant import TenantConfig, build_thread_id


class TestTenantConfig:
    """Test TenantConfig dataclass."""

    def test_default_tenant(self):
        tenant = TenantConfig.default()
        assert tenant.name == "RYKNSH records"
        assert tenant.tenant_id == UUID("00000000-0000-0000-0000-000000000000")
        assert tenant.default_model == "claude-sonnet-4-20250514"
        assert len(tenant.allowed_models) == 3

    def test_from_db_row(self):
        row = {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Test Corp",
            "config": {
                "default_model": "gpt-4o",
                "allowed_models": ["gpt-4o", "gpt-4o-mini"],
                "rate_limit_rpm": 120,
                "monthly_budget_usd": 1000.0,
            },
        }
        tenant = TenantConfig.from_db_row(row)
        assert tenant.name == "Test Corp"
        assert tenant.default_model == "gpt-4o"
        assert tenant.allowed_models == ("gpt-4o", "gpt-4o-mini")
        assert tenant.rate_limit_rpm == 120
        assert tenant.monthly_budget_usd == 1000.0

    def test_from_db_row_minimal(self):
        row = {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Minimal Corp",
            "config": {},
        }
        tenant = TenantConfig.from_db_row(row)
        assert tenant.name == "Minimal Corp"
        assert tenant.default_model == "claude-sonnet-4-20250514"
        assert len(tenant.allowed_models) == 3

    def test_from_db_row_no_config(self):
        row = {
            "id": "33333333-3333-3333-3333-333333333333",
            "name": "No Config Corp",
            "config": None,
        }
        tenant = TenantConfig.from_db_row(row)
        assert tenant.name == "No Config Corp"

    def test_frozen(self):
        tenant = TenantConfig.default()
        with pytest.raises(AttributeError):
            tenant.name = "Modified"


class TestBuildThreadId:
    """Test thread ID generation."""

    def test_format(self):
        tid = UUID("11111111-1111-1111-1111-111111111111")
        thread_id = build_thread_id(tid, "req-123")
        assert thread_id == "11111111-1111-1111-1111-111111111111:req-123"

    def test_deterministic(self):
        tid = UUID("00000000-0000-0000-0000-000000000000")
        assert build_thread_id(tid, "a") == build_thread_id(tid, "a")

    def test_unique_per_request(self):
        tid = UUID("00000000-0000-0000-0000-000000000000")
        assert build_thread_id(tid, "a") != build_thread_id(tid, "b")
