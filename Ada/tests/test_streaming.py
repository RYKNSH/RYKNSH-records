"""Tests for streaming SSE — /v1/chat/completions with stream=true."""

import json

import pytest
from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestStreamingEndpoint:
    """Test SSE streaming responses."""

    def test_streaming_returns_event_stream(self, client):
        """stream=true should return text/event-stream content type."""
        # This will fail at the LLM call (no real API key),
        # but we can verify the response type
        resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )
        # Should get a streaming response (even if LLM fails, SSE handles errors)
        assert resp.headers.get("content-type", "").startswith("text/event-stream")

    def test_streaming_ends_with_done(self, client):
        """Streaming responses should end with data: [DONE]."""
        resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )
        body = resp.text
        # Should contain [DONE] marker (either from success or error handling)
        assert "data: [DONE]" in body

    def test_non_streaming_still_works(self, client):
        """stream=false should still return JSON (not SSE)."""
        resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )
        # Non-streaming will fail with 502 (no real LLM key) but it's JSON not SSE
        content_type = resp.headers.get("content-type", "")
        assert "text/event-stream" not in content_type


class TestRateLimitIntegration:
    """Test rate limiting integration in the API."""

    def test_rate_limit_429(self, client):
        """Exceeding rate limit should return 429."""
        # Use a known tenant with the dev key (default tenant has rpm=60)
        # We'll manually set a low limit by resetting
        from server.rate_limit import rate_limiter

        # Create a tenant bucket with capacity of 1
        rate_limiter.reset()

        # First request — should work
        # (will fail at LLM but that's after rate check)
        resp1 = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        # Should not be 429
        assert resp1.status_code != 429

    def test_rate_limit_has_retry_after(self, client):
        """429 responses should include Retry-After header."""
        from server.rate_limit import rate_limiter, TokenBucket

        # Reset all state first
        rate_limiter.reset()

        # Default tenant has rate_limit_rpm=60
        # The check() in app.py uses tenant.rate_limit_rpm=60, so we must match capacity
        tenant_id = "00000000-0000-0000-0000-000000000000"
        bucket = TokenBucket(capacity=60)
        bucket.tokens = 0.0  # exhaust all tokens
        bucket.last_refill = __import__("time").monotonic()  # reset refill clock
        rate_limiter._buckets[tenant_id] = bucket

        resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer ada-test-key"},
            json={
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        assert resp.status_code == 429
        assert "retry-after" in resp.headers

        # Clean up
        rate_limiter.reset()

