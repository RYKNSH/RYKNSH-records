"""Velie QA Agent — Trust Score & Review Quality Tracking.

Tracks suggestion acceptance rates, review precision,
and generates trust metrics for the dashboard.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_TRUST_FILE = _DATA_DIR / "trust.json"


def _load_trust() -> dict:
    """Load trust data."""
    if not _TRUST_FILE.exists():
        return {"events": [], "repos": {}}
    try:
        return json.loads(_TRUST_FILE.read_text())
    except Exception:
        return {"events": [], "repos": {}}


def _save_trust(data: dict) -> None:
    """Save trust data."""
    _DATA_DIR.mkdir(exist_ok=True)
    _TRUST_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def record_suggestion_outcome(
    repo_full_name: str,
    pr_number: int,
    suggestion_count: int,
    accepted_count: int,
) -> None:
    """Record how many suggestions were accepted for a PR.

    Args:
        repo_full_name: Repository.
        pr_number: PR number.
        suggestion_count: Total suggestions made.
        accepted_count: Suggestions accepted by developer.
    """
    data = _load_trust()

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": repo_full_name,
        "pr_number": pr_number,
        "suggestions": suggestion_count,
        "accepted": accepted_count,
        "rate": round(accepted_count / suggestion_count, 3) if suggestion_count > 0 else 0.0,
    }

    data["events"].append(event)
    data["events"] = data["events"][-500:]

    # Update repo-level stats
    if repo_full_name not in data["repos"]:
        data["repos"][repo_full_name] = {"total_suggestions": 0, "total_accepted": 0}

    repo_stats = data["repos"][repo_full_name]
    repo_stats["total_suggestions"] += suggestion_count
    repo_stats["total_accepted"] += accepted_count

    _save_trust(data)


def record_review_verdict(
    repo_full_name: str,
    pr_number: int,
    velie_flagged: bool,
    was_real_bug: bool,
) -> None:
    """Record whether a Velie finding was a real bug or false positive.

    Args:
        repo_full_name: Repository.
        pr_number: PR number.
        velie_flagged: Whether Velie flagged an issue.
        was_real_bug: Whether it was actually a bug.
    """
    data = _load_trust()

    if repo_full_name not in data["repos"]:
        data["repos"][repo_full_name] = {"total_suggestions": 0, "total_accepted": 0}

    repo_stats = data["repos"][repo_full_name]

    if velie_flagged and was_real_bug:
        repo_stats["true_positives"] = repo_stats.get("true_positives", 0) + 1
    elif velie_flagged and not was_real_bug:
        repo_stats["false_positives"] = repo_stats.get("false_positives", 0) + 1
    elif not velie_flagged and was_real_bug:
        repo_stats["missed_bugs"] = repo_stats.get("missed_bugs", 0) + 1

    _save_trust(data)


def get_trust_score(repo_full_name: str | None = None) -> dict:
    """Calculate trust score for a repo or globally.

    Returns:
        Dict with acceptance_rate, precision, trust_score, trend.
    """
    data = _load_trust()

    if repo_full_name:
        repos = {repo_full_name: data["repos"].get(repo_full_name, {})}
    else:
        repos = data.get("repos", {})

    total_suggestions = sum(r.get("total_suggestions", 0) for r in repos.values())
    total_accepted = sum(r.get("total_accepted", 0) for r in repos.values())
    true_positives = sum(r.get("true_positives", 0) for r in repos.values())
    false_positives = sum(r.get("false_positives", 0) for r in repos.values())

    acceptance_rate = (
        round(total_accepted / total_suggestions, 3)
        if total_suggestions > 0 else 0.0
    )

    precision = (
        round(true_positives / (true_positives + false_positives), 3)
        if (true_positives + false_positives) > 0 else 0.0
    )

    # Trust score = weighted average of acceptance rate and precision
    trust_score = round(acceptance_rate * 0.6 + precision * 0.4, 3)

    # Trend from recent events
    events = data.get("events", [])
    if repo_full_name:
        events = [e for e in events if e.get("repo") == repo_full_name]

    if len(events) >= 10:
        recent = [e["rate"] for e in events[-5:]]
        earlier = [e["rate"] for e in events[:5]]
        recent_avg = sum(recent) / len(recent)
        earlier_avg = sum(earlier) / len(earlier)
        if recent_avg > earlier_avg + 0.05:
            trend = "improving"
        elif recent_avg < earlier_avg - 0.05:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "trust_score": trust_score,
        "acceptance_rate": acceptance_rate,
        "precision": precision,
        "total_suggestions": total_suggestions,
        "total_accepted": total_accepted,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "trend": trend,
    }
