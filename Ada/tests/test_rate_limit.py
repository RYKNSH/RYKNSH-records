"""Tests for server.rate_limit — Token Bucket rate limiter."""

import time

from server.rate_limit import RateLimiter, TokenBucket


class TestTokenBucket:
    """Test individual token bucket mechanics."""

    def test_initial_tokens(self):
        bucket = TokenBucket(capacity=60)
        assert bucket.tokens == 60.0

    def test_consume_success(self):
        bucket = TokenBucket(capacity=10)
        assert bucket.consume() is True
        assert bucket.tokens < 10.0

    def test_consume_exhaustion(self):
        bucket = TokenBucket(capacity=2)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_retry_after_positive(self):
        bucket = TokenBucket(capacity=60)
        # Exhaust all tokens
        for _ in range(60):
            bucket.consume()
        assert bucket.consume() is False
        retry = bucket.retry_after()
        assert retry > 0

    def test_retry_after_zero_when_available(self):
        bucket = TokenBucket(capacity=60)
        assert bucket.retry_after() == 0.0


class TestRateLimiter:
    """Test per-tenant rate limiting."""

    def test_allow_within_limit(self):
        limiter = RateLimiter()
        allowed, retry = limiter.check("tenant-1", 60)
        assert allowed is True
        assert retry == 0.0

    def test_different_tenants_independent(self):
        limiter = RateLimiter()
        # Exhaust tenant-1 (capacity=2)
        limiter.check("tenant-1", 2)
        limiter.check("tenant-1", 2)
        allowed1, _ = limiter.check("tenant-1", 2)

        # tenant-2 should still be allowed
        allowed2, _ = limiter.check("tenant-2", 60)

        assert allowed1 is False
        assert allowed2 is True

    def test_reset_tenant(self):
        limiter = RateLimiter()
        limiter.check("tenant-1", 2)
        limiter.check("tenant-1", 2)
        limiter.check("tenant-1", 2)  # Should be rate limited

        limiter.reset("tenant-1")
        allowed, _ = limiter.check("tenant-1", 2)
        assert allowed is True

    def test_reset_all(self):
        limiter = RateLimiter()
        limiter.check("tenant-1", 2)
        limiter.check("tenant-2", 2)
        limiter.reset()
        allowed1, _ = limiter.check("tenant-1", 2)
        allowed2, _ = limiter.check("tenant-2", 2)
        assert allowed1 is True
        assert allowed2 is True

    def test_rate_limit_returns_retry_after(self):
        limiter = RateLimiter()
        limiter.check("tenant-x", 1)
        allowed, retry = limiter.check("tenant-x", 1)
        assert allowed is False
        assert retry > 0

    def test_capacity_update(self):
        limiter = RateLimiter()
        limiter.check("tenant-1", 10)
        # Update capacity
        limiter.check("tenant-1", 100)
        # New bucket should be created with 100 capacity
        allowed, _ = limiter.check("tenant-1", 100)
        assert allowed is True
