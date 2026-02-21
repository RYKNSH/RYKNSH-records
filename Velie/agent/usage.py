"""Velie QA Agent — Usage Tracking & Billing.

Tracks review usage per tenant for billing purposes.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_USAGE_FILE = _DATA_DIR / "usage.json"

# Plan limits
PLAN_LIMITS = {
    "free": {"reviews_per_month": 5, "repos": 1, "model": "claude-haiku"},
    "pro": {"reviews_per_month": -1, "repos": 10, "model": "claude-sonnet"},
    "enterprise": {"reviews_per_month": -1, "repos": -1, "model": "claude-opus"},
}


def _load_usage() -> dict:
    """Load usage data from local JSON."""
    if not _USAGE_FILE.exists():
        return {}
    try:
        return json.loads(_USAGE_FILE.read_text())
    except Exception:
        return {}


def _save_usage(data: dict) -> None:
    """Save usage data to local JSON."""
    _DATA_DIR.mkdir(exist_ok=True)
    _USAGE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def record_usage(
    tenant_id: str,
    repo_full_name: str,
    pr_number: int,
    model_used: str,
) -> None:
    """Record a review usage event.

    Args:
        tenant_id: Tenant identifier.
        repo_full_name: Repository full name.
        pr_number: PR number.
        model_used: Model used for the review.
    """
    data = _load_usage()
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")

    if tenant_id not in data:
        data[tenant_id] = {"plan": "free", "months": {}}

    if month_key not in data[tenant_id]["months"]:
        data[tenant_id]["months"][month_key] = {
            "review_count": 0,
            "repos": [],
            "events": [],
        }

    month_data = data[tenant_id]["months"][month_key]
    month_data["review_count"] += 1

    if repo_full_name not in month_data["repos"]:
        month_data["repos"].append(repo_full_name)

    month_data["events"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": repo_full_name,
        "pr_number": pr_number,
        "model": model_used,
    })

    # Cap events at 500 per month
    month_data["events"] = month_data["events"][-500:]

    _save_usage(data)
    logger.info(
        "Recorded usage: tenant=%s, month=%s, count=%d",
        tenant_id, month_key, month_data["review_count"],
    )


def get_usage(tenant_id: str, month: str | None = None) -> dict:
    """Get usage data for a tenant.

    Args:
        tenant_id: Tenant identifier.
        month: Optional month key (YYYY-MM). Defaults to current month.

    Returns:
        Usage data dict with review_count, repos, plan, limit info.
    """
    data = _load_usage()
    month_key = month or datetime.now(timezone.utc).strftime("%Y-%m")

    tenant_data = data.get(tenant_id, {"plan": "free", "months": {}})
    plan = tenant_data.get("plan", "free")
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    month_data = tenant_data.get("months", {}).get(month_key, {
        "review_count": 0,
        "repos": [],
    })

    review_count = month_data.get("review_count", 0)
    reviews_limit = limits["reviews_per_month"]

    return {
        "tenant_id": tenant_id,
        "plan": plan,
        "month": month_key,
        "review_count": review_count,
        "reviews_limit": reviews_limit,
        "repos_count": len(month_data.get("repos", [])),
        "repos_limit": limits["repos"],
        "at_limit": reviews_limit > 0 and review_count >= reviews_limit,
        "usage_percent": min(
            (review_count / reviews_limit * 100) if reviews_limit > 0 else 0,
            100,
        ),
    }


def check_usage_allowed(tenant_id: str) -> tuple[bool, str]:
    """Check if a tenant is allowed to perform a review.

    Returns:
        Tuple of (allowed: bool, reason: str).
    """
    usage = get_usage(tenant_id)

    if usage["at_limit"]:
        return False, f"Monthly review limit reached ({usage['reviews_limit']} reviews). Upgrade to Pro for unlimited."

    return True, "ok"


def update_plan(tenant_id: str, plan: str) -> None:
    """Update a tenant's plan.

    Args:
        tenant_id: Tenant identifier.
        plan: New plan name ("free", "pro", "enterprise").
    """
    if plan not in PLAN_LIMITS:
        raise ValueError(f"Unknown plan: {plan}")

    data = _load_usage()
    if tenant_id not in data:
        data[tenant_id] = {"plan": plan, "months": {}}
    else:
        data[tenant_id]["plan"] = plan

    _save_usage(data)
    logger.info("Updated plan for tenant %s to %s", tenant_id, plan)
