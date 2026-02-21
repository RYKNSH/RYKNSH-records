"""Tests for tenant resolution logic."""

from uuid import UUID

import pytest

from agent.tenant import TenantConfig, build_thread_id


class TestTenantConfig:
    """Test TenantConfig data class."""

    def test_default_tenant(self):
        """Default tenant should have RYKNSH records name and zero UUID."""
        tenant = TenantConfig.default()
        assert tenant.name == "RYKNSH records"
        assert tenant.tenant_id == UUID("00000000-0000-0000-0000-000000000000")
        assert tenant.llm_model == "claude-sonnet-4-20250514"
        assert tenant.review_language == "ja"

    def test_from_db_row(self):
        """Should parse a database row into TenantConfig."""
        row = {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Test Corp",
            "config": {
                "llm_model": "claude-opus-4-20250514",
                "max_diff_chars": 80000,
                "review_language": "en",
                "system_prompt_override": "Be strict.",
            },
        }
        tenant = TenantConfig.from_db_row(row)
        assert tenant.name == "Test Corp"
        assert tenant.llm_model == "claude-opus-4-20250514"
        assert tenant.max_diff_chars == 80000
        assert tenant.system_prompt_override == "Be strict."

    def test_from_db_row_missing_config(self):
        """Should handle missing/null config gracefully."""
        row = {"id": "22222222-2222-2222-2222-222222222222", "name": "Minimal", "config": None}
        tenant = TenantConfig.from_db_row(row)
        assert tenant.name == "Minimal"
        assert tenant.llm_model == "claude-sonnet-4-20250514"  # default
        assert tenant.system_prompt_override is None


class TestBuildThreadId:
    """Test thread_id generation."""

    def test_format(self):
        """Thread ID should follow tenant:repo:pr-N format."""
        tid = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        result = build_thread_id(tid, "RYKNSH/RYKNSH-records", 42)
        assert result == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee:RYKNSH/RYKNSH-records:pr-42"

    def test_different_prs_different_threads(self):
        """Different PRs should produce different thread IDs."""
        tid = UUID("00000000-0000-0000-0000-000000000000")
        t1 = build_thread_id(tid, "org/repo", 1)
        t2 = build_thread_id(tid, "org/repo", 2)
        assert t1 != t2

    def test_different_tenants_different_threads(self):
        """Same PR in different tenants should produce different thread IDs."""
        t1 = build_thread_id(UUID("11111111-1111-1111-1111-111111111111"), "org/repo", 1)
        t2 = build_thread_id(UUID("22222222-2222-2222-2222-222222222222"), "org/repo", 1)
        assert t1 != t2


class TestResolveTenant:
    """Test tenant resolution with mocked DB."""

    @pytest.mark.asyncio
    async def test_none_installation_returns_default(self):
        """No installation_id should return default tenant."""
        from agent.tenant import resolve_tenant
        tenant = await resolve_tenant(None)
        assert tenant.name == "RYKNSH records"

    @pytest.mark.asyncio
    async def test_no_supabase_url_returns_default(self):
        """Missing SUPABASE_DB_URL should return default tenant."""
        from agent.tenant import resolve_tenant
        tenant = await resolve_tenant(12345)
        assert tenant.name == "RYKNSH records"
