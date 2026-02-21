"""Tests for server.app — FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture
def client():
    """Create a test client with lifespan disabled."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealthCheck:
    """Test /health endpoint."""

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "ada-core-api"
        assert data["version"] == "0.1.0"


class TestModelsEndpoint:
    """Test /v1/models endpoint."""

    def test_models_no_auth(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 401

    def test_models_with_auth(self, client):
        resp = client.get(
            "/v1/models",
            headers={"Authorization": "Bearer ada-test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) > 0
        for model in data["data"]:
            assert "id" in model
            assert model["object"] == "model"


class TestChatCompletions:
    """Test /v1/chat/completions endpoint."""

    def test_no_auth(self, client):
        resp = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert resp.status_code == 401

    def test_streaming_not_supported(self, client):
        resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "stream": True,
            },
        )
        assert resp.status_code == 400
        assert "Stream" in resp.json()["detail"] or "stream" in resp.json()["detail"].lower()

    def test_disallowed_model(self, client):
        resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "model": "nonexistent-model",
            },
        )
        assert resp.status_code == 400


class TestRouteEndpoint:
    """Test /v1/route endpoint."""

    def test_route_no_auth(self, client):
        resp = client.post("/v1/route", json={
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert resp.status_code == 401

    def test_route_short_message(self, client):
        resp = client.post(
            "/v1/route",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommended_model" in data
        assert "reason" in data
        # Short message should recommend gpt-4o-mini
        assert data["recommended_model"] == "gpt-4o-mini"

    def test_route_code_message(self, client):
        resp = client.post(
            "/v1/route",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "```python\ndef hello():\n    pass\n```"}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommended_model"] == "claude-sonnet-4-20250514"

    def test_route_explicit_model(self, client):
        resp = client.post(
            "/v1/route",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "model": "gpt-4o",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommended_model"] == "gpt-4o"
