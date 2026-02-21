"""Velie QA Agent — CI Status Monitor.

Monitors GitHub Actions check run status for Fix PRs and
provides feedback on whether fixes pass CI.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def get_check_runs(
    client: httpx.AsyncClient,
    repo: str,
    commit_sha: str,
    headers: dict,
) -> list[dict]:
    """Get check runs for a specific commit.

    Returns:
        List of check run dicts with name, status, and conclusion.
    """
    resp = await client.get(
        f"https://api.github.com/repos/{repo}/commits/{commit_sha}/check-runs",
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()

    return [
        {
            "name": cr["name"],
            "status": cr["status"],  # queued, in_progress, completed
            "conclusion": cr.get("conclusion"),  # success, failure, etc.
            "html_url": cr.get("html_url", ""),
        }
        for cr in data.get("check_runs", [])
    ]


async def wait_for_checks(
    client: httpx.AsyncClient,
    repo: str,
    commit_sha: str,
    headers: dict,
    timeout_seconds: int = 300,
    poll_interval: int = 15,
) -> dict:
    """Wait for all check runs to complete and return a summary.

    Args:
        client: HTTP client.
        repo: Repository full name.
        commit_sha: Commit SHA to monitor.
        headers: API headers.
        timeout_seconds: Maximum wait time (default 5 minutes).
        poll_interval: Seconds between polls.

    Returns:
        Dict with "all_passed", "total", "passed", "failed", "details".
    """
    elapsed = 0

    while elapsed < timeout_seconds:
        check_runs = await get_check_runs(client, repo, commit_sha, headers)

        if not check_runs:
            # No checks configured — consider it passed
            logger.info("No check runs found for %s, assuming pass", commit_sha[:8])
            return {
                "all_passed": True,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "details": [],
            }

        all_completed = all(cr["status"] == "completed" for cr in check_runs)

        if all_completed:
            passed = [cr for cr in check_runs if cr["conclusion"] == "success"]
            failed = [cr for cr in check_runs if cr["conclusion"] != "success"]

            result = {
                "all_passed": len(failed) == 0,
                "total": len(check_runs),
                "passed": len(passed),
                "failed": len(failed),
                "details": check_runs,
            }

            if result["all_passed"]:
                logger.info(
                    "All %d checks passed for %s",
                    result["total"], commit_sha[:8],
                )
            else:
                failed_names = [cr["name"] for cr in failed]
                logger.warning(
                    "%d/%d checks failed for %s: %s",
                    len(failed), len(check_runs), commit_sha[:8],
                    ", ".join(failed_names),
                )

            return result

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    # Timeout
    logger.warning("Timed out waiting for checks on %s", commit_sha[:8])
    return {
        "all_passed": False,
        "total": len(check_runs),
        "passed": 0,
        "failed": 0,
        "timed_out": True,
        "details": check_runs,
    }


async def post_ci_status_comment(
    client: httpx.AsyncClient,
    repo: str,
    pr_number: int,
    ci_result: dict,
    headers: dict,
) -> None:
    """Post a comment on the PR with CI status results."""
    if ci_result.get("timed_out"):
        status_emoji = "⏰"
        status_text = "CI check timed out — please verify manually."
    elif ci_result["all_passed"]:
        status_emoji = "✅"
        status_text = f"All {ci_result['total']} CI checks passed!"
    else:
        status_emoji = "❌"
        status_text = f"{ci_result['failed']}/{ci_result['total']} checks failed."

    details_section = ""
    for cr in ci_result.get("details", []):
        icon = "✅" if cr.get("conclusion") == "success" else "❌"
        details_section += f"  - {icon} {cr['name']}\n"

    body = (
        f"## {status_emoji} Velie CI Status\n\n"
        f"{status_text}\n\n"
    )
    if details_section:
        body += f"### Check Details\n\n{details_section}"

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    resp = await client.post(url, headers=headers, json={"body": body})
    resp.raise_for_status()
    logger.info("Posted CI status comment on PR #%d", pr_number)
