"""Ada Core API — Usage Billing Foundation.

Tracks tool/node execution usage per tenant for billing purposes.
Granularity: per-request, per-node, per-tool.

MS4.2: Enables pay-per-use pricing model.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UsageRecord(BaseModel):
    """Single usage event record."""

    request_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # What was used
    event_type: str  # "node_execution", "tool_call", "llm_invocation"
    resource_name: str  # Node/tool name

    # Metrics
    tokens_used: int = 0
    execution_time_ms: float = 0.0
    cost_usd: float = 0.0


class UsageTracker:
    """Tracks and aggregates usage per tenant.

    Supports in-memory aggregation and Supabase persistence.
    """

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    def track(self, record: UsageRecord) -> None:
        """Record a usage event."""
        self._records.append(record)

    def track_from_state(
        self,
        state: dict[str, Any],
        request_id: str,
        tenant_id: str,
    ) -> list[UsageRecord]:
        """Auto-create usage records from graph execution state."""
        records: list[UsageRecord] = []

        # Node metrics
        node_metrics = state.get("node_metrics", [])
        for metric in node_metrics:
            record = UsageRecord(
                request_id=request_id,
                tenant_id=tenant_id,
                event_type="node_execution",
                resource_name=metric.get("node_name", "unknown"),
                execution_time_ms=metric.get("execution_time_ms", 0),
            )
            records.append(record)
            self.track(record)

        # LLM usage
        usage = state.get("usage", {})
        if usage.get("total_tokens", 0) > 0:
            from agent.observability import estimate_cost
            model = state.get("response_model", "unknown")
            record = UsageRecord(
                request_id=request_id,
                tenant_id=tenant_id,
                event_type="llm_invocation",
                resource_name=model,
                tokens_used=usage.get("total_tokens", 0),
                cost_usd=estimate_cost(model, usage.get("total_tokens", 0)),
            )
            records.append(record)
            self.track(record)

        return records

    def get_tenant_usage(
        self,
        tenant_id: str,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregated usage for a tenant."""
        records = [r for r in self._records if r.tenant_id == tenant_id]
        if since:
            records = [r for r in records if r.timestamp >= since]

        if not records:
            return {
                "tenant_id": tenant_id,
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "breakdown": {},
            }

        # Breakdown by event type
        breakdown: dict[str, dict[str, Any]] = {}
        for r in records:
            key = f"{r.event_type}:{r.resource_name}"
            if key not in breakdown:
                breakdown[key] = {"count": 0, "tokens": 0, "cost_usd": 0.0, "time_ms": 0.0}
            breakdown[key]["count"] += 1
            breakdown[key]["tokens"] += r.tokens_used
            breakdown[key]["cost_usd"] += r.cost_usd
            breakdown[key]["time_ms"] += r.execution_time_ms

        unique_requests = len(set(r.request_id for r in records))

        return {
            "tenant_id": tenant_id,
            "total_requests": unique_requests,
            "total_tokens": sum(r.tokens_used for r in records),
            "total_cost_usd": round(sum(r.cost_usd for r in records), 6),
            "total_time_ms": round(sum(r.execution_time_ms for r in records), 2),
            "breakdown": breakdown,
        }

    def generate_invoice(
        self,
        tenant_id: str,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate a billing invoice for a tenant."""
        usage = self.get_tenant_usage(tenant_id, since)

        # Apply markup
        markup = 1.3  # 30% margin
        billable = round(usage["total_cost_usd"] * markup, 4)

        return {
            "tenant_id": tenant_id,
            "period_start": since.isoformat() if since else "all_time",
            "total_cost_usd": usage["total_cost_usd"],
            "markup_rate": markup,
            "billable_amount_usd": billable,
            "usage_summary": usage,
        }


# Module singleton
usage_tracker = UsageTracker()
