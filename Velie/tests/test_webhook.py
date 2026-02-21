"""Tests for the FastAPI webhook endpoint."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WEBHOOK_SECRET = "test-secret-123"
GITHUB_TOKEN = "ghp_test_token"
ANTHROPIC_KEY = "sk-ant-test-key"


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required environment variables for all tests."""
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("GITHUB_TOKEN", GITHUB_TOKEN)
    monkeypatch.setenv("ANTHROPIC_API_KEY", ANTHROPIC_KEY)


@pytest.fixture()
def client():
    """Create a fresh TestClient for each test."""
    # Import here so env vars are set first
    from server.app import app
    return TestClient(app)


def _sign(payload: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Generate HMAC-SHA256 signature."""
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _pr_payload(action: str = "opened", pr_number: int = 42) -> dict:
    """Create a minimal pull_request webhook payload."""
    return {
        "action": action,
        "pull_request": {
            "number": pr_number,
            "title": "Test PR",
            "body": "This is a test pull request.",
            "user": {"login": "test-user"},
        },
        "repository": {
            "full_name": "RYKNSH/test-repo",
        },
        "installation": {"id": 12345},
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "velie-qa-agent"


class TestWebhookSignature:
    def test_missing_signature_returns_401(self, client):
        resp = client.post(
            "/webhook/github",
            content=b"{}",
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert resp.status_code == 401

    def test_invalid_signature_returns_401(self, client):
        payload = json.dumps(_pr_payload()).encode()
        resp = client.post(
            "/webhook/github",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=invalid",
            },
        )
        assert resp.status_code == 401


class TestWebhookEventFiltering:
    def test_non_pr_event_is_ignored(self, client):
        payload = json.dumps({"action": "completed"}).encode()
        resp = client.post(
            "/webhook/github",
            content=payload,
            headers={
                "X-GitHub-Event": "check_run",
                "X-Hub-Signature-256": _sign(payload),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_pr_closed_action_is_ignored(self, client):
        payload_dict = _pr_payload(action="closed")
        payload = json.dumps(payload_dict).encode()
        resp = client.post(
            "/webhook/github",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": _sign(payload),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"


class TestWebhookQueueing:
    def test_pr_opened_is_queued(self, client):
        payload_dict = _pr_payload(action="opened")
        payload = json.dumps(payload_dict).encode()
        resp = client.post(
            "/webhook/github",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": _sign(payload),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["pr_number"] == 42
        assert data["repo"] == "RYKNSH/test-repo"

    def test_pr_synchronize_is_queued(self, client):
        payload_dict = _pr_payload(action="synchronize")
        payload = json.dumps(payload_dict).encode()
        resp = client.post(
            "/webhook/github",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": _sign(payload),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "queued"
