"""Ada Core API — Quality Tester (Implicit Signal Collector).

Collects and analyzes implicit quality signals from request execution:
1. Explicit feedback (👍/👎 + comments)
2. Implicit signals (retry rate, edit distance, response time)
3. Quality metrics (validation score, grounding score, cost)

WHITEPAPER ref: Section 3 — Evolution Layer, tester
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FeedbackRecord(BaseModel):
    """A single feedback record (explicit or implicit)."""

    request_id: str
    tenant_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Explicit feedback
    rating: int | None = None  # 1 (👎) or 5 (👍)
    comment: str = ""
    comment_category: str = ""  # "helpful", "inaccurate", "incomplete", "off_topic"

    # Implicit signals
    was_retried: bool = False
    response_edited: bool = False
    response_time_ms: float = 0.0
    follow_up_count: int = 0  # Number of follow-up messages in same thread

    # Quality metrics (from validator/observability)
    validation_score: float = 1.0
    grounding_score: float = 1.0
    model_used: str = ""
    tokens_used: int = 0
    cost_usd: float = 0.0

    def overall_score(self) -> float:
        """Calculate overall quality score (0.0-1.0).

        Combines explicit and implicit signals with weights.
        """
        score = 0.0
        weight_sum = 0.0

        # Explicit rating (highest weight)
        if self.rating is not None:
            score += (self.rating / 5.0) * 0.4
            weight_sum += 0.4

        # Validation score
        score += self.validation_score * 0.25
        weight_sum += 0.25

        # Grounding score
        score += self.grounding_score * 0.15
        weight_sum += 0.15

        # Implicit signals (negative indicators)
        implicit_penalty = 0.0
        if self.was_retried:
            implicit_penalty += 0.3
        if self.response_edited:
            implicit_penalty += 0.2
        score += max(0.0, 1.0 - implicit_penalty) * 0.2
        weight_sum += 0.2

        return round(score / weight_sum, 3) if weight_sum > 0 else 0.5


class QualityTester:
    """Collects and analyzes quality feedback.

    Aggregates feedback records per tenant and provides
    statistical summaries for the evolver.
    """

    def __init__(self) -> None:
        self._records: list[FeedbackRecord] = []

    def record(self, feedback: FeedbackRecord) -> None:
        """Record a feedback entry."""
        self._records.append(feedback)
        logger.debug(
            "Feedback recorded: req=%s score=%.3f",
            feedback.request_id, feedback.overall_score(),
        )

    def record_from_state(
        self,
        state: dict[str, Any],
        request_id: str,
        tenant_id: str = "",
    ) -> FeedbackRecord:
        """Auto-create feedback from graph execution state."""
        feedback = FeedbackRecord(
            request_id=request_id,
            tenant_id=tenant_id,
            validation_score=state.get("validation_score", 1.0),
            was_retried=state.get("retry_count", 0) > 0,
            model_used=state.get("response_model", ""),
            tokens_used=state.get("usage", {}).get("total_tokens", 0),
        )
        self.record(feedback)
        return feedback

    def get_tenant_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get aggregated statistics for a tenant."""
        tenant_records = [r for r in self._records if r.tenant_id == tenant_id]
        if not tenant_records:
            return {"count": 0, "avg_score": 0.0}

        scores = [r.overall_score() for r in tenant_records]
        return {
            "count": len(tenant_records),
            "avg_score": round(sum(scores) / len(scores), 3),
            "min_score": round(min(scores), 3),
            "max_score": round(max(scores), 3),
            "retry_rate": round(
                sum(1 for r in tenant_records if r.was_retried) / len(tenant_records), 3,
            ),
            "model_distribution": _count_models(tenant_records),
        }

    def get_model_stats(self, tenant_id: str = "") -> dict[str, dict[str, float]]:
        """Get per-model quality statistics."""
        records = self._records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]

        by_model: dict[str, list[float]] = {}
        for r in records:
            model = r.model_used or "unknown"
            by_model.setdefault(model, []).append(r.overall_score())

        return {
            model: {
                "count": len(scores),
                "avg_score": round(sum(scores) / len(scores), 3),
                "success_rate": round(
                    sum(1 for s in scores if s >= 0.7) / len(scores), 3,
                ),
            }
            for model, scores in by_model.items()
        }

    @property
    def total_records(self) -> int:
        return len(self._records)


def _count_models(records: list[FeedbackRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        model = r.model_used or "unknown"
        counts[model] = counts.get(model, 0) + 1
    return counts


# Module-level singleton
quality_tester = QualityTester()
