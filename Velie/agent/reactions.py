"""Velie QA Agent — Review Reactions (PMF Measurement).

Track 👍/👎 reactions on reviews for PMF validation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_REACTIONS_FILE = _DATA_DIR / "reactions.json"


def _load_reactions() -> dict:
    """Load reactions data."""
    if not _REACTIONS_FILE.exists():
        return {"reviews": {}, "stats": {"total": 0, "helpful": 0, "not_helpful": 0}}
    try:
        return json.loads(_REACTIONS_FILE.read_text())
    except Exception:
        return {"reviews": {}, "stats": {"total": 0, "helpful": 0, "not_helpful": 0}}


def _save_reactions(data: dict) -> None:
    """Save reactions data."""
    _DATA_DIR.mkdir(exist_ok=True)
    _REACTIONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def record_reaction(
    review_id: str,
    reaction: str,
    tenant_id: str = "default",
    comment: str = "",
) -> dict:
    """Record a 👍 or 👎 reaction on a review.

    Args:
        review_id: Review identifier.
        reaction: "helpful" (👍) or "not_helpful" (👎).
        tenant_id: Tenant identifier.
        comment: Optional user comment on why.

    Returns:
        Updated reaction stats.
    """
    if reaction not in ("helpful", "not_helpful"):
        raise ValueError(f"Invalid reaction: {reaction}")

    data = _load_reactions()

    data["reviews"][review_id] = {
        "reaction": reaction,
        "tenant_id": tenant_id,
        "comment": comment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    data["stats"]["total"] += 1
    data["stats"][reaction] += 1

    _save_reactions(data)
    logger.info("Recorded %s reaction for review %s", reaction, review_id)

    return get_reaction_stats()


def get_reaction_stats() -> dict:
    """Get overall reaction statistics.

    Returns:
        Dict with total, helpful, not_helpful counts and helpfulness rate.
    """
    data = _load_reactions()
    stats = data["stats"]
    total = stats["total"]

    return {
        "total": total,
        "helpful": stats["helpful"],
        "not_helpful": stats["not_helpful"],
        "helpfulness_rate": round(stats["helpful"] / total, 3) if total > 0 else 0.0,
        "nps_proxy": round((stats["helpful"] - stats["not_helpful"]) / total * 100, 1) if total > 0 else 0.0,
    }


def get_review_reaction(review_id: str) -> dict | None:
    """Get the reaction for a specific review.

    Args:
        review_id: Review identifier.

    Returns:
        Reaction dict or None if no reaction recorded.
    """
    data = _load_reactions()
    return data["reviews"].get(review_id)
