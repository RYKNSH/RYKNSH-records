"""Tests for MS5 — 外販プラットフォーム.

Covers:
- API Keys (generation, hashing, CRUD)
- Stripe Billing (plans, quotas, checkout)
- Onboarding (signup flow)
- Dashboard API (usage, keys, billing)
- SDK client
"""

import pytest

from server.api_keys import generate_api_key, hash_api_key, APIKeyStore
from server.stripe_billing import StripeBilling, PLANS
from server.onboarding import signup, SignupRequest
from server.dashboard import get_usage, list_keys, create_key, KeyCreateRequest, get_billing, get_catalog_api


class TestAPIKeys:
    """Test API key management."""

    def test_generate_live_key(self):
        key, h = generate_api_key("live")
        assert key.startswith("ada_live_")
        assert len(key) == 73  # "ada_live_" (9) + 64 hex chars

    def test_generate_test_key(self):
        key, h = generate_api_key("test")
        assert key.startswith("ada_test_")

    def test_hash_consistency(self):
        key, h = generate_api_key()
        assert hash_api_key(key) == h

    def test_uniqueness(self):
        keys = [generate_api_key()[0] for _ in range(100)]
        assert len(set(keys)) == 100

    @pytest.mark.asyncio
    async def test_create_and_validate(self):
        store = APIKeyStore()
        plain, record = await store.create("t1", "my-key")
        validated = await store.validate(plain)
        assert validated is not None
        assert validated.tenant_id == "t1"
        assert validated.name == "my-key"

    @pytest.mark.asyncio
    async def test_validate_invalid(self):
        store = APIKeyStore()
        result = await store.validate("ada_live_invalid_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke(self):
        store = APIKeyStore()
        plain, record = await store.create("t1")
        assert await store.revoke(record.id, "t1") is True
        # Should no longer validate
        result = await store.validate(plain)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_tenant(self):
        store = APIKeyStore()
        await store.create("t1", "key1")
        await store.create("t1", "key2")
        await store.create("t2", "key3")
        t1_keys = await store.list_by_tenant("t1")
        assert len(t1_keys) == 2


class TestStripeBilling:
    """Test Stripe billing."""

    def test_plans_defined(self):
        assert len(PLANS) == 3
        assert "free" in PLANS
        assert "pro" in PLANS
        assert "enterprise" in PLANS

    def test_default_free_plan(self):
        billing = StripeBilling()
        sub = billing.get_or_create_subscription("t1")
        assert sub.plan == "free"
        assert sub.request_limit == 100

    def test_check_quota(self):
        billing = StripeBilling()
        quota = billing.check_quota("t1")
        assert quota["has_quota"] is True
        assert quota["remaining"] == 100

    @pytest.mark.asyncio
    async def test_increment_usage(self):
        billing = StripeBilling()
        await billing.increment_usage("t1")
        quota = billing.check_quota("t1")
        assert quota["request_count"] == 1
        assert quota["remaining"] == 99

    @pytest.mark.asyncio
    async def test_free_quota_exhaustion(self):
        billing = StripeBilling()
        for _ in range(100):
            await billing.increment_usage("t1")
        quota = billing.check_quota("t1")
        assert quota["remaining"] == 0
        assert quota["has_quota"] is False  # Free plan, no overage

    @pytest.mark.asyncio
    async def test_pro_quota_allows_overage(self):
        billing = StripeBilling()
        billing.upgrade_plan("t1", "pro")
        for _ in range(10001):
            await billing.increment_usage("t1")
        quota = billing.check_quota("t1")
        assert quota["has_quota"] is True  # Pro allows overage

    def test_upgrade_plan(self):
        billing = StripeBilling()
        sub = billing.upgrade_plan("t1", "enterprise")
        assert sub.plan == "enterprise"
        assert sub.request_limit == 100_000

    def test_unknown_plan_raises(self):
        billing = StripeBilling()
        with pytest.raises(ValueError):
            billing.upgrade_plan("t1", "ultra_premium")

    @pytest.mark.asyncio
    async def test_billing_info(self):
        billing = StripeBilling()
        billing.upgrade_plan("t1", "pro")
        for _ in range(50):
            await billing.increment_usage("t1")
        info = billing.get_billing_info("t1")
        assert info["plan"] == "pro"
        assert info["monthly_cost_usd"] == 49
        assert info["request_count"] == 50
        assert info["overage_count"] == 0

    @pytest.mark.asyncio
    async def test_overage_billing(self):
        billing = StripeBilling()
        billing.upgrade_plan("t1", "pro")
        for _ in range(10_100):
            await billing.increment_usage("t1")
        info = billing.get_billing_info("t1")
        assert info["overage_count"] == 100
        assert info["overage_cost_usd"] == 0.5  # 100 * 0.005


class TestOnboarding:
    """Test tenant onboarding."""

    @pytest.mark.asyncio
    async def test_signup(self):
        resp = await signup(SignupRequest(email="test@example.com"))
        assert resp.tenant_id != ""
        assert resp.api_key.startswith("ada_live_")
        assert resp.plan == "free"

    @pytest.mark.asyncio
    async def test_signup_with_plan(self):
        resp = await signup(SignupRequest(email="pro@example.com", plan="pro"))
        assert resp.plan == "pro"


class TestDashboard:
    """Test dashboard API."""

    @pytest.mark.asyncio
    async def test_get_usage(self):
        usage = await get_usage("dash-t1")
        assert usage.plan == "free"
        assert usage.remaining == 100

    @pytest.mark.asyncio
    async def test_create_and_list_keys(self):
        key_resp = await create_key("dash-t1", KeyCreateRequest(name="test-key"))
        assert key_resp.api_key.startswith("ada_live_")
        keys = await list_keys("dash-t1")
        assert len(keys) >= 1

    @pytest.mark.asyncio
    async def test_get_billing(self):
        billing = await get_billing("dash-t1")
        assert "plan" in billing
        assert "total_cost_usd" in billing

    @pytest.mark.asyncio
    async def test_catalog_api(self):
        catalog = await get_catalog_api()
        assert len(catalog) == 3
        providers = {c["provider"] for c in catalog}
        assert providers == {"velie", "cyrus", "lumina"}
