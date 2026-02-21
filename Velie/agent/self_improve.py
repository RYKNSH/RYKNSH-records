"""Velie QA Agent — Self-Improvement Engine.

Uses feedback data to optimize prompt effectiveness
and track review quality over time.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_LEARNING_FILE = _DATA_DIR / "learning.json"


def _load_learning() -> dict:
    """Load learning data."""
    if not _LEARNING_FILE.exists():
        return {"prompt_adjustments": [], "quality_scores": [], "patterns": {}}
    try:
        return json.loads(_LEARNING_FILE.read_text())
    except Exception:
        return {"prompt_adjustments": [], "quality_scores": [], "patterns": {}}


def _save_learning(data: dict) -> None:
    """Save learning data."""
    _DATA_DIR.mkdir(exist_ok=True)
    _LEARNING_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def analyze_feedback_patterns() -> dict:
    """Analyze feedback data to identify improvement patterns.

    Returns:
        Dict with pattern analysis results.
    """
    from agent.feedback import _FEEDBACK_FILE

    if not _FEEDBACK_FILE.exists():
        return {"patterns": [], "suggestions": []}

    try:
        feedback = json.loads(_FEEDBACK_FILE.read_text())
    except Exception:
        return {"patterns": [], "suggestions": []}

    # Count outcomes
    outcomes: dict[str, int] = {}
    for record in feedback:
        ft = record.get("feedback_type", "unknown")
        outcomes[ft] = outcomes.get(ft, 0) + 1

    # Identify patterns
    patterns = []
    suggestions = []

    total_fixes = outcomes.get("fix_created", 0)
    ci_passed = outcomes.get("ci_passed", 0)
    ci_failed = outcomes.get("ci_failed", 0)

    if total_fixes > 0:
        fix_success_rate = ci_passed / total_fixes if total_fixes > 0 else 0
        patterns.append({
            "type": "fix_quality",
            "success_rate": round(fix_success_rate, 2),
            "total_fixes": total_fixes,
            "ci_passed": ci_passed,
            "ci_failed": ci_failed,
        })

        if fix_success_rate < 0.5 and total_fixes >= 3:
            suggestions.append(
                "Fix success rate is below 50%. Consider adjusting suggestion "
                "prompt to be more conservative with code changes."
            )
        elif fix_success_rate > 0.8:
            suggestions.append(
                "Fix success rate is above 80%. Auto-fix is working well — "
                "consider lowering auto_fix_threshold to 'warning' for more coverage."
            )

    # Track most problematic repos
    repo_issues: dict[str, int] = {}
    for record in feedback:
        if record.get("feedback_type") == "ci_failed":
            repo = record.get("repo_full_name", "unknown")
            repo_issues[repo] = repo_issues.get(repo, 0) + 1

    if repo_issues:
        worst_repo = max(repo_issues, key=repo_issues.get)
        patterns.append({
            "type": "problematic_repo",
            "repo": worst_repo,
            "failure_count": repo_issues[worst_repo],
        })

    return {"patterns": patterns, "suggestions": suggestions, "outcomes": outcomes}


def record_quality_score(
    pr_number: int,
    repo_full_name: str,
    score: float,
    source: str = "automated",
) -> None:
    """Record a quality score for a review.

    Args:
        pr_number: PR number.
        repo_full_name: Repository.
        score: Quality score (0.0-1.0).
        source: How the score was determined.
    """
    data = _load_learning()

    data["quality_scores"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pr_number": pr_number,
        "repo_full_name": repo_full_name,
        "score": score,
        "source": source,
    })

    # Cap at 500
    data["quality_scores"] = data["quality_scores"][-500:]

    _save_learning(data)


def get_quality_trend(repo_full_name: str | None = None) -> dict:
    """Get quality score trend.

    Returns:
        Dict with average score, trend direction, and count.
    """
    data = _load_learning()
    scores = data.get("quality_scores", [])

    if repo_full_name:
        scores = [s for s in scores if s.get("repo_full_name") == repo_full_name]

    if not scores:
        return {"average": 0.0, "trend": "neutral", "count": 0}

    values = [s["score"] for s in scores]
    avg = sum(values) / len(values)

    # Trend: compare last 5 vs first 5
    if len(values) >= 10:
        recent = sum(values[-5:]) / 5
        early = sum(values[:5]) / 5
        if recent > early + 0.05:
            trend = "improving"
        elif recent < early - 0.05:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "average": round(avg, 3),
        "trend": trend,
        "count": len(values),
    }
