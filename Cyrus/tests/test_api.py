"""Tests for Sprint 6: PLG Launch — API + Tenant + Auth."""

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.tenant import create_tenant, _TENANTS, _API_KEYS


@pytest.fixture(autouse=True)
def reset_tenants():
    """Reset in-memory tenant store between tests."""
    _TENANTS.clear()
    _API_KEYS.clear()
    yield
    _TENANTS.clear()
    _API_KEYS.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create a tenant and return auth headers."""
    _, api_key = create_tenant("test-tenant", "Test Corp", "usage")
    return {"X-API-Key": api_key}


@pytest.fixture
def free_headers():
    """Create a free-tier tenant."""
    _, api_key = create_tenant("free-tenant", "Free User", "free")
    return {"X-API-Key": api_key}


# --- Health ---

class TestHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["nodes"] == "23"


# --- Tenant API ---

class TestTenantAPI:
    def test_create_tenant(self, client):
        resp = client.post("/api/tenants/", json={
            "tenant_id": "new-tenant",
            "name": "New Corp",
            "plan": "growth",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == "new-tenant"
        assert data["api_key"].startswith("cyrus_")
        assert data["plan"] == "growth"

    def test_duplicate_tenant(self, client):
        create_tenant("dup", "Dup Corp")
        resp = client.post("/api/tenants/", json={"tenant_id": "dup", "name": "Dup"})
        assert resp.status_code == 409

    def test_get_tenant(self, client):
        create_tenant("info-test", "Info Corp", "full_outcome")
        resp = client.get("/api/tenants/info-test")
        assert resp.status_code == 200
        assert resp.json()["plan"] == "full_outcome"

    def test_get_nonexistent(self, client):
        resp = client.get("/api/tenants/nope")
        assert resp.status_code == 404

    def test_get_plans(self, client):
        resp = client.get("/api/tenants/plans/available")
        assert resp.status_code == 200
        plans = resp.json()["plans"]
        assert "free" in plans
        assert "full_outcome" in plans


# --- Auth ---

class TestAuth:
    def test_no_key(self, client):
        resp = client.post("/api/growth/run", json={"blueprint": {}})
        assert resp.status_code == 401

    def test_invalid_key(self, client):
        resp = client.post("/api/growth/run", json={"blueprint": {}}, headers={"X-API-Key": "bad"})
        assert resp.status_code == 401


# --- Growth API ---

class TestGrowthAPI:
    def test_full_pipeline_b2b(self, client, auth_headers):
        resp = client.post("/api/growth/run", json={
            "blueprint": {
                "business_model": "b2b",
                "entity_config": {"type": "organization", "industry": "saas"},
                "trust_config": {"method": "challenger"},
                "conversion_config": {"mode": "b2b"},
                "acquisition_config": {"channels": {}},
            },
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["pipeline_used"] == "b2b"
        assert "market_data" in data
        assert "close_strategy" in data
        assert "performance_metrics" in data
        assert len(data["node_metrics"]) == 18

    def test_full_pipeline_b2c(self, client, auth_headers):
        resp = client.post("/api/growth/run", json={
            "blueprint": {
                "business_model": "b2c",
                "entity_config": {"type": "individual"},
                "trust_config": {},
                "conversion_config": {"mode": "b2c"},
                "acquisition_config": {"channels": {}},
            },
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["pipeline_used"] == "b2c"
        assert len(data["node_metrics"]) == 17

    def test_intelligence_scan(self, client, auth_headers):
        resp = client.post("/api/growth/scan", json={
            "blueprint": {
                "business_model": "b2b",
                "entity_config": {"type": "organization"},
            },
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert "market_data" in resp.json()

    def test_free_plan_blocks_growth(self, client, free_headers):
        resp = client.post("/api/growth/run", json={
            "blueprint": {"business_model": "b2b"},
        }, headers=free_headers)
        assert resp.status_code == 403

    def test_free_plan_allows_scan(self, client, free_headers):
        resp = client.post("/api/growth/scan", json={
            "blueprint": {"business_model": "b2b"},
        }, headers=free_headers)
        assert resp.status_code == 200
