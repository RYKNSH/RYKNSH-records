"""Velie QA Agent — Feedback Loop.

Collects and stores feedback on review quality for continuous improvement.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Local feedback storage
_FEEDBACK_DIR = Path(__file__).parent.parent / "data"
_FEEDBACK_FILE = _FEEDBACK_DIR / "feedback.json"


def record_feedback(
    pr_number: int,
    repo_full_name: str,
    feedback_type: str,
    details: dict | None = None,
) -> None:
    """Record feedback about a review for learning.

    Args:
        pr_number: PR number.
        repo_full_name: Repository full name.
        feedback_type: Type of feedback (e.g., "fix_applied", "fix_rejected",
                       "suggestion_accepted", "ci_passed", "ci_failed").
        details: Additional details dict.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pr_number": pr_number,
        "repo_full_name": repo_full_name,
        "feedback_type": feedback_type,
        "details": details or {},
    }

    _FEEDBACK_DIR.mkdir(exist_ok=True)

    existing: list = []
    if _FEEDBACK_FILE.exists():
        try:
            existing = json.loads(_FEEDBACK_FILE.read_text())
        except Exception:
            existing = []

    existing.insert(0, record)
    existing = existing[:1000]  # cap at 1000

    _FEEDBACK_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    logger.info(
        "Recorded feedback: %s for PR #%d in %s",
        feedback_type, pr_number, repo_full_name,
    )


def get_feedback_stats(repo_full_name: str | None = None) -> dict:
    """Get summarized feedback statistics.

    Args:
        repo_full_name: Optional filter by repository.

    Returns:
        Dict with counts by feedback_type.
    """
    if not _FEEDBACK_FILE.exists():
        return {"total": 0, "by_type": {}}

    try:
        data = json.loads(_FEEDBACK_FILE.read_text())
    except Exception:
        return {"total": 0, "by_type": {}}

    if repo_full_name:
        data = [d for d in data if d.get("repo_full_name") == repo_full_name]

    by_type: dict[str, int] = {}
    for record in data:
        ft = record.get("feedback_type", "unknown")
        by_type[ft] = by_type.get(ft, 0) + 1

    return {"total": len(data), "by_type": by_type}
