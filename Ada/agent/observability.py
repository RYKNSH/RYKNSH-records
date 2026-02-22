"""Ada Core API — Observability Module.

Provides execution metrics, timing, and resource management for all graph nodes.
Every AdaNode automatically gets observability through the base class wrapper.

Features:
- NodeTimer: Measures execution time per node
- NodeMetrics: Structured metrics data (time, tokens, cost)
- MetricsCollector: Request-scoped metrics aggregation (tenant isolation)
- ResourceLimiter: Per-node resource limits (timeout, token caps)

WHITEPAPER ref: Section 6 — Observability, Section Security — リソース管理
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metrics Data
# ---------------------------------------------------------------------------

@dataclass
class NodeMetrics:
    """Execution metrics for a single node invocation."""

    node_name: str
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_name": self.node_name,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "tokens_used": self.tokens_used,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "success": self.success,
            "error": self.error,
        }


@dataclass
class RequestMetrics:
    """Aggregated metrics for an entire request pipeline."""

    request_id: str = ""
    tenant_id: str = ""
    total_time_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    node_metrics: list[NodeMetrics] = field(default_factory=list)

    def add(self, metrics: NodeMetrics) -> None:
        self.node_metrics.append(metrics)
        self.total_time_ms += metrics.execution_time_ms
        self.total_tokens += metrics.tokens_used
        self.total_cost_usd += metrics.estimated_cost_usd

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "total_time_ms": round(self.total_time_ms, 2),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "nodes": [m.to_dict() for m in self.node_metrics],
        }


# ---------------------------------------------------------------------------
# Metrics Collector (request-scoped, thread-safe)
# ---------------------------------------------------------------------------

class MetricsCollector:
    """Collects metrics for a single request pipeline.

    Usage:
        collector = MetricsCollector(request_id="abc", tenant_id="xyz")
        collector.record(NodeMetrics(node_name="sentinel", execution_time_ms=1.2))
        summary = collector.summary()
    """

    def __init__(self, request_id: str = "", tenant_id: str = "") -> None:
        self._metrics = RequestMetrics(request_id=request_id, tenant_id=tenant_id)

    def record(self, metrics: NodeMetrics) -> None:
        """Record metrics for a node execution."""
        self._metrics.add(metrics)
        logger.debug(
            "Node [%s] completed in %.2fms (tokens=%d)",
            metrics.node_name, metrics.execution_time_ms, metrics.tokens_used,
        )

    def summary(self) -> dict[str, Any]:
        """Get aggregated metrics summary."""
        return self._metrics.to_dict()

    @property
    def total_time_ms(self) -> float:
        return self._metrics.total_time_ms

    @property
    def total_tokens(self) -> int:
        return self._metrics.total_tokens

    @property
    def node_count(self) -> int:
        return len(self._metrics.node_metrics)


# ---------------------------------------------------------------------------
# Resource Limiter
# ---------------------------------------------------------------------------

# Default resource limits per node
DEFAULT_NODE_TIMEOUT_SEC = 30.0
DEFAULT_MAX_TOKENS_PER_NODE = 100_000

# Cost estimates per 1K tokens (USD)
COST_PER_1K_TOKENS: dict[str, float] = {
    "claude-sonnet-4-20250514": 0.015,
    "gpt-4o": 0.010,
    "gpt-4o-mini": 0.0003,
}


@dataclass
class ResourceLimits:
    """Resource limits for a node execution."""

    timeout_sec: float = DEFAULT_NODE_TIMEOUT_SEC
    max_tokens: int = DEFAULT_MAX_TOKENS_PER_NODE


def estimate_cost(model: str, tokens: int) -> float:
    """Estimate cost based on model and token count."""
    rate = COST_PER_1K_TOKENS.get(model, 0.01)
    return (tokens / 1000) * rate


# ---------------------------------------------------------------------------
# Node Timer (decorator / wrapper)
# ---------------------------------------------------------------------------

async def timed_node_execution(
    node_name: str,
    coro,
    collector: MetricsCollector | None = None,
    limits: ResourceLimits | None = None,
) -> dict:
    """Execute a node coroutine with timing and resource limits.

    Args:
        node_name: Name of the node being executed.
        coro: The awaitable coroutine to execute.
        collector: Optional MetricsCollector to record metrics.
        limits: Optional ResourceLimits for timeout enforcement.

    Returns:
        The result dict from the node.

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout.
    """
    limits = limits or ResourceLimits()
    start = time.perf_counter()
    error_msg = None
    success = True

    try:
        result = await asyncio.wait_for(coro, timeout=limits.timeout_sec)
    except asyncio.TimeoutError:
        error_msg = f"Node '{node_name}' timed out after {limits.timeout_sec}s"
        logger.error(error_msg)
        success = False
        result = {}
        raise
    except Exception as e:
        error_msg = str(e)
        success = False
        result = {}
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        metrics = NodeMetrics(
            node_name=node_name,
            execution_time_ms=elapsed_ms,
            success=success,
            error=error_msg,
        )
        if collector:
            collector.record(metrics)

    return result
