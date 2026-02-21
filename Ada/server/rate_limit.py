"""Ada Core API — Rate Limiting.

Token-bucket rate limiter with per-tenant limits.
Uses in-memory tracking with optional Redis backend for distributed deployments.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Simple token bucket for rate limiting."""

    capacity: int  # max tokens (requests per minute)
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def consume(self) -> bool:
        """Try to consume one token. Returns True if allowed, False if rate-limited."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Refill tokens based on elapsed time (tokens per second = capacity / 60)
        refill_rate = self.capacity / 60.0
        self.tokens = min(self.capacity, self.tokens + elapsed * refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    def retry_after(self) -> float:
        """Seconds until next token is available."""
        if self.tokens >= 1.0:
            return 0.0
        refill_rate = self.capacity / 60.0
        if refill_rate <= 0:
            return 60.0
        return (1.0 - self.tokens) / refill_rate


class RateLimiter:
    """Per-tenant rate limiter using token buckets."""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    def check(self, tenant_id: str, rate_limit_rpm: int) -> tuple[bool, float]:
        """Check if a request is allowed for the given tenant.

        Args:
            tenant_id: Unique tenant identifier
            rate_limit_rpm: Requests per minute limit for this tenant

        Returns:
            Tuple of (allowed: bool, retry_after: float seconds)
        """
        if tenant_id not in self._buckets:
            self._buckets[tenant_id] = TokenBucket(capacity=rate_limit_rpm)
        else:
            # Update capacity if tenant config changed
            bucket = self._buckets[tenant_id]
            if bucket.capacity != rate_limit_rpm:
                self._buckets[tenant_id] = TokenBucket(capacity=rate_limit_rpm)

        bucket = self._buckets[tenant_id]
        allowed = bucket.consume()
        retry_after = 0.0 if allowed else bucket.retry_after()

        if not allowed:
            logger.warning(
                "Rate limited tenant %s (limit=%d rpm, retry_after=%.1fs)",
                tenant_id, rate_limit_rpm, retry_after,
            )

        return allowed, retry_after

    def reset(self, tenant_id: str | None = None) -> None:
        """Reset rate limit state. If tenant_id is None, reset all."""
        if tenant_id:
            self._buckets.pop(tenant_id, None)
        else:
            self._buckets.clear()


# Global rate limiter singleton
rate_limiter = RateLimiter()
