"""Velie QA Agent — Health Monitor & Self-Healing.

Provides health monitoring, error tracking, and
self-healing capabilities for the QA agent.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_HEALTH_FILE = _DATA_DIR / "health.json"


def _load_health() -> dict:
    """Load health data."""
    if not _HEALTH_FILE.exists():
        return {"errors": [], "restarts": [], "uptime_start": None}
    try:
        return json.loads(_HEALTH_FILE.read_text())
    except Exception:
        return {"errors": [], "restarts": [], "uptime_start": None}


def _save_health(data: dict) -> None:
    """Save health data."""
    _DATA_DIR.mkdir(exist_ok=True)
    _HEALTH_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def record_startup() -> None:
    """Record agent startup time."""
    data = _load_health()
    now = datetime.now(timezone.utc).isoformat()
    data["uptime_start"] = now
    data["restarts"].append({"timestamp": now, "pid": os.getpid()})
    data["restarts"] = data["restarts"][-100:]
    _save_health(data)
    logger.info("Health monitor: startup recorded (PID=%d)", os.getpid())


def record_error(
    error_type: str,
    error_message: str,
    context: dict | None = None,
) -> None:
    """Record an error for health tracking.

    Args:
        error_type: Category of error (e.g., "github_api", "llm", "queue").
        error_message: Error description.
        context: Additional context dict.
    """
    data = _load_health()
    data["errors"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": error_type,
        "message": error_message[:500],
        "context": context or {},
    })
    data["errors"] = data["errors"][-200:]
    _save_health(data)


def get_health_summary() -> dict:
    """Get a comprehensive health summary.

    Returns:
        Dict with error counts, uptime, restart history, and status.
    """
    data = _load_health()
    errors = data.get("errors", [])
    restarts = data.get("restarts", [])

    # Count errors in last hour (approximate)
    recent_errors = 0
    if errors:
        # Simple: count last 10 as "recent"
        recent_errors = min(len(errors), 10)

    # Determine health status
    if recent_errors > 5:
        status = "degraded"
    elif recent_errors > 0:
        status = "warning"
    else:
        status = "healthy"

    # Error breakdown by type
    error_types: dict[str, int] = {}
    for e in errors:
        et = e.get("type", "unknown")
        error_types[et] = error_types.get(et, 0) + 1

    return {
        "status": status,
        "uptime_start": data.get("uptime_start"),
        "total_errors": len(errors),
        "recent_errors": recent_errors,
        "error_types": error_types,
        "total_restarts": len(restarts),
        "pid": os.getpid(),
    }


def should_alert(threshold: int = 5) -> tuple[bool, str]:
    """Check if an alert should be sent based on error accumulation.

    Args:
        threshold: Number of recent errors to trigger alert.

    Returns:
        Tuple of (should_alert: bool, reason: str).
    """
    summary = get_health_summary()
    if summary["recent_errors"] >= threshold:
        return True, f"High error rate: {summary['recent_errors']} recent errors. Status: {summary['status']}"
    return False, "System healthy"
