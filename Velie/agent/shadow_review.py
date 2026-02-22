"""Velie QA Agent — Shadow Review.

Run Velie reviews on already-merged PRs to measure accuracy
without affecting real repositories. Compares AI review with
human review outcomes.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_SHADOW_DIR = _DATA_DIR / "shadow_reviews"


async def fetch_merged_prs(
    repo: str,
    token: str,
    limit: int = 50,
) -> list[dict]:
    """Fetch recently merged PRs from a GitHub repository.

    Args:
        repo: Repository full name (e.g., 'langchain-ai/langchain').
        token: GitHub personal access token.
        limit: Maximum number of PRs to fetch.

    Returns:
        List of PR dicts with number, title, author, body.
    """
    prs = []
    page = 1
    per_page = min(limit, 100)

    async with httpx.AsyncClient(timeout=30) as client:
        while len(prs) < limit:
            res = await client.get(
                f"https://api.github.com/repos/{repo}/pulls",
                params={
                    "state": "closed",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": per_page,
                    "page": page,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )

            if res.status_code != 200:
                logger.warning("GitHub API error %d for %s", res.status_code, repo)
                break

            data = res.json()
            if not data:
                break

            for pr in data:
                if pr.get("merged_at"):
                    prs.append({
                        "number": pr["number"],
                        "title": pr["title"],
                        "author": pr["user"]["login"],
                        "body": (pr.get("body") or "")[:500],
                        "merged_at": pr["merged_at"],
                        "review_comments": pr.get("review_comments", 0),
                    })
                    if len(prs) >= limit:
                        break

            page += 1

    logger.info("Fetched %d merged PRs from %s", len(prs), repo)
    return prs


async def fetch_pr_diff(
    repo: str,
    pr_number: int,
    token: str,
    max_chars: int = 60000,
) -> str:
    """Fetch the diff for a specific PR.

    Args:
        repo: Repository full name.
        pr_number: PR number.
        token: GitHub token.
        max_chars: Maximum diff size in characters.

    Returns:
        Diff string, truncated if necessary.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3.diff",
            },
        )

        if res.status_code != 200:
            return ""

        diff = res.text
        if len(diff) > max_chars:
            diff = diff[:max_chars] + "\n\n... [diff truncated]"

        return diff


async def fetch_human_reviews(
    repo: str,
    pr_number: int,
    token: str,
) -> list[dict]:
    """Fetch human review comments for a PR.

    Args:
        repo: Repository full name.
        pr_number: PR number.
        token: GitHub token.

    Returns:
        List of review comment dicts.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )

        if res.status_code != 200:
            return []

        reviews = res.json()
        return [
            {
                "author": r["user"]["login"],
                "state": r["state"],
                "body": (r.get("body") or "")[:500],
            }
            for r in reviews
            if r.get("state") in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED")
        ]


def save_shadow_result(
    repo: str,
    pr_number: int,
    velie_review: str,
    velie_severity: str,
    human_reviews: list[dict],
    human_outcome: str,
) -> None:
    """Save a shadow review result for later analysis.

    Args:
        repo: Repository full name.
        pr_number: PR number.
        velie_review: Velie's review body.
        velie_severity: Velie's severity classification.
        human_reviews: Human review data.
        human_outcome: Human outcome (approved/changes_requested).
    """
    _SHADOW_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "repo": repo,
        "pr_number": pr_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "velie": {
            "severity": velie_severity,
            "review_length": len(velie_review),
            "review_body": velie_review[:2000],
        },
        "human": {
            "outcome": human_outcome,
            "review_count": len(human_reviews),
            "reviews": human_reviews,
        },
        "agreement": _check_agreement(velie_severity, human_outcome),
    }

    safe_repo = repo.replace("/", "__")
    path = _SHADOW_DIR / f"{safe_repo}_pr{pr_number}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    logger.info("Saved shadow review: %s PR#%d (agreement=%s)", repo, pr_number, result["agreement"])


def _check_agreement(velie_severity: str, human_outcome: str) -> str:
    """Check if Velie and human reviewers agree.

    Returns:
        'agree', 'false_positive', 'false_negative', or 'unknown'.
    """
    velie_flagged = velie_severity in ("critical", "warning")
    human_flagged = human_outcome == "changes_requested"

    if velie_flagged and human_flagged:
        return "true_positive"
    if not velie_flagged and not human_flagged:
        return "true_negative"
    if velie_flagged and not human_flagged:
        return "false_positive"
    if not velie_flagged and human_flagged:
        return "false_negative"
    return "unknown"


def generate_accuracy_report() -> dict:
    """Generate an accuracy report from all shadow reviews.

    Returns:
        Report dict with precision, recall, F1, and per-repo stats.
    """
    _SHADOW_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for path in _SHADOW_DIR.glob("*.json"):
        try:
            results.append(json.loads(path.read_text()))
        except Exception:
            continue

    if not results:
        return {"total": 0, "message": "No shadow reviews yet"}

    # Aggregate
    tp = sum(1 for r in results if r.get("agreement") == "true_positive")
    tn = sum(1 for r in results if r.get("agreement") == "true_negative")
    fp = sum(1 for r in results if r.get("agreement") == "false_positive")
    fn = sum(1 for r in results if r.get("agreement") == "false_negative")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Per-repo breakdown
    repos: dict[str, dict] = {}
    for r in results:
        repo = r["repo"]
        if repo not in repos:
            repos[repo] = {"total": 0, "agree": 0}
        repos[repo]["total"] += 1
        if r.get("agreement") in ("true_positive", "true_negative"):
            repos[repo]["agree"] += 1

    return {
        "total": len(results),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "repos": {
            repo: {
                "total": stats["total"],
                "accuracy": round(stats["agree"] / stats["total"], 3) if stats["total"] > 0 else 0,
            }
            for repo, stats in repos.items()
        },
    }
