"""Ada Core API — Feedback API Endpoint.

REST endpoint for collecting explicit user feedback (👍/👎).

WHITEPAPER ref: Section 3 — フィードバック収集
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    """Feedback submission request."""

    request_id: str
    rating: int = Field(ge=1, le=5, description="1=bad, 5=great")
    comment: str = ""
    category: str = ""  # "helpful", "inaccurate", "incomplete", "off_topic"


class FeedbackResponse(BaseModel):
    """Feedback submission response."""

    success: bool = True
    message: str = "Feedback recorded"


async def submit_feedback(
    request: FeedbackRequest,
    tenant_id: str = "",
) -> FeedbackResponse:
    """Process a feedback submission.

    Records both to QualityTester (in-memory) and Supabase (if available).
    """
    from agent.evolution.tester import FeedbackRecord, quality_tester

    record = FeedbackRecord(
        request_id=request.request_id,
        tenant_id=tenant_id,
        rating=request.rating,
        comment=request.comment,
        comment_category=request.category,
    )
    quality_tester.record(record)

    # Persist to Supabase if available
    await _persist_feedback(record)

    logger.info(
        "Feedback submitted: req=%s rating=%d tenant=%s",
        request.request_id, request.rating, tenant_id,
    )

    return FeedbackResponse()


async def _persist_feedback(record) -> None:
    """Persist feedback to Supabase (best effort)."""
    try:
        from server.config import get_settings
        cfg = get_settings()
        if not (cfg.supabase_url and cfg.supabase_anon_key):
            return

        import httpx
        url = f"{cfg.supabase_url}/rest/v1/ada_feedback"
        headers = {
            "apikey": cfg.supabase_anon_key,
            "Authorization": f"Bearer {cfg.supabase_anon_key}",
            "Content-Type": "application/json",
        }
        row = {
            "request_id": record.request_id,
            "tenant_id": record.tenant_id,
            "rating": record.rating,
            "comment": record.comment,
            "comment_category": record.comment_category,
            "validation_score": record.validation_score,
            "was_retried": record.was_retried,
            "model_used": record.model_used,
            "tokens_used": record.tokens_used,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, headers=headers, json=row)
    except Exception:
        logger.debug("Feedback persistence to Supabase failed (non-critical)")
